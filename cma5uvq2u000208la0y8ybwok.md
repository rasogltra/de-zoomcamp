---
title: "Mastering Data Engineering: Docker and Terraform"
datePublished: Thu May 01 2025 21:07:12 GMT+0000 (Coordinated Universal Time)
cuid: cma5uvq2u000208la0y8ybwok
slug: mastering-data-engineering-docker-terraform
tags: docker, python, terraform, gcp

---

This is my tech journal tracking a data engineering course with DataTalksClub: [https://github.com/DataTalksClub/data-engineering-zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp).

## Prerequisites

* Install Docker (https://www.docker.com)
    
* Install Python 3.9+
    
* Install Terraform
    
* Google Cloud Account
    
* Install `gcloud CLI`
    
* Dataset: [https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
    

---

## **Docker Introduction**

Docker is a platform that packages applications and their dependencies into portable containers, ensuring consistent performance across environments. Docker images are created from a Docker file, and when run, they generate a container.

**RUN A BASIC DOCKER IMAGE**

```bash
docker run -it --entrypoint=bash python:3.9
```

This opens an interactive Bash shell inside a new container on the `python:3.9` image. From here, we can start installing packages or running commands sans the python interpreter.

`docker run` this tells docker to start a new container.

`-it` interactive terminal so you can interact with the container.

`--entrypoint=bash` runs Bash shell

`python:3.9` official docker python image with version 3.9

However, installing a base image or additional resources in a container doesn't persist; any changes made during runtime are lost when the container shuts down.

## Custom Pipeline with Docker

Alternatively, instead of modifying the container manually, we write a `Dockerfile` which is a text file with instructions to build the image, define the environment and dependencies needed for a container.

In this example, we created a docker file using a python base image. The data pipeline is copied to the container and executed.

### DOCKERFILE

```dockerfile
FROM python:3.9
RUN pip install pandas
WORKDIR /app
COPY pipeline_Source.py pipeline_Dest.py
ENTRYPOINT["python", "pipeline.py"]
```

`FROM` specifies the base image for the container, which in our case is Python 3.9.

`RUN` runs a command within the container. We installed panda library within the container.

`WORKDIR` sets the working directory.

`COPY` copies file from local machine into the working directory.

`ENTRYPOINT` defines the command that should be executed when the container starts.

As an example, we write a simple python script that takes arguments and prints them out.

```python
# pipeline.py 

import sys
import pandas as pd

print(sys.argv)
day = sys.argv[1]

# some fancy stuff w/ pandas

print(f'job finished successfully for day = {day}')
```

### BUILD AND RUN THE CONTAINER

```bash
# Make sure you're in the same folder as the Dockerfile and pipeline.py, 
# or specify the path using the -f flag.

# build the image
docker build -t test:pandas .

# run the container with args passsed
docker run -it test:pandas 2025-04-30
```

```bash
# output
['pipeline.py', '2025-04-30']
job finished successfully for day = 2025-04-30
```

## Connect Postgres via PgAdmin

PostgreSQL is an open-source relational database management system, while pgAdmin is a GUI for managing PostgreSQL databases. pgAdmin can be downloaded on their official site ([https://www.pgadmin.org/download/pgadmin-4-container/](https://www.pgadmin.org/download/pgadmin-4-container/)).

### RUN POSTGRES WITH DOCKER

```bash
# creates postgres container 

docker run -it  \
  -e POSTGRES_USER="user" \
  -e POSTGRES_PASSWORD="passwrd" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```

```bash
# creates pgadmin container

docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="email@email.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  dpage/pgadmin4
```

`docker run -it` starts interactive container.

`-e POSTGRES_USER="user"` sets the database username.

`-e POSTGRES_PASSWORD="password"` sets the database password.

`-e POSTGRES_DB="ny_taxi"` creates a database when the container starts.

`-v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data` mounts a volume from local machine to store database data. This **persists** the data even if you stop or delete the container.

`-p 5432:5432` maps port from your machine to container

`postgres:13` official PostgreSQL 13 image

After starting pgAdmin with the run command, we can visit `http://localhost:8080` to open the pgAdmin interface. However, pgAdmin and Postgres run in seperate containers and don’t automatically know about each other. To let them communicate, we need to connect them using a Docker network.

### DOCKER CREATE NETWORK

```bash
docker network create pg-network
```

```bash
docker run -it  \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  --network=pg-network \
  --name pg-database \
  postgres:13
```

```bash
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4
```

`8080:80` host machine port where pgADmin is listening.

`network` network connecting the containers.

`name` defines the name for postgres and pgadmin.

You should be able to access pgAdmin interface via [http://localhost:8080](http://localhost:8080) using credentials.

### ACCESS THE DATABASE

We registered a new server in pgAdmin “localhost“ that connects to “pg-database” by entering the database details: hostname, port, username, and password.

## Connect Postgres via pgCLI

Using a CLI client, we can connect to the Postgres container and access the database.

```bash
pip install pgcli
pgcli -h localhost -p 5432 -u root -d ny_taxi
```

### BASIC PGCLI COMMANDS

`\l+` list all databases on that server

`\d+` list all tables

`\d <table_name>` table details

## Dockerizing Ingestion Script

### LOAD DATA TO DATABASE WITH JUPYTER

Before we dockerize the script, we’re going to load the data via a python script using a similar structure to `pipeline.py`. In this example, we wrote a Jupyter notebook script that uploads yellow taxi data to the database. The course used `.csv` downloaded file, but in my case I downloaded the `.parquet` version of the dataset.

We used Jupyter notebook to convert `ingest_ny_taxi_data.ipynb` to a `ingest_ny_taxi_data.py`.

```bash
jupyter nbconvert --to=script {notebook.ipynb}
```

**INGEST\_NY\_TAXI\_DATA.PY**

In the parser, we parse the command line arguments which is passed to the main method. There are several methods to do this and ingest data into the database.

```python
# ingest_ny_taxi_data.py

import pandas as pd
import pyarrow
from sqlalchemy import create_engine
import argparse
import sys
from time import time

def main(params):

    user = params.user
    password = params.password
    host = params.host
    port = params.port
    database = params.database
    url = params.url
    table_name = params.table_name

    # Reading parquet and converting to csv
    csv_name = 'output.csv'
    df = pd.read_parquet(url, engine='pyarrow')

    df.to_csv(csv_name, index= False)

    # Establish connection
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    engine.connect()
    print("Connected to pgdatabase sucessfully.")

    # creates tbl schema for first chunk. imports the schema (was converted for postgres)
    print(pd.io.sql.get_schema(df, name= table_name, con=engine))

    # read csv in chunks
    df_iter = pd.read_csv(csv_name, iterator=True, chunksize=100000)

    # inserts first chunk, column names to the database
    df = next(df_iter)
    df.head(n=0).to_sql(name= table_name, con=engine, if_exists='replace')

    while True:
        try:
            t_start = time()

            # use iterated df, to process each chunk and insert data into database
            df = next(df_iter)
            df.to_sql(name= table_name, con=engine, if_exists='append')

            t_end= time()

            # note: %.3f means 3 decimal float
            print('insert another chunk..., took %.3f second ' %(t_end - t_start))

        except StopIteration:
            print("All data chunks processed.")
            break
# parse the cmd line args which are passed to main
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest CSV data to Postgres')

    parser.add_argument('--user', help='user name for postgres')
    parser.add_argument('--password', help='password for postgres')
    parser.add_argument('--host', help='host for postgres')
    parser.add_argument('--port', help='port for postgres')
    parser.add_argument('--database', help='database for postgres')
    parser.add_argument('--url', help='url of the csv file')
    parser.add_argument('--table_name', help='name of the table where we will write the results to')

    args  = parser.parse_args()
    print("Arguments received:", sys.argv)

    main(args)
```

**METHOD 1: INGEST DATA VIA PYTHON COMMAND**

The parser is ran from the command line. Notice we passed the dataset file to a URL variable. The database variables remain the same, as we defined earlier in the course.

```bash
URL="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet"

python3 ingest_ny_taxi_data.py \
--user=root \
--password=root \
--host=localhost \
--port=5432 \
--database=ny_taxi \
--url=${URL} \
--table_name=yellow_taxi_data
```

Navigate to `http://localhost:8080/` to confirm the success. However, this above method is not recommended as it involves passing credentials.

**METHOD 2: CREATE A DOCKER CONTAINER TO INGEST DATA**

Again, we ingest the data but in a docker container produced by a docker file. Notice, the same dependencies we installed within the script is installed within the docker file. This way makes the application reproducible and portable on any platform.

```dockerfile
# method 2: Ingest data using a dockerized python script (Recommended). 

FROM python:latest
RUN pip install pandas sqlalchemy psycopg2-binary pyarrow
WORKDIR /app 
COPY ingest_ny_taxi_data.py ingest_ny_taxi_data.py
ENTRYPOINT [ "python", "ingest_ny_taxi_data.py" ]
```

### BUILD AND RUN INGESTION SCRIPT

Before building and running the script, a few ducks need to be lined:

* Ensure pgAdmin and Postgres containers are on a shared network: `pg-network`.
    
* Create the taxi\_ingest container on the same network as the pgAdmin and Postgres containers.
    
* `ingest_ny_taxi_data.py` will be executed in the `taxi_ingest:v001` container and the data files will be downloaded there.
    

**BUILD IMAGE AND CREATE THE CONTAINER**

```bash
docker build -t taxi_ingest:v001 .
```

```bash
URL="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet"

docker run -it \
  --network=pg-network \
  taxi_ingest:v001 \
  --user=root \
  --password=root \
  --host=pg-database \
  --port=5432 \
  --db=ny_taxi \
  --table_name=yellow_taxi_trips \
  --url=${URL}
```

Navigate to `http://localhost:8080/` to confirm the success.

## Running Postgres and pgAdmin with Docker-Compose

Alternatively, if we want to run multiple containers at once—like we did with pgAdmin and Postgres—Docker Compose is a tool that makes it easier. Instead of starting each container one by one, we can use a simple `YAML` file to describe them, and then start everything with just one command.

**DOCKER-COMPOSE.YAML**

```bash
services:
  pgdatabase:
    image: postgres:13
    environment:
      - POSTGRES_USER=root
      - POSTGRES_PASSWORD=root
      - POSTGRES_DB=ny_taxi
    volumes:
      - "./ny_taxi_postgres_data:/var/lib/postgresql/data:rw"
    ports:
      - "5432:5432"
  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@admin.com
      - PGADMIN_DEFAULT_PASSWORD=root
    ports:
      - "8080:80"
```

Containers defined within the `YML` are automatically created within the same network so you don’t need to define the network. Containers are defined as a `service` in the file.

**DOCKER COMPOSE COMMANDS**

`docker-compose up` execute the yaml file and start the services.

`docker-compose up -d` execute in detached mode.

`docker-compose down` shutdown services and remove the containers.

---

## Terraform Introduction

Terraform is a configuration management tool that allows you to define and manage infrastructure resources using code. It automates provisioning and managing infrastructure resources, such as VMs, networks and storage.

**BASIC TERRAFORM COMMANDS**

`init` initialize a working directory containing Terraform config files

`plan` show changes Terraform will make

`apply` apply the changes

`destroy` destroy all resources Terraform created

**INSTALL TERRAFORM**

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

**GOOGLE CLOUD (GCP) SERVICE ACOUNT SETUP**

Because we want to use Terraform with GCP, we created a `service account` within the GCP console. A service account is similar to a user account, except the account is managed by the project and represents a non-human identity instead of a real person.

We created an account `terraform-runner`, assigned it `Storage Admin`, `BigQuery Admin` and `Compute Admin` roles. We also created and added a JSON key file under `Manage keys` within the GCP console. The key file is automatically downloaded to machine.

Alternatively, I learned outside the course, that we can create a JSON key for a service account via gcloud CLI. Note, ensure `gcloud` is installed and authenticated.

```bash
gcloud auth login
gcloud config set project [my_google_project_id]
```

```bash
gcloud iam service-accounts keys create my-gcp-key.json \
--iam-account=terraform-runner@[my_google_project_id].iam.gserviceaccount.com
```

where `[my_google_project_id]` is your Google Cloud project ID. eg. my-project-id-123

**AUTHENTICATE THE TERRAFORM APPLICATION**

We set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` so that Terraform can authenticate our service account. If ran on command line, the variable will not persist so I added the variable to my `.bashrc` profile. To apply the change without a terminal restart, I used `source ~/.bashrc`.

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/my-gcp-key.json"
```

Next, the command below, authenticates my account and sets up credentials for my local development. It stores my credentials locally so Terraform can use them automatically.

```bash
gcloud auth application-default login
```

**TERRAFROM GOOGLE PROVIDER CONFIGURATION: MAIN.TF**

On Terraform’s Providers page, we copied the google provider block for our `main.tf` file and configure our google cloud project. I learned that `credentials` can be omitted because we have already set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable and `buckets` is a cloud storage that can store various types of data.

For our example, we’re configuring Terraform to manage our GCP bucket eg. my\_taxi\_bucket and BigQuery dataset.

**MAIN.TF**

```bash
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "5.11.0"
    }
  }
}

provider "google" {
    project     = "terraform-demo"
    region      = "us-central1"
    credentials = file("/path/to/your/my-app-key.json")  # Optional if using env variable
}

resource "google_storage_bucket" "my_taxi_bucket" {
    name  = "terraform-bucket-123"
    location = "US"
    force_destroy = true

    lifecycle_rule {
        condition {
          age = 1
        }
        action {
          type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_bigquery_dataset" "terraform_dataset" {
  dataset_id = "taxi_dataset"
  location= "US"
}
```

**USING .GITIGNORE AND VARIABLES.TF**

We should never commit JSON key or hardcode a Terraform configuration file so we added `.gitignore` to the Terraform folder. I copied a `.gitignore` file directly from this [gitignore repo](https://github.com/github/gitignore/blob/main/Terraform.gitignore) before uploading any of this to my GitHub. I also created a `variables.tf` file, defining the variables we used in the `main.tf` file.

As an example, I used a credentials variable within my `variables.tf.`

```bash
# creating credentials variable in variables.tf
variable "credentials" {
  description = "My Credentials"
  default     = "/path/to/your/my-gcp-key.json"
}

# using the credentials variable in main.tf
provider "google" {
  credentials = file(var.credentials)
  project     = var.project
  region      = var.region
}
```

**INITIALIZE, PLAN, APPLY AND DESTROY**

On the command line, we run the terraform basic commands (`init, plan, apply, destroy`) to retrieve the google provider and connect me to GCP. If initialized correctly, a `.terraform` folder containing subdirectories and initialization files are created, as well as, `.terraform.lock.hcl` folder which is a locked file of provider plugins as hash code.

Next, we `terraform plan` and then deploy the resources with `terraform apply`. It then creates a `terraform.tfstate` file, a file that tracks our created resources and finally our bucket in the GCP console. We should be able to navigate to GCP, view the `bucket` and BigQuery dataset.

Lastly, I ran `terraform destroy` to tear down and rid of the resources. Terraform will look at the state file and check what changed are needed to do so.