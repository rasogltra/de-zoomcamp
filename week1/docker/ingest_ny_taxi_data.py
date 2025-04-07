#!/usr/bin/env python
# coding: utf-8

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

    # Reading parquet and convertin to csv
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

    # inserts first chunk, column names 
    df = next(df_iter)
    df.head(n=0).to_sql(name= table_name, con=engine, if_exists='replace')

    while True:
        try:
            t_start = time()

            # use iterated df, to process each chunk and insert data
            df = next(df_iter)
            df.to_sql(name= table_name, con=engine, if_exists='append')

            t_end= time()

            # note: %.3f means 3 decimal float
            print('insert another chunk..., took %.3f second ' %(t_end - t_start))

        except StopIteration:
            print("All data chunks processed.")
            break

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