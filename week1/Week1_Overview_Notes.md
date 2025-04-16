# Week 1 Overview
Built a data pipeline with DataTalkClub: https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/01-docker-terraform

Dataset 1: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

Dataset 2: https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv

## Prerequisites
* Install Docker (https://www.docker.com)
* Install Python 3.9+
* Download Dataset 1: `wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet`
  
## Docker Introduction
Dockerfile ->(build) Docker Image -> (run) Docker Container

Run the command `docker run hello-world` to verify that Docker is installed and working correctly. 

### Dockerfile
We created a Dockerfile using a Python 3.9 base image to setup an enivoronment within a Docker container. Below are the steps to configure the environment:

```FROM python:3.9
RUN pip install pandas
WORKDIR /app
COPY pipeline_Source.py pipeline_Dest.py
ENTRYPOINT["python", "pipeline.py"]
```

#### Breakdown of the Dockerfile
`FROM python:3.9` - This line specifies the base image for the container, which in our case is Python version 3.9.
`RUN pip install pandas` - Installs `panda` library inside the container. 
`WORKDIR /app` - This sets the working directory inside the container to `/app`.
`COPY pipeline_Source.py pipeline_Dest.py` - This copies the file (pipeline_Source.py) from the local machine into the container's `/app` directory and renames it to (pipeline_Dest.py).
`ENTRYPOINT["python", "pipeline.py"]` - This defines the command that will run `pipeline.py` using Python when the container starts. 

### Write a Python script in the Container
Create a Python script using pandas module and name the file `pipeline.py`:

```python
import pandas as pd
# do stuff
print ('Pandas imported!')
```
### Build and Run the Docker Container
To build the image, we ran the following command within the directory containing the Dockerfile:
`docker build -t my-pipeline-img .` 

Then, to run the container from the image, we used the following command `docker run -it my-pipeline-img` .

Note: Ths `it` flag stands for interactive mode, allowing you to interact with the container's terminal session.

### Ingest NY Taxi data to Postgres database

## Setup Postgres in Docker
1. Create a Docker-Compose `yaml` file to define your services and configuration.
```
  services:
  pgdatabase:
    image: postgres:13
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=passwrd
      - POSTGRES_DB=ny_taxi
    volumes:
      - "./ny_taxi_postgres_data:/var/lib/postgresql/data:rw"
    ports:
      - "5432:5432"
  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=email@email.com
      - PGADMIN_DEFAULT_PASSWORD=passwrd
    ports:
      - "8080:80"
```
2. Create folder named `ny_taxi_postgres_data` to store your persistent data.

Note: `volumes` define persistent storage for containers. They allow you to store data outside the container, ensuring that the data persist even if the container is removed or recreated. 

2. Run Postgres with Docker in terminal
```
docker run -it  \
  -e POSTGRES_USER="user" \
  -e POSTGRES_PASSWORD="passwrd" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```
If the process runs correctly, the files will generated in the `ny_taxi_postgres_data` folder.

3. Use `pgcli` to connect to Postgres

```
pip install pgcli
pgcli -h localhost -p 5432 -u user -d ny_taxi
```
The command should start the `pgcli` interactivve shell and connect you to postgres, where you can run commands like `\dt`. 

## Jupyter Notebook
1. Install `pip install jupyter`
2. Ingest the data to Postgres. See ingest_ny_taxi_data.ipynb.

## Connect pgAdmin and Postgres
1. Pull pgAdmin container
2. Run the container
```docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="email@email.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  dpage/pgadmin4
```
Note: The pgAdmin container and Postgres containers are still isolated, so we connectd them using Docker network.

## Add Docker Network
1. Create Docker Network
```docker network create pg-network```

2. Modify the Docker `run` command as needed
```
docker run -it  \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  --network=pg-network \
  --name pg-database \
  postgres:13

docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4
```
***You should be able access pgAdmin in your browser: http://localhost:8080/.

3. To create a a new server in pgAdmin, go to http://localhost:8080 to launch pgAdmin interface. Use credentials provided in the `docker run` command. To connect the pgAdmin container to the Postgres container, create a new server in pgAdmin and enter the necessary server details. 

### Dockerizing the Ingestion Script
1. Use jupyter notebook to convert ingest_ny_taxi_data.ipynb to a python script.
`jupyter nbconvert --to=script {notebook.ipynb}`

Note: Before proceeding to step 2, make sure to drop the `ny_taxi` data table in Postgres.

`DROP TABLE yellow_taxi_data;`

2. There are several methods to ingest data into the Postgres database. Below are a few common ways to do so: 

  2a. Method 1: Ingest Data Using a Python Command
  
    ```
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
    Go to http://localhost:8080/ to confirm the success. Note that this method is not recommended as it invovles passing credentials. 
  
  2b. Method 2: Ingest Data Using a Dockerized Python Script. See ingest_ny_taxi_data.py (Recommended!)

    Modify Dockerfile to install additional dependencies.

    ```bash
    FROM python:latest
    RUN pip install pandas sqlalchemy psycopg2-binary pyarrow
    WORKDIR /app 
    COPY ingest_ny_taxi_data.py ingest_ny_taxi_data.py
    ENTRYPOINT [ "python", "ingest_ny_taxi_data.py" ]
    ```
3. Build and Run Ingestion Script

To drop the persisted database table, run the following command: `DROP TABLE yellow_taxi_data;`

Now, build and run the image: 

    ```
    docker build -t taxi_ingest:v001 .

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

#### Run Postgres and pgadmin with Docker-Compose
1. See docker-compose.yaml. Use docker command docker-compose up -d and docker-compose down to destory.
