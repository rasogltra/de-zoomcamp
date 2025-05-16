---
title: "Workflow Orchestration for Scalable Data Pipelines"
datePublished: Fri May 09 2025 17:52:37 GMT+0000 (Coordinated Universal Time)
cuid: cmah3gaod003708l421pqc90g
slug: learning-data-engineering-orchestration
tags: postgresql, orchestration, data-pipeline, cronjob, scheduling, kestra

---

This is my tech journal tracking a data engineering course with DataTalks.Club: [https://github.com/DataTalksClub/data-engineering-zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp).

In [Module 1](https://hashnode.com/edit/cma5uvq2u000208la0y8ybwok), we dockerized a Python script that downloads a parquet file and loads taxi data into a Postgres database. For this week, we’re covering workflow orchestration and Kestra.

## **Introduction to Orchestration and Kestra**

**WHY USE WORKFLOW ORCHESTRATION?**

Workflow orchestration helps different services and tools work together—no more manual steps or scattered scripts. Sure, you could automate the same tasks, but that usually just runs one thing at a time, which works great in unit testing or deployments. Orchestration goes a step further: it connects and automates many tasks to run as one smooth, end-to-end process.

**USE CASES**

* **DATA-DRIVEN ENVIRONMENTS:** Orchestrators are great for ETL tasks—they make it easy to pull data from different sources and load it into a data warehouse.
    
* ![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746135379412/0d806b50-ff87-4bf2-b22c-efbd5e3f0880.png align="left")
    
* **CI/CD PIPELINES**: You can build, test, and publish your code to different places all at the same time.
    
    ![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746135198176/afddcdac-88aa-40df-b405-13ca65b1bcd4.png align="center")
    

### **WHAT IS KESTRA?**

Kestra is a flexible, orchestration tool that helps you automate complex tasks across different services. You write the workflows in YAML, which makes them readable. It plays nicely with programming languages such as Python, SQL, and Bash, and comes with 600+ plugins so you can plug into tons of tools without much setup.

I followed the [Getting Started with Kestra](https://kestra.io/docs/tutorial?clid=eyJpIjoiWDgxRzZROHFua2JnUjFQQUJiczJoIiwiaCI6IiIsInAiOiIvZGUtem9vbWNhbXAvdHV0b3JpYWwiLCJ0IjoxNzQ2NDg2MDI3fQ.sED5CQvfdkfN3vGoBzxzjDulagi2ztOcYWhwmSoKaiY) step-by-step to build my first workflow. The video says it takes 5 minutes, but realistically it took me about an hour— understandably, since I’m a beginner to Kestra. 🙂

**INSTALL KESTRA AND DOCKER-COMPOSE**

```bash
# downloads the latest image 
docker run --pull=always --rm -it 
    -p 8080:8080 --user=root 
    -v /var/run/docker.sock:/var/run/docker.sock 
    -v /tmp:/tmp kestra/kestra:latest server local
```

The video downloads a docker-compose to start the Kestra server:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/kestra-io/kestra/develop/docker-compose.yml
```

I made a small change to the YAML file by modifying the volume mount. Instead of using the downloaded version’s path, I used a relative path: `./tmp` on the host side. This tells Docker to link the local `./tmp` folder (which is in the same directory as your `docker-compose.yml)` to the container’s `/tmp/kestra-wd` folder.

To avoid potential errors in Kestra—like the ones I ran into— make sure you do the following **before** running `docker-compose`:

* Create a directory named `tmp` in the same directory, if it doesn't exist, as your `docker-compose.yml`. If you decide to keep the downloaded version, then you’ll need to create the local folder: `/tmp/kestra-wd`.
    
* Give it permissions so Docker can read and write to it. I used `chmod 777 ./tmp`.
    

```yaml
volumes:
  postgres-data:
    driver: local
  kestra-data:
    driver: local

services:
  postgres:
    image: postgres
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: kestra
      POSTGRES_USER: kestra
      POSTGRES_PASSWORD: k3str4
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -d $${POSTGRES_DB} -U $${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 10

  kestra:
    image: kestra/kestra:latest
    pull_policy: always
    # Note that this setup with a root user is intended for development purpose.
    # Our base image runs without root, but the Docker Compose implementation needs root to access the Docker socket
    user: "root"
    command: server standalone
    volumes:
      - kestra-data:/app/storage
      - /var/run/docker.sock:/var/run/docker.sock
      - ./tmp:/tmp/kestra-wd # mount relative path './tmp' from host 
                                # to container 'tmp/kestra-wd'
    environment:
      KESTRA_CONFIGURATION: |
        datasources:
          postgres:
            url: jdbc:postgresql://postgres:5432/kestra
            driverClassName: org.postgresql.Driver
            username: kestra
            password: k3str4
        kestra:
          server:
            basicAuth:
              enabled: false
              username: "admin@localhost.dev" # it must be a valid email address
              password: kestra
          repository:
            type: postgres
          storage:
            type: local
            local:
              basePath: "/app/storage"
          queue:
            type: postgres
          tasks:
            tmpDir:
              path: /tmp/kestra-wd/tmp
          url: http://localhost:8080/
    ports:
      - "8081:8080"
    depends_on:
      postgres:
        condition: service_started
```

We then started the Kestra service using `docker compose up -d` and then launched the UI, in my case `http://localhost:8081`.

**KESTRA PROPERTIES FILE**

In Kestra, `Flows` are declared using a `YAML` file. Each flow contains an `id`, `namespace` and `tasks`.

In our example, we created a simple flow that runs a Python script, stores the result into a variable called `gh_stars`, and then uses that variable in the `python_output` task. The flow runs inside a docker container, which helps keep all dependencies isolated and consistent.

It took me several tries to get the script running without errors. One important tip: make sure to use the pipe symbol (`|`) before writing a multi-line script. This tells Kestra that the content is a block of multi-line text.

```yaml
id: gazelle_128930 # id: workflow name
namespace: company.team # area where workflow is stored

tasks: # set of instructions to be executed
  - id: python_script
    type: io.kestra.plugin.scripts.python.Script
    beforeCommands:
      - pip install requests kestra
    script: |
      import requests
      from kestra import Kestra

      r = requests.get('https://api.github.com/repos/kestra-io/kestra')
      gh_stars = r.json()['stargazers_count']

      Kestra.outputs({'gh_stars':gh_stars})
  - id: python_output
    type: io.kestra.plugin.core.log.Log
    message: "Number of stars: {{outputs.python_script.vars.gh_stars}}"
```

## **BUILD DATA PIPELINE WITH KESTRA**

The first step we took was to extract data from the CSV files. I created a `docker compose` file to launch Kestra, followed by in a separate directory, I ran `docker compose` configuration to start the Postgres service. While it's possible to combine both services into a singular docker compose setup as a workaround, I kept them separate to align with the structure presented in the [tutorial video](https://www.youtube.com/watch?v=OkfLX28Ecjg).

**EXTRACTING DATA WITH POSTGRES\_TAXI.YAML**

To extract the CSV data, we created a `postgres_taxi.yaml` flow and a `Dockerfile` that together handle both downloading the dataset from GitHub via an `HTTP request` and loading it into our database. The flow uses several `inputs`—such as `dataset type, year, and month`—so we can control what data gets loaded without hardcoding values throughout the workflow. Based on these `inputs`, we define variables that are reused across the flow for things like filenames and table names (more on that below). We also added a `set_label` task to make it easier to track what was executed in the logs.

```yaml
id: postgres_taxi
namespace: company.team

inputs:
  - id: taxi
    type: SELECT
    displayName: Select taxi type
    values: [yellow, green]
    defaults: yellow

  - id: year
    type: SELECT
    displayName: Select year
    values: ["2019", "2020"]
    defaults: "2019"

  - id: month
    type: SELECT
    displayName: Select month
    values: ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    defaults: "01"

variables:
    file: "{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv"
    staging_table: "public.{{inputs.taxi}}_tripdata_staging"
    table: "public.{{inputs.taxi}}_tripdata"
    data: "{{outputs.extract.outputFiles[inputs.taxi ~ '_tripdata_' ~ inputs.year ~ '-' ~ inputs.month ~ '.csv']}}"

tasks:
  - id: set_label
    type: io.kestra.plugin.core.execution.Labels
    labels:
      file: "{{render(vars.file)}}"
      taxi: "{{inputs.taxi}}"

  - id: extract
    type: io.kestra.plugin.scripts.shell.Commands
    outputFiles:
      - "*.csv"
    taskRunner:
      type: io.kestra.plugin.core.runner.Process
    commands:
      - wget -qO- https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{{inputs.taxi}}/{{render(vars.file)}}.gz | gunzip > {{render(vars.file)}}
```

```dockerfile
volumes:
  postgres-data:
    driver: local
  kestra-data:
    driver: local

services:
  postgres:
    image: postgres
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: kestra
      POSTGRES_USER: kestra
      POSTGRES_PASSWORD: k3str4
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -d $${POSTGRES_DB} -U $${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 10

  kestra:
    image: kestra/kestra:v0.20.7
    pull_policy: always
    user: "root"
    command: server standalone
    volumes:
      - kestra-data:/app/storage
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp:/tmp/kestra-wd
    environment:
      KESTRA_CONFIGURATION: |
        datasources:
          postgres:
            url: jdbc:postgresql://postgres:5432/kestra
            driverClassName: org.postgresql.Driver
            username: kestra
            password: k3str4
        kestra:
          server:
            basicAuth:
              enabled: false
              username: "admin@admin.com" # it must be a valid email address
              password: kestra
          repository:
            type: postgres
          storage:
            type: local
            local:
              basePath: "/app/storage"
          queue:
            type: postgres
          tasks:
            tmpDir:
              path: /tmp/kestra-wd/tmp
          url: http://localhost:8080/
    ports:
      - "8081:8080"
    depends_on:
      postgres:
        condition: service_started
```

Following the approach demonstrated in the tutorial video, I started with a small, manageable dataset— I selected 'green' taxi type from January 2019—to make sure everything was working correctly before scaling up. You should be prompted before execution, like so:

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746804587981/8bd2b0f2-4376-4217-ac32-5a10b55367f6.png align="center")

Check out futher breakdown in the [video](https://www.youtube.com/watch?v=OkfLX28Ecjg) below for a step-by-step explanation.

**CONTINUE BUILDING** `postgres_taxi.yaml`

Once the data is extracted, the next step is to expand our Kestra flow. We add a series of SQL queries to create database tables for both yellow and green taxi data, set up staging tables, copy the data into staging, add a `unique_id` and `filename` data column, and finally merge the data into `green_tripdata` or `yellow_tripdata` tables. I also added a `debug_inputs` task to help log and trace input value errors while testing the flow.

```yaml
 - id: if_yellow_taxi
    type: io.kestra.plugin.core.flow.If
    condition: "{{inputs.taxi == 'yellow'}}"
    then:
      - id: debug_inputs
        type: io.kestra.plugin.core.debug.Return
        format: |
          Taxi: "{{ inputs.taxi }}"
          File: "{{ render(vars.file) }}"

      - id: yellow_create_table
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
          CREATE TABLE IF NOT EXISTS {{render(vars.table)}} (
              unique_row_id          text,
              filename               text,
              VendorID               text,
              tpep_pickup_datetime   timestamp,
              tpep_dropoff_datetime  timestamp,
              passenger_count        integer,
              trip_distance          double precision,
              RatecodeID             text,
              store_and_fwd_flag     text,
              PULocationID           text,
              DOLocationID           text,
              payment_type           integer,
              fare_amount            double precision,
              extra                  double precision,
              mta_tax                double precision,
              tip_amount             double precision,
              tolls_amount           double precision,
              improvement_surcharge  double precision,
              total_amount           double precision,
              congestion_surcharge   double precision
          );

      - id: yellow_create_staging_table
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
            CREATE TABLE IF NOT EXISTS {{render(vars.staging_table)}} (
                unique_row_id          text,
                filename               text,
                VendorID               text,
                tpep_pickup_datetime   timestamp,
                tpep_dropoff_datetime  timestamp,
                passenger_count        integer,
                trip_distance          double precision,
                RatecodeID             text,
                store_and_fwd_flag     text,
                PULocationID           text,
                DOLocationID           text,
                payment_type           integer,
                fare_amount            double precision,
                extra                  double precision,
                mta_tax                double precision,
                tip_amount             double precision,
                tolls_amount           double precision,
                improvement_surcharge  double precision,
                total_amount           double precision,
                congestion_surcharge   double precision
            );

      - id: yellow_truncate_staging_table
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
          TRUNCATE TABLE {{render(vars.staging_table)}};
      
      - id: yellow_copy_in_to_staging_table
        type: io.kestra.plugin.jdbc.postgresql.CopyIn
        format: CSV
        from: "{{render(vars.data)}}"
        table: "{{render(vars.staging_table)}}"
        header: true
        columns: [VendorID,tpep_pickup_datetime,tpep_dropoff_datetime,passenger_count,trip_distance,RatecodeID,store_and_fwd_flag,PULocationID,DOLocationID,payment_type,fare_amount,extra,mta_tax,tip_amount,tolls_amount,improvement_surcharge,total_amount,congestion_surcharge]

      - id: yellow_add_unique_id_and_filename
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
          UPDATE {{render(vars.staging_table)}}
          SET 
            unique_row_id = md5(
              COALESCE(CAST(VendorID AS text), '') ||
              COALESCE(CAST(tpep_pickup_datetime AS text), '') || 
              COALESCE(CAST(tpep_dropoff_datetime AS text), '') || 
              COALESCE(PULocationID, '') || 
              COALESCE(DOLocationID, '') || 
              COALESCE(CAST(fare_amount AS text), '') || 
              COALESCE(CAST(trip_distance AS text), '')      
            ),
            filename = '{{render(vars.file)}}';

      - id: yellow_merge_data
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
          MERGE INTO {{render(vars.table)}} AS T
          USING {{render(vars.staging_table)}} AS S
          ON T.unique_row_id = S.unique_row_id
          WHEN NOT MATCHED THEN
            INSERT (
              unique_row_id, filename, VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
              passenger_count, trip_distance, RatecodeID, store_and_fwd_flag, PULocationID,
              DOLocationID, payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount,
              improvement_surcharge, total_amount, congestion_surcharge
            )
            VALUES (
              S.unique_row_id, S.filename, S.VendorID, S.tpep_pickup_datetime, S.tpep_dropoff_datetime,
              S.passenger_count, S.trip_distance, S.RatecodeID, S.store_and_fwd_flag, S.PULocationID,
              S.DOLocationID, S.payment_type, S.fare_amount, S.extra, S.mta_tax, S.tip_amount, S.tolls_amount,
              S.improvement_surcharge, S.total_amount, S.congestion_surcharge
            );

  - id: if_green_taxi
    type: io.kestra.plugin.core.flow.If
    condition: "{{inputs.taxi == 'green'}}"
    then:
      - id: green_create_table
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
          CREATE TABLE IF NOT EXISTS {{render(vars.table)}} (
              unique_row_id          text,
              filename               text,
              VendorID               text,
              lpep_pickup_datetime   timestamp,
              lpep_dropoff_datetime  timestamp,
              passenger_count        integer,
              trip_distance          double precision,
              RatecodeID             text,
              store_and_fwd_flag      text,
              PULocationID           text,
              DOLocationID           text,
              payment_type           integer,
              fare_amount            double precision,
              extra                  double precision,
              mta_tax                double precision,
              tip_amount             double precision,
              tolls_amount           double precision,
              ehail_fee              double precision,
              improvement_surcharge  double precision,
              total_amount           double precision,
              trip_type              integer,
              congestion_surcharge   double precision
          );

      - id: green_create_staging_table
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
              CREATE TABLE IF NOT EXISTS {{render(vars.staging_table)}} (
                  unique_row_id          text,
                  filename               text,
                  VendorID               text,
                  lpep_pickup_datetime   timestamp,
                  lpep_dropoff_datetime  timestamp,
                  store_and_fwd_flag     text,
                  RatecodeID             text,
                  PULocationID           text,
                  DOLocationID           text,
                  passenger_count        integer,
                  trip_distance          double precision,
                  fare_amount            double precision,
                  extra                  double precision,
                  mta_tax                double precision,
                  tip_amount             double precision,
                  tolls_amount           double precision,
                  ehail_fee              double precision,
                  improvement_surcharge  double precision,
                  total_amount           double precision,
                  payment_type           integer,
                  trip_type              integer,
                  congestion_surcharge   double precision
              );

      - id: green_truncate_staging_table
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
              TRUNCATE TABLE {{render(vars.staging_table)}};

      - id: green_copy_in_to_staging_table
        type: io.kestra.plugin.jdbc.postgresql.CopyIn
        format: CSV
        from: "{{render(vars.data)}}"
        table: "{{render(vars.staging_table)}}"
        header: true
        columns: [VendorID,lpep_pickup_datetime,lpep_dropoff_datetime,store_and_fwd_flag,RatecodeID,PULocationID,DOLocationID,passenger_count,trip_distance,fare_amount,extra,mta_tax,tip_amount,tolls_amount,ehail_fee,improvement_surcharge,total_amount,payment_type,trip_type,congestion_surcharge]

      - id: green_add_unique_id_and_filename
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
              UPDATE {{render(vars.staging_table)}}
              SET 
                unique_row_id = md5(
                  COALESCE(CAST(VendorID AS text), '') ||
                  COALESCE(CAST(lpep_pickup_datetime AS text), '') || 
                  COALESCE(CAST(lpep_dropoff_datetime AS text), '') || 
                  COALESCE(PULocationID, '') || 
                  COALESCE(DOLocationID, '') || 
                  COALESCE(CAST(fare_amount AS text), '') || 
                  COALESCE(CAST(trip_distance AS text), '')      
                ),
                filename = '{{render(vars.file)}}';

      - id: green_merge_data
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
              MERGE INTO {{render(vars.table)}} AS T
              USING {{render(vars.staging_table)}} AS S
              ON T.unique_row_id = S.unique_row_id
              WHEN NOT MATCHED THEN
                INSERT (
                  unique_row_id, filename, VendorID, lpep_pickup_datetime, lpep_dropoff_datetime,
                  store_and_fwd_flag, RatecodeID, PULocationID, DOLocationID, passenger_count,
                  trip_distance, fare_amount, extra, mta_tax, tip_amount, tolls_amount, ehail_fee,
                  improvement_surcharge, total_amount, payment_type, trip_type, congestion_surcharge
                )
                VALUES (
                  S.unique_row_id, S.filename, S.VendorID, S.lpep_pickup_datetime, S.lpep_dropoff_datetime,
                  S.store_and_fwd_flag, S.RatecodeID, S.PULocationID, S.DOLocationID, S.passenger_count,
                  S.trip_distance, S.fare_amount, S.extra, S.mta_tax, S.tip_amount, S.tolls_amount, S.ehail_fee,
                  S.improvement_surcharge, S.total_amount, S.payment_type, S.trip_type, S.congestion_surcharge
                );

  - id: purge_files
    type: io.kestra.plugin.core.storage.PurgeCurrentExecutionFiles
    description: This will remove output files. If you'd like to explore Kestra outputs, disable it.

pluginDefaults:
  - type: io.kestra.plugin.jdbc.postgresql
    values:
      url: jdbc:postgresql://host.docker.internal:5432/postgres-zoomcamp
      username: kestra
      password: k3str4
```

The key to getting our data into the database was adding the `pluginDefaults` block. Without this, Kestra throws errors during query execution. This section sets default connection details for Postgres, so we don’t need to repeat the same `url`, `username`, and `password` in every task. It applies automatically to all Postgres-related plugins in the flow, keeping things clean.

```yaml
pluginDefaults:
  - type: io.kestra.plugin.jdbc.postgresql
    values:
      url: jdbc:postgresql://host.docker.internal:5432/postgres-zoomcamp
      username: kestra
      password: k3str4
```

**VARS VS RENDER (VARS)**

When to use *vars* versus *rendering a vars* was a confusing concept to me in learning Kestra. I think it’s helpful to have a clear understanding, while debugging errors.

In the `postgres_taxi.yaml` flow, there's a `variables:` section where we dynamically define `file`, `staging_table`, `table`, and `data`. For example, the `file` variable stores a templated string representing the dataset filename: `{{`[`inputs.taxi`](http://inputs.taxi)`}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv`.

```yaml
variables:
    file: "{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv"
    staging_table: "public.{{inputs.taxi}}_tripdata_staging"
    table: "public.{{inputs.taxi}}_tripdata"
    data: "{{outputs.extract.outputFiles[inputs.taxi ~ '_tripdata_' ~ inputs.year ~ '-' ~ inputs.month ~ '.csv']}}"
```

Throughout `postgres_taxi.yaml`, we *render* variables—such as when we add the `filename` column, like so `filename = '{{render(vars.file)}}';` to a data table. In these cases, we're telling Kestra to evaluate the `file` variable by replacing the template string with actual input values.

For example, if the inputs are `yellow`, `2019`, and `01`, it becomes `yellow_tripdata_2019-01.csv`. Without rendering variables, Kestra outputs the raw string `"{{`[`inputs.taxi`](http://inputs.taxi)`}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv"`.

```yaml
- id: green_add_unique_id_and_filename
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
              UPDATE {{render(vars.staging_table)}}
              SET 
                unique_row_id = md5(
                  COALESCE(CAST(VendorID AS text), '') ||
                  COALESCE(CAST(lpep_pickup_datetime AS text), '') || 
                  COALESCE(CAST(lpep_dropoff_datetime AS text), '') || 
                  COALESCE(PULocationID, '') || 
                  COALESCE(DOLocationID, '') || 
                  COALESCE(CAST(fare_amount AS text), '') || 
                  COALESCE(CAST(trip_distance AS text), '')      
                ),
                filename = '{{render(vars.file)}}';
```

**LOAD TAXI DATA TO POSTGRES**

I found the **"Source and Topology"** tabs in Kestra helpful for visualizing the entire flow. In my screenshot, I’m highlighting the steps Kestra takes to extract the data, create our Postgres table for yellow taxi datasets (part of green taxi got cut off), and then copy the data into our database.

Notice that we added `if-statements` to process either the yellow or green datasets, meaning both cannot be processed simultaneously. Also, not shown here, but implemented in `postgres_taxi.yaml`, we purge/remove *all* output files.

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746808823854/71b0e7e2-ec1a-467f-9990-415db1053bac.png align="center")

Next, we’ll set up a Postgres database using Docker. We’ll use a `docker-compose.yml` file to easily run both Postgres and PgAdmin in connected containers. This approach was covered in depth back in [Module 1](https://hashnode.com/edit/cma5uvq2u000208la0y8ybwok), so revisit that if in need of a refresher.

I’m running PgAdmin inside Docker, so I connect to Postgres from my PgAdmin container — *not* from `localhost`. This is because containers talk to each other over a shared Docker network, and `localhost` would point to the PgAdmin container itself, not Postgres.

Here’s what helped:

* Use the **Postgres container’s name** (like `postgres-db`) as the host when connecting from PgAdmin.
    
* Make sure both containers are on the **same docker network** (docker compose handles this automatically if they’re in the same `docker-compose.yaml` file).
    
* I used the same PgAdmin login credentials that were used in [Module 1](https://hashnode.com/edit/cma5uvq2u000208la0y8ybwok).
    

```dockerfile
services:
  postgres:
    image: postgres
    container_name: postgres-db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: postgres-zoomcamp
      POSTGRES_USER: kestra
      POSTGRES_PASSWORD: k3str4
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -d $${POSTGRES_DB} -U $${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 10
  pgadmin:
    image: dpage/pgadmin4
    container_name: pgadmin-1
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "8080:80"
    depends_on:
      - postgres
volumes:
  postgres-data:
```

After starting Postgres with the command `docker-compose up -d`, navigate to your browser and enter your pgadmin credentials. A successful execution in Kestra should complete all flow tasks and migrate the data to our database and in PgAdmin, you should see both the green and yellow taxi data in your database.

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746814173905/4db5d6e0-02be-44f2-b38b-b3dd88344d88.png align="center")

**SCHEDULING AND BACKFILLS WITH POSTGRES**

We’re automating our pipeline using a cron scheduler to run backfills on historical data. To do this, we made a few updates to `postgres_taxi.yaml`, specifically modifying the inputs and variables, and adding triggers.

In Kestra, I created a new flow called `postgres_taxi_scheduled`, which accepts `taxi_type` as input and uses a trigger to dynamically provide the year and month.

The core tasks in the flow remain unchanged. This is reflected in the Topology view, where the structure and logic of the flow are largely the same, with the main difference being the addition of the trigger.

```yaml
id: postgres_taxi_scheduled
namespace: zoomcamp

concurrency:
  limit: 1

inputs:
  - id: taxi
    type: SELECT
    displayName: Select taxi type
    values: [yellow, green]
    defaults: yellow

variables:
  file: "{{inputs.taxi}}_tripdata_{{trigger.date | date ('yyyy-MM')}}.csv"
  staging_table: "public.{{inputs.taxi}}_tripdata_staging"
  table: "public.{{inputs.taxi}}_tripdata"
  data: "{{outputs.extract.outputFiles[inputs.taxi ~ '_tripdata_' ~ (trigger.date | date('yyyy-MM')) ~ '.csv']}}"
```

At the bottom of the YAML file, just after `pluginDefaults`, we define the triggers for both green and yellow taxis. These are scheduled to run automatically on the first day of each month—green taxi data at 9:00 AM and yellow taxi data at 10:00 AM.

```yaml
triggers:
  - id: green_schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 9 1 * *"
    inputs:
      taxi: green

  - id: yellow_schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 10 1 * *"
    inputs:
      taxi: yellow
```

To fill in any missing data from 2019, we'll use Kestra's `backfill execution` feature. We've configured execution labels to indicate whether a run is a backfill, making it easy to track. After triggering the backfill, the Postgres tables should be populated for all twelve months, from `January 1st` to `December 31st, 2019`.

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746823221096/de303e86-4aec-4e4c-9620-9fbb03389359.png align="center")

I followed the [tutorial video](https://www.youtube.com/watch?v=_-li_z97zog), which provides a deeper look into how these functions work in Kestra.

**ETL PIPELINE IN KESTRA USING GOGLE CLOUD STORAGE**

Another option is to upload the same data to a data lake like Google Cloud Storage (GCS), then use BigQuery to create tables from the taxi `.csv` files. That way, I can run queries just like I would in Postgres.

1. We set up our Google Cloud credentials using the `KV Store` in Kestra and created a service account—pretty similar to how it's done for Terraform. In the GCP console, I created a service account called `data-lake-big-query` and gave it the BigQuery Admin and Storage Admin roles. I ran into permission issues at this step, so make sure your roles are assigned at the **project level** to avoid access problems.
    
2. I created a new key in GCP and copied the entire JSON content into a new key-value entry in the `KV Store`.
    
3. In `gcp_kv`, we use the variables where you'll need to provide your `project ID` and set a globally unique `bucket name`. This flow then saves those variables to the `KV Store`, which I confirmed.
    
    ```yaml
    id: gcp_kv
    namespace: zoomcamp
    
    tasks:
      - id: gcp_project_id
        type: io.kestra.plugin.core.kv.Set
        key: GCP_PROJECT_ID
        kvType: STRING
        value: # TODO replace with your project id
    
      - id: gcp_location
        type: io.kestra.plugin.core.kv.Set
        key: GCP_LOCATION
        kvType: STRING
        value: europe-west2
    
      - id: gcp_bucket_name
        type: io.kestra.plugin.core.kv.Set
        key: GCP_BUCKET_NAME
        kvType: STRING
        value: # TODO make sure it's globally unique!
    
      - id: gcp_dataset
        type: io.kestra.plugin.core.kv.Set
        key: GCP_DATASET
        kvType: STRING
        value: zoomcamp
    ```
    
4. The `gcp_setup` flow creates our Google Cloud Storage bucket and sets up the cloud environment using the variables from `gcp_kv`.
    
    ```yaml
    id: gcp_setup
    namespace: zoomcamp
    
    tasks:
      - id: create_gcs_bucket
        type: io.kestra.plugin.gcp.gcs.CreateBucket
        ifExists: SKIP
        storageClass: REGIONAL
        name: "{{kv('GCP_BUCKET_NAME')}}" # make sure it's globally unique!
    
      - id: create_bq_dataset
        type: io.kestra.plugin.gcp.bigquery.CreateDataset
        name: "{{kv('GCP_DATASET')}}"
        ifExists: SKIP
    
    pluginDefaults:
      - type: io.kestra.plugin.gcp
        values:
          serviceAccount: "{{kv('GCP_CREDS')}}"
          projectId: "{{kv('GCP_PROJECT_ID')}}"
          location: "{{kv('GCP_LOCATION')}}"
          bucket: "{{kv('GCP_BUCKET_NAME')}}"
    ```
    
    5. The `gcp_taxi` flow uploads our data to the Google Cloud Storage data lake, where we repeat similar steps—like creating tables and purging files—as we did when importing into Postgres. The key difference is that this time, the data ends up in our cloud-based warehouse, BigQuery. In this example, I ran `gcp_taxi` on the green taxi data for January and February 2019, and did the same for yellow taxi. As a result, you should see four `.csv` files in your Kestra bucket and multiple tables or files in BigQuery.
        
        ```yaml
        id: gcp_taxi
        namespace: zoomcamp
        description: |
          The CSV Data used in the course: https://github.com/DataTalksClub/nyc-tlc-data/releases
        
        inputs:
          - id: taxi
            type: SELECT
            displayName: Select taxi type
            values: [yellow, green]
            defaults: green
        
          - id: year
            type: SELECT
            displayName: Select year
            values: ["2019", "2020"]
            defaults: "2019"
            allowCustomValue: true # allows you to type 2021 from the UI for the homework 🤗
        
          - id: month
            type: SELECT
            displayName: Select month
            values: ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
            defaults: "01"
        
        variables:
          file: "{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv"
          gcs_file: "gs://{{kv('GCP_BUCKET_NAME')}}/{{vars.file}}"
          table: "{{kv('GCP_DATASET')}}.{{inputs.taxi}}_tripdata_{{inputs.year}}_{{inputs.month}}"
          data: "{{outputs.extract.outputFiles[inputs.taxi ~ '_tripdata_' ~ inputs.year ~ '-' ~ inputs.month ~ '.csv']}}"
        
        tasks:
          - id: set_label
            type: io.kestra.plugin.core.execution.Labels
            labels:
              file: "{{render(vars.file)}}"
              taxi: "{{inputs.taxi}}"
              
          - id: extract
            type: io.kestra.plugin.scripts.shell.Commands
            outputFiles:
              - "*.csv"
            taskRunner:
              type: io.kestra.plugin.core.runner.Process
            commands:
              - wget -qO- https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{{inputs.taxi}}/{{render(vars.file)}}.gz | gunzip > {{render(vars.file)}}
          
          - id: upload_to_gcs
            type: io.kestra.plugin.gcp.gcs.Upload
            from: "{{render(vars.data)}}"
            to: "{{render(vars.gcs_file)}}"
        
          - id: if_yellow_taxi
            type: io.kestra.plugin.core.flow.If
            condition: "{{inputs.taxi == 'yellow'}}"
            then:
              - id: bq_yellow_tripdata
                type: io.kestra.plugin.gcp.bigquery.Query
                sql: |
                  CREATE TABLE IF NOT EXISTS `{{kv('GCP_PROJECT_ID')}}.{{kv('GCP_DATASET')}}.yellow_tripdata`
                  (
                      unique_row_id BYTES OPTIONS (description = 'A unique identifier for the trip, generated by hashing key trip attributes.'),
                      filename STRING OPTIONS (description = 'The source filename from which the trip data was loaded.'),      
                      VendorID STRING OPTIONS (description = 'A code indicating the LPEP provider that provided the record. 1= Creative Mobile Technologies, LLC; 2= VeriFone Inc.'),
                      tpep_pickup_datetime TIMESTAMP OPTIONS (description = 'The date and time when the meter was engaged'),
                      tpep_dropoff_datetime TIMESTAMP OPTIONS (description = 'The date and time when the meter was disengaged'),
                      passenger_count INTEGER OPTIONS (description = 'The number of passengers in the vehicle. This is a driver-entered value.'),
                      trip_distance NUMERIC OPTIONS (description = 'The elapsed trip distance in miles reported by the taximeter.'),
                      RatecodeID STRING OPTIONS (description = 'The final rate code in effect at the end of the trip. 1= Standard rate 2=JFK 3=Newark 4=Nassau or Westchester 5=Negotiated fare 6=Group ride'),
                      store_and_fwd_flag STRING OPTIONS (description = 'This flag indicates whether the trip record was held in vehicle memory before sending to the vendor, aka "store and forward," because the vehicle did not have a connection to the server. TRUE = store and forward trip, FALSE = not a store and forward trip'),
                      PULocationID STRING OPTIONS (description = 'TLC Taxi Zone in which the taximeter was engaged'),
                      DOLocationID STRING OPTIONS (description = 'TLC Taxi Zone in which the taximeter was disengaged'),
                      payment_type INTEGER OPTIONS (description = 'A numeric code signifying how the passenger paid for the trip. 1= Credit card 2= Cash 3= No charge 4= Dispute 5= Unknown 6= Voided trip'),
                      fare_amount NUMERIC OPTIONS (description = 'The time-and-distance fare calculated by the meter'),
                      extra NUMERIC OPTIONS (description = 'Miscellaneous extras and surcharges. Currently, this only includes the $0.50 and $1 rush hour and overnight charges'),
                      mta_tax NUMERIC OPTIONS (description = '$0.50 MTA tax that is automatically triggered based on the metered rate in use'),
                      tip_amount NUMERIC OPTIONS (description = 'Tip amount. This field is automatically populated for credit card tips. Cash tips are not included.'),
                      tolls_amount NUMERIC OPTIONS (description = 'Total amount of all tolls paid in trip.'),
                      improvement_surcharge NUMERIC OPTIONS (description = '$0.30 improvement surcharge assessed on hailed trips at the flag drop. The improvement surcharge began being levied in 2015.'),
                      total_amount NUMERIC OPTIONS (description = 'The total amount charged to passengers. Does not include cash tips.'),
                      congestion_surcharge NUMERIC OPTIONS (description = 'Congestion surcharge applied to trips in congested zones')
                  )
                  PARTITION BY DATE(tpep_pickup_datetime);
        
              - id: bq_yellow_table_ext
                type: io.kestra.plugin.gcp.bigquery.Query
                sql: |
                  CREATE OR REPLACE EXTERNAL TABLE `{{kv('GCP_PROJECT_ID')}}.{{render(vars.table)}}_ext`
                  (
                      VendorID STRING OPTIONS (description = 'A code indicating the LPEP provider that provided the record. 1= Creative Mobile Technologies, LLC; 2= VeriFone Inc.'),
                      tpep_pickup_datetime TIMESTAMP OPTIONS (description = 'The date and time when the meter was engaged'),
                      tpep_dropoff_datetime TIMESTAMP OPTIONS (description = 'The date and time when the meter was disengaged'),
                      passenger_count INTEGER OPTIONS (description = 'The number of passengers in the vehicle. This is a driver-entered value.'),
                      trip_distance NUMERIC OPTIONS (description = 'The elapsed trip distance in miles reported by the taximeter.'),
                      RatecodeID STRING OPTIONS (description = 'The final rate code in effect at the end of the trip. 1= Standard rate 2=JFK 3=Newark 4=Nassau or Westchester 5=Negotiated fare 6=Group ride'),
                      store_and_fwd_flag STRING OPTIONS (description = 'This flag indicates whether the trip record was held in vehicle memory before sending to the vendor, aka "store and forward," because the vehicle did not have a connection to the server. TRUE = store and forward trip, FALSE = not a store and forward trip'),
                      PULocationID STRING OPTIONS (description = 'TLC Taxi Zone in which the taximeter was engaged'),
                      DOLocationID STRING OPTIONS (description = 'TLC Taxi Zone in which the taximeter was disengaged'),
                      payment_type INTEGER OPTIONS (description = 'A numeric code signifying how the passenger paid for the trip. 1= Credit card 2= Cash 3= No charge 4= Dispute 5= Unknown 6= Voided trip'),
                      fare_amount NUMERIC OPTIONS (description = 'The time-and-distance fare calculated by the meter'),
                      extra NUMERIC OPTIONS (description = 'Miscellaneous extras and surcharges. Currently, this only includes the $0.50 and $1 rush hour and overnight charges'),
                      mta_tax NUMERIC OPTIONS (description = '$0.50 MTA tax that is automatically triggered based on the metered rate in use'),
                      tip_amount NUMERIC OPTIONS (description = 'Tip amount. This field is automatically populated for credit card tips. Cash tips are not included.'),
                      tolls_amount NUMERIC OPTIONS (description = 'Total amount of all tolls paid in trip.'),
                      improvement_surcharge NUMERIC OPTIONS (description = '$0.30 improvement surcharge assessed on hailed trips at the flag drop. The improvement surcharge began being levied in 2015.'),
                      total_amount NUMERIC OPTIONS (description = 'The total amount charged to passengers. Does not include cash tips.'),
                      congestion_surcharge NUMERIC OPTIONS (description = 'Congestion surcharge applied to trips in congested zones')
                  )
                  OPTIONS (
                      format = 'CSV',
                      uris = ['{{render(vars.gcs_file)}}'],
                      skip_leading_rows = 1,
                      ignore_unknown_values = TRUE
                  );
        
              - id: bq_yellow_table_tmp
                type: io.kestra.plugin.gcp.bigquery.Query
                sql: |
                  CREATE OR REPLACE TABLE `{{kv('GCP_PROJECT_ID')}}.{{render(vars.table)}}`
                  AS
                  SELECT
                    MD5(CONCAT(
                      COALESCE(CAST(VendorID AS STRING), ""),
                      COALESCE(CAST(tpep_pickup_datetime AS STRING), ""),
                      COALESCE(CAST(tpep_dropoff_datetime AS STRING), ""),
                      COALESCE(CAST(PULocationID AS STRING), ""),
                      COALESCE(CAST(DOLocationID AS STRING), "")
                    )) AS unique_row_id,
                    "{{render(vars.file)}}" AS filename,
                    *
                  FROM `{{kv('GCP_PROJECT_ID')}}.{{render(vars.table)}}_ext`;
        
              - id: bq_yellow_merge
                type: io.kestra.plugin.gcp.bigquery.Query
                sql: |
                  MERGE INTO `{{kv('GCP_PROJECT_ID')}}.{{kv('GCP_DATASET')}}.yellow_tripdata` T
                  USING `{{kv('GCP_PROJECT_ID')}}.{{render(vars.table)}}` S
                  ON T.unique_row_id = S.unique_row_id
                  WHEN NOT MATCHED THEN
                    INSERT (unique_row_id, filename, VendorID, tpep_pickup_datetime, tpep_dropoff_datetime, passenger_count, trip_distance, RatecodeID, store_and_fwd_flag, PULocationID, DOLocationID, payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount, improvement_surcharge, total_amount, congestion_surcharge)
                    VALUES (S.unique_row_id, S.filename, S.VendorID, S.tpep_pickup_datetime, S.tpep_dropoff_datetime, S.passenger_count, S.trip_distance, S.RatecodeID, S.store_and_fwd_flag, S.PULocationID, S.DOLocationID, S.payment_type, S.fare_amount, S.extra, S.mta_tax, S.tip_amount, S.tolls_amount, S.improvement_surcharge, S.total_amount, S.congestion_surcharge);
              
          - id: if_green_taxi
            type: io.kestra.plugin.core.flow.If
            condition: "{{inputs.taxi == 'green'}}"
            then:
              - id: bq_green_tripdata
                type: io.kestra.plugin.gcp.bigquery.Query
                sql: |
                  CREATE TABLE IF NOT EXISTS `{{kv('GCP_PROJECT_ID')}}.{{kv('GCP_DATASET')}}.green_tripdata`
                  (
                      unique_row_id BYTES OPTIONS (description = 'A unique identifier for the trip, generated by hashing key trip attributes.'),
                      filename STRING OPTIONS (description = 'The source filename from which the trip data was loaded.'),      
                      VendorID STRING OPTIONS (description = 'A code indicating the LPEP provider that provided the record. 1= Creative Mobile Technologies, LLC; 2= VeriFone Inc.'),
                      lpep_pickup_datetime TIMESTAMP OPTIONS (description = 'The date and time when the meter was engaged'),
                      lpep_dropoff_datetime TIMESTAMP OPTIONS (description = 'The date and time when the meter was disengaged'),
                      store_and_fwd_flag STRING OPTIONS (description = 'This flag indicates whether the trip record was held in vehicle memory before sending to the vendor, aka "store and forward," because the vehicle did not have a connection to the server. Y= store and forward trip N= not a store and forward trip'),
                      RatecodeID STRING OPTIONS (description = 'The final rate code in effect at the end of the trip. 1= Standard rate 2=JFK 3=Newark 4=Nassau or Westchester 5=Negotiated fare 6=Group ride'),
                      PULocationID STRING OPTIONS (description = 'TLC Taxi Zone in which the taximeter was engaged'),
                      DOLocationID STRING OPTIONS (description = 'TLC Taxi Zone in which the taximeter was disengaged'),
                      passenger_count INT64 OPTIONS (description = 'The number of passengers in the vehicle. This is a driver-entered value.'),
                      trip_distance NUMERIC OPTIONS (description = 'The elapsed trip distance in miles reported by the taximeter.'),
                      fare_amount NUMERIC OPTIONS (description = 'The time-and-distance fare calculated by the meter'),
                      extra NUMERIC OPTIONS (description = 'Miscellaneous extras and surcharges. Currently, this only includes the $0.50 and $1 rush hour and overnight charges'),
                      mta_tax NUMERIC OPTIONS (description = '$0.50 MTA tax that is automatically triggered based on the metered rate in use'),
                      tip_amount NUMERIC OPTIONS (description = 'Tip amount. This field is automatically populated for credit card tips. Cash tips are not included.'),
                      tolls_amount NUMERIC OPTIONS (description = 'Total amount of all tolls paid in trip.'),
                      ehail_fee NUMERIC,
                      improvement_surcharge NUMERIC OPTIONS (description = '$0.30 improvement surcharge assessed on hailed trips at the flag drop. The improvement surcharge began being levied in 2015.'),
                      total_amount NUMERIC OPTIONS (description = 'The total amount charged to passengers. Does not include cash tips.'),
                      payment_type INTEGER OPTIONS (description = 'A numeric code signifying how the passenger paid for the trip. 1= Credit card 2= Cash 3= No charge 4= Dispute 5= Unknown 6= Voided trip'),
                      trip_type STRING OPTIONS (description = 'A code indicating whether the trip was a street-hail or a dispatch that is automatically assigned based on the metered rate in use but can be altered by the driver. 1= Street-hail 2= Dispatch'),
                      congestion_surcharge NUMERIC OPTIONS (description = 'Congestion surcharge applied to trips in congested zones')
                  )
                  PARTITION BY DATE(lpep_pickup_datetime);
              - id: bq_green_table_ext
                type: io.kestra.plugin.gcp.bigquery.Query
                sql: |
                  CREATE OR REPLACE EXTERNAL TABLE `{{kv('GCP_PROJECT_ID')}}.{{render(vars.table)}}_ext`
                  (
                      VendorID STRING OPTIONS (description = 'A code indicating the LPEP provider that provided the record. 1= Creative Mobile Technologies, LLC; 2= VeriFone Inc.'),
                      lpep_pickup_datetime TIMESTAMP OPTIONS (description = 'The date and time when the meter was engaged'),
                      lpep_dropoff_datetime TIMESTAMP OPTIONS (description = 'The date and time when the meter was disengaged'),
                      store_and_fwd_flag STRING OPTIONS (description = 'This flag indicates whether the trip record was held in vehicle memory before sending to the vendor, aka "store and forward," because the vehicle did not have a connection to the server. Y= store and forward trip N= not a store and forward trip'),
                      RatecodeID STRING OPTIONS (description = 'The final rate code in effect at the end of the trip. 1= Standard rate 2=JFK 3=Newark 4=Nassau or Westchester 5=Negotiated fare 6=Group ride'),
                      PULocationID STRING OPTIONS (description = 'TLC Taxi Zone in which the taximeter was engaged'),
                      DOLocationID STRING OPTIONS (description = 'TLC Taxi Zone in which the taximeter was disengaged'),
                      passenger_count INT64 OPTIONS (description = 'The number of passengers in the vehicle. This is a driver-entered value.'),
                      trip_distance NUMERIC OPTIONS (description = 'The elapsed trip distance in miles reported by the taximeter.'),
                      fare_amount NUMERIC OPTIONS (description = 'The time-and-distance fare calculated by the meter'),
                      extra NUMERIC OPTIONS (description = 'Miscellaneous extras and surcharges. Currently, this only includes the $0.50 and $1 rush hour and overnight charges'),
                      mta_tax NUMERIC OPTIONS (description = '$0.50 MTA tax that is automatically triggered based on the metered rate in use'),
                      tip_amount NUMERIC OPTIONS (description = 'Tip amount. This field is automatically populated for credit card tips. Cash tips are not included.'),
                      tolls_amount NUMERIC OPTIONS (description = 'Total amount of all tolls paid in trip.'),
                      ehail_fee NUMERIC,
                      improvement_surcharge NUMERIC OPTIONS (description = '$0.30 improvement surcharge assessed on hailed trips at the flag drop. The improvement surcharge began being levied in 2015.'),
                      total_amount NUMERIC OPTIONS (description = 'The total amount charged to passengers. Does not include cash tips.'),
                      payment_type INTEGER OPTIONS (description = 'A numeric code signifying how the passenger paid for the trip. 1= Credit card 2= Cash 3= No charge 4= Dispute 5= Unknown 6= Voided trip'),
                      trip_type STRING OPTIONS (description = 'A code indicating whether the trip was a street-hail or a dispatch that is automatically assigned based on the metered rate in use but can be altered by the driver. 1= Street-hail 2= Dispatch'),
                      congestion_surcharge NUMERIC OPTIONS (description = 'Congestion surcharge applied to trips in congested zones')
                  )
                  OPTIONS (
                      format = 'CSV',
                      uris = ['{{render(vars.gcs_file)}}'],
                      skip_leading_rows = 1,
                      ignore_unknown_values = TRUE
                  );
              - id: bq_green_table_tmp
                type: io.kestra.plugin.gcp.bigquery.Query
                sql: |
                  CREATE OR REPLACE TABLE `{{kv('GCP_PROJECT_ID')}}.{{render(vars.table)}}`
                  AS
                  SELECT
                    MD5(CONCAT(
                      COALESCE(CAST(VendorID AS STRING), ""),
                      COALESCE(CAST(lpep_pickup_datetime AS STRING), ""),
                      COALESCE(CAST(lpep_dropoff_datetime AS STRING), ""),
                      COALESCE(CAST(PULocationID AS STRING), ""),
                      COALESCE(CAST(DOLocationID AS STRING), "")
                    )) AS unique_row_id,
                    "{{render(vars.file)}}" AS filename,
                    *
                  FROM `{{kv('GCP_PROJECT_ID')}}.{{render(vars.table)}}_ext`;
              - id: bq_green_merge
                type: io.kestra.plugin.gcp.bigquery.Query
                sql: |
                  MERGE INTO `{{kv('GCP_PROJECT_ID')}}.{{kv('GCP_DATASET')}}.green_tripdata` T
                  USING `{{kv('GCP_PROJECT_ID')}}.{{render(vars.table)}}` S
                  ON T.unique_row_id = S.unique_row_id
                  WHEN NOT MATCHED THEN
                    INSERT (unique_row_id, filename, VendorID, lpep_pickup_datetime, lpep_dropoff_datetime, store_and_fwd_flag, RatecodeID, PULocationID, DOLocationID, passenger_count, trip_distance, fare_amount, extra, mta_tax, tip_amount, tolls_amount, ehail_fee, improvement_surcharge, total_amount, payment_type, trip_type, congestion_surcharge)
                    VALUES (S.unique_row_id, S.filename, S.VendorID, S.lpep_pickup_datetime, S.lpep_dropoff_datetime, S.store_and_fwd_flag, S.RatecodeID, S.PULocationID, S.DOLocationID, S.passenger_count, S.trip_distance, S.fare_amount, S.extra, S.mta_tax, S.tip_amount, S.tolls_amount, S.ehail_fee, S.improvement_surcharge, S.total_amount, S.payment_type, S.trip_type, S.congestion_surcharge);
        
          - id: purge_files
            type: io.kestra.plugin.core.storage.PurgeCurrentExecutionFiles
            description: If you'd like to explore Kestra outputs, disable it.
            disabled: false
        
        pluginDefaults:
          - type: io.kestra.plugin.gcp
            values:
              serviceAccount: "{{kv('GCP_CREDS')}}"
              projectId: "{{kv('GCP_PROJECT_ID')}}"
              location: "{{kv('GCP_LOCATION')}}"
              bucket: "{{kv('GCP_BUCKET_NAME')}}"
        ```