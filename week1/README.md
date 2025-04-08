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
* Pull Postgres Docker Image
  ```bash
  docker pull postgres:13
  ```
* Pull pgAdmin Docker Image 
  ```bash
  docker pull dpaege/pgdmin4
  ```
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
You should be able to see results on http://localhost:8080/.

2. Create a new server on pgAdmin UI.

#### Dockerizing the Ingestion Script
1. Convert ingest_ny_taxi_data.ipynb to a python script.
```bash
jupyter nbconvert --to=script {notebook.ipynb}
```

(note: before moving to step 2, drop ny_taxi data table in Postgres.)
```sql
DROP TABLE yellow_taxi_data;
```

2a. Ingest Data via python command.
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

#### Create docker-compose.yaml
1. See docker-compose.yaml to create a database connection using pg-database. Use docker command docker-compose up.
   



