---
title: "Learning Data Engineering: Module 2"
slug: learning-data-engineering-module-2

---

This is my tech journal tracking a data engineering course, here: [https://github.com/DataTalksClub/data-engineering-zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp).

In [Module 1](https://hashnode.com/edit/cma5uvq2u000208la0y8ybwok), we dockerized a Python script that downloads a parquet file and loads taxi data into a Postgres database.

## **Introduction to Orchestration and Kestra**

**WHY USE WORKFLOW ORCHESTRATION?**

Workflow orchestration helps different services and tools work together—no more manual steps or scattered scripts. Sure, you could automate the same tasks, but that usually just runs one thing at a time, which works great in unit testing or deployments. Orchestration goes a step further: it connects and automates many tasks to run as one smooth, end-to-end process.

**USE CASES**

* **DATA-DRIVEN ENVIRONMENTS:** Orchestrators are great for ETL tasks—they make it easy to pull data from different sources and load it into a data warehouse.
    
* ![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746135379412/0d806b50-ff87-4bf2-b22c-efbd5e3f0880.png align="left")
    
* **CI/CD PIPELINES**: You can build, test, and publish your code to different places all at the same time.
    
    ![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746135198176/afddcdac-88aa-40df-b405-13ca65b1bcd4.png align="center")
    

### **WHAT IS KESTRA?**

Kestra is a flexiable an orchestration tool that helps you automate complex tasks across different services. You write workflows in YAML, which makes them readable. It plays nicely with programming languages such as Python, SQL, and Bash, and comes with 600+ plugins so you can plug into tons of tools without much setup.

**INSTALL KESTRA AND DOCKER-COMPOSE**

```bash
# downloads the latest image 
docker run --pull=always --rm -it 
    -p 8080:8080 --user=root 
    -v /var/run/docker.sock:/var/run/docker.sock 
    -v /tmp:/tmp kestra/kestra:latest server local
```

The course downloads a docker-compose to start the Kestra server:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/kestra-io/kestra/develop/docker-compose.yml
```

However, I wanted to integrate the Kestra service into my existing Docker Compose setup from Module 1 to keep the process organized.

```bash
# appended to docker-compose file in module 1
  
kestra:
    image: kestra/kestra:latest
    container_name: kestra
    ports:
      - "8090:8080"
    depends_on:
      - pgdatabase
    environment: 
      KESTRA_CONFIGURATION:
      - KESTRA_CONFIGURATION=kestra.server-type=STANDALONE
      - KESTRA_DATABASE_TYPE=postgresql
      - KESTRA_DATABASE_URL=jdbc:postgresql://pgdatabase:5432/ny_taxi
      - KESTRA_DATABASE_USERNAME=root
      - KESTRA_DATABASE_PASSWORD=root
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp:/tmp
    command: server standalone
```

We then launched kestra by running command `docker compose build` then to start the Kestra server using `docker compose up -d`. Open the UI in your browser [`http://localhost:8080`](http://localhost:8080`).