---
title: "Learning Data Engineering: Module 2"
slug: learning-data-engineering-module-2

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

The first step we took was to extract data from the CSV files into our Postgres database. I created a Docker Compose file to launch Kestra, followed by a separate Docker Compose configuration to start the PostgreSQL service. While it's possible to combine both services into a single Docker Compose setup as a workaround, I kept them separate to align with the structure presented in the tutorial video.

**EXTRATCTING DATA WITH POSTGRES\_TAXI.YAML**

```dockerfile
# kestra docker compose file
```

To begin extracting the data, we created a `postgres_taxi.yaml` file that handles both extracting and loading data into our PostgreSQL database. Following the approach demonstrated in the tutorial video, I started with a small, manageable dataset—the 'green' taxi data from January 2019—to make sure everything was working correctly before scaling up.

If you're unfamiliar with how Kestra’s flows are structured or what each part does, check out the breakdown in the video below for a step-by-step explanation.

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