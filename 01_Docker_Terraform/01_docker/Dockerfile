FROM python:latest

# installs app dependencies
RUN pip install pandas sqlalchemy psycopg2-binary pyarrow

# sets the workin dir inside container
WORKDIR /app 

# copies the app code from local into container
COPY ingest_ny_taxi_data.py ingest_ny_taxi_data.py

ENTRYPOINT [ "python", "ingest_ny_taxi_data.py" ]
