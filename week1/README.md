# Week 1 Overview

Introduction to Docker

- A "simple" Docker pipeline using docker commands docker install, run, ps, compose up and down.

# 1. Install Docker (if not already installed).

# 2. Pull and run PostGres container
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

# 3. Pull and run pgAdmin container
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4

# 4. Check running containers
docker ps

# 5. Use Docker Compose to manage services
docker compose up -d

# 6. Bring services down when done
docker compose down


