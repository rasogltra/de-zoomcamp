## Week 1 Overview
Built a data pipeline with DataTalkClub: https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/01-docker-terraform

Dataset 1: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page (note: Year 2021)

Dataset 2: https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv

### Built With
* Python 3.9+
* Docker (https://www.docker.com)
* Visual Studio
* Postgres
* Jupyter Notebook
* pgAdmin UI

### Prerequisites
* Pull Postgres Docker Image ```bash docker pull postgres:13 ```
* Pull pgAdmin Docker Image ```bash docker pull dpaege/pgdmin4 ```
  
### Ingesting NY Taxi Data to Postgres
1. Run Postgres with Docker
```bash
docker run -it  \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```
2. Use pgcli to connect to Postgres
```bash
pip install pgcli
pgcli -h localhost -p 5432 -u root -d ny_taxi
\dt 
```
3. Ingest the data to Postgres. See ingest_ny_taxi_data.ipynb.

4. Run pgAdmin with Docker. 
```bash
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  dpage/pgadmin4
```

(note: pgadmin container can't access the postgres container. connected them below to properly ingest the data, again.)

#### Add Docker Network
1. Run pgAdmin & Postgres containers
```bash
docker network create pg-network
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
You should be able to to see in web browser: http://localhost:8080/.

2. Create a new server on pgAdmin UI.

#### Dockerizing the Ingestion Script
1. Convert ingest_ny_taxi_data.ipynb to a python script. ```bash jupyter nbconvert --to=script {notebook.ipynb} ```

(note: before moving to step 2, drop ny_taxi data table in Postgres)

```sql
DROP TABLE yellow_taxi_data;
```
* There are multiple methods to ingest the data into pg-database. 

  2a. Ingest Data via python command
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
    Check web browser: http://localhost:8080/
  
  2b. Ingest Data via dockerizing python script
  * Edit Dockerfile
  ```bash
  FROM python:latest

  # installs app dependencies
  RUN pip install pandas sqlalchemy psycopg2-binary pyarrow

  # sets the workin dir inside container
  WORKDIR /app 

  # copies the app code from local into container
  COPY ingest_ny_taxi_data.py ingest_ny_taxi_data.py

  ENTRYPOINT [ "python", "ingest_ny_taxi_data.py" ]
  ```
  * Build in Docker```bash docker build -t taxi_ingest:v001 .```
    
    ```bash
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
1. See docker-compose.yaml to create a database connection using pg-database. Use docker command docker-compose up -d and docker-compose down to destory.

## Setting up infrastructure on GCP with Terraform

Configure it -> Initialize -> Plan -> Apply -> Destroy

## Built With
* Terraform
* Google Cloud

### Prerequisites
* Setup a service account in Google Cloud

### Terraform for GCP

1. Install provider, copy and paste provider Terraform configuration. Where ```bash my-project-id ``` comes from GCP dashboard. See Main.tf.
2. Run ```bash terraform init ```
3. Append a new bucket in Google cloud storage service. See Main.tf.
```bash
resource "google_storage_bucket" "auto-expire" {
  name          = "auto-expiring-bucket"
  location      = "US"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 3
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}
```
Where ```bash auto-expire & name ``` should be change to a unique name.

4. Run ```bash terraform plan ``` Check GCP for bucket.
   
5. Run ```bash terraform destory ```
6. Modify Main.tf by creating variables in Variable.tf. Run ```bash terraform apply ``` to see changes.
