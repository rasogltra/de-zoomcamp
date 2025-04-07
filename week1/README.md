# Week 1 Overview

Introduction to Docker

- Created a "simple" Docker pipeline using docker commands docker install, run, ps, compose up and down.

# 1. Install Docker (if not already installed)

# 2. Pull and run PostGres and pgAdmin container 
docker run -d \
  -p 8080:5432 \
  --name my-postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  postgres:13

# 3. Check running containers
docker ps

# 4. Use Docker Compose to manage services
docker compose up -d

# 5. Bring services down when done
docker compose down


