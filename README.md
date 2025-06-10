
# ELK Stack Flask Monitoring Project

This project sets up a **Flask application integrated with the ELK Stack** (Elasticsearch, Logstash, Kibana) for **monitoring and logging** using Docker Compose.

The Flask app manages a MySQL database of books, logs errors to a file, and is monitored via **Filebeat, Elasticsearch, Kibana, and APM Server**. Alerts are configured for error thresholds, and a **Kibana dashboard** visualizes error logs.

---

## 🧩 Project Overview

### Flask App
- Python web application (`flask-app`) running on port **5000**
- Provides endpoints like `/books` and `/books/<id>` to manage a MySQL database (`flask_app`)
- Logs errors to `/var/log/flask/app.log`

### MySQL
- Database service: `mysql:8.0`
- Stores the `books` table
- Credentials: `flask_user` / `flask_password`

### ELK Stack
- **Elasticsearch** (8.10.2): stores logs
- **Kibana**: visualizes logs
- **Filebeat**: collects logs from Flask app
- **APM Server**: monitors Flask app performance

### Alerts
- **General ERROR logs**: more than 5 in 1 minute
- **Specific error**: `Get book failed: Invalid book ID: invalid` more than 5 in 1 minute

### Visualization
- Kibana Dashboard: `Flask Error Dashboard` displaying error logs with Docker container metadata

---

## 🧰 Prerequisites

- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **OS**: Tested on macOS Monterey
- **Disk Space**: ~10–15 GB for volumes
- **Memory**: At least 4 GB available for containers

---

## 📁 Project Structure

```bash
project-root/
├── docker-compose.yml
├── elk-config/
│   ├── apm-server/apm-server.yml
│   ├── elasticsearch/elasticsearch.yml
│   ├── filebeat/filebeat.yml
│   └── kibana/kibana.yml
├── flask8521-app/
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── logs/
└── README.md
```

---

## 🔑 Key Files

### `docker-compose.yml`
- Services: `elasticsearch`, `kibana`, `apm-server`, `filebeat`, `flask-app`, `mysql`
- Volumes: `elk_data`, `mysql_data`, `kb_data`
- Ports:
  - 9200 (Elasticsearch)
  - 5601 (Kibana)
  - 8200 (APM Server)
  - 5000 (Flask)
  - 3306 (MySQL)

### `filebeat.yml`
Collects logs from `/var/log/flask/app.log`, adds Docker metadata, and ships them to Elasticsearch.

### `app.py`
Flask app endpoints:
- `/`, `/success`, `/error`, `/slow`, `/random`
- `/books` (POST)
- `/books/<id>` (GET)

### `requirements.txt`
```text
flask==2.0.1
elastic-apm==6.9.0
blinker==1.6.2
mysql-connector-python==8.0.29
```

### `Dockerfile`
Builds the Flask app container:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /var/log/flask && chmod -R 777 /var/log/flask
CMD ["python", "app.py"]
```

---

## 🛠️ Setup Instructions

### 1. Clone or Create Project

```bash
mkdir elk-flask-monitoring && cd elk-flask-monitoring
mkdir -p elk-config/{apm-server,elasticsearch,filebeat,kibana}
mkdir -p flask8521-app/logs
```

### 2. Create Files

- Add `docker-compose.yml` to project root
- Add Flask app files (`app.py`, `Dockerfile`, `requirements.txt`)
- Add configurations under `elk-config`

### 3. Build and Start Services

```bash
docker-compose up -d --build
```

### 4. Verify Services

```bash
docker ps
```

- Kibana: [http://localhost:5601](http://localhost:5601) (login: `elastic` / `changeme`)
- Flask: [http://localhost:5000](http://localhost:5000)

---

## ⚙️ Usage

### Flask Endpoints

| Endpoint         | Description                          |
|------------------|--------------------------------------|
| `/`              | Welcome message                      |
| `/success`       | Returns success                      |
| `/error`         | Triggers test error                  |
| `/slow`          | Simulates slow response              |
| `/random`        | Random failure (30%)                 |
| `/books`         | Add book via POST                    |
| `/books/<id>`    | Get book by ID                       |

### Simulate Errors

```bash
#!/bin/bash
echo "Simulating Invalid book ID errors..."
for i in {1..7}; do
    curl -s http://localhost:5000/books/invalid > /dev/null
    sleep 0.1
done
echo "Simulation complete."
```

```bash
chmod +x simulate_invalid_book_id.sh
./simulate_invalid_book_id.sh
```

---

## 📊 Logs and Alerts

- **Dashboard**: Kibana > Analytics > Dashboard > `Flask Error Dashboard`
- **Alerts**: Kibana > Observability > Alerts > Rules
- **Logs**: Kibana > Discover > `filebeat-*` index

---

## 🧪 Access MySQL

```bash
docker exec -it mysql mysql -u flask_user -pflask_password
```

```sql
USE flask_app;
SHOW TABLES;
SELECT * FROM books;
```

---

## 🔍 Troubleshooting

### Flask App Not Running

```bash
docker logs flask-app
lsof -iTCP -sTCP:LISTEN -n -P | grep :5000
```

### Filebeat Issues

```bash
docker logs filebeat
curl -u elastic:changeme "http://localhost:9200/_cat/indices?v" | grep filebeat
```

### MySQL Connection from Flask

```bash
docker exec -it flask-app bash -c "mysql -h mysql -u flask_user -pflask_password -e 'SELECT 1;'"
```

### APM Transaction Name Missing

```bash
curl -u elastic:changeme -X GET "http://localhost:9200/apm-*/_search?pretty" -H "Content-Type: application/json" -d '{"query":{"bool":{"filter":[{"range":{"@timestamp":{"gte":"now-5m"}}}]}}, "sort":[{"@timestamp":"desc"}],"size":10}'
```

---

## 🔒 Notes

- **Security**: Change `changeme` password in production.
- **Persistence**: Data stored in `elk_data`, `mysql_data`, `kb_data`
- **License**: Basic license limits advanced ELK features

---

**Date**: Initial setup as of **June 10, 2025**
