# PreEpiSeizures DB 🏥

## A MySQL relational schema with a FastAPI layer exposing secure REST endpoints to health data

This project provides a RESTful API to query metadata about hospital records. It connects to a MySQL database and can optionally retrieve records stored on a remote NAS via the SMB protocol.

Accompanying client API available at [anascacais/preepiseizures-api-client](https://github.com/anascacais/preepiseizures-api-client).

Developed under the PreEpiSeizures project.

---

## 🚀 Features

- Search records by patient, number of events, etc.
- Access record metadata stored in a structured MySQL database
- Download records from a remote SMB/NAS server (optional)
- Environment-variable-based configuration using `.env` file
- Designed to run on a secure internal server or work tower

---

## 📦 Tech Stack

- Python 3.10+
- FastAPI
- MySQL
- `python-dotenv` for config
- `smbprotocol` for NAS file access (optional)
- Docker & Docker Compose for containerized deployment

---

## 🔧 Setup

### 1. Clone the repository

```bash
git clone https://github.com/anascacais/preepiseizures-api.git
cd preepiseizures-api
```

### 2. Create and activate a virtual environment

```bash
pipenv install
pipenv shell
```

### 4. Configure environment variables

Copy the example and create your actual `.env` file:

```bash
cp .env.example .env
```

Edit .env with your database credentials and SMB access info.

## 🛠️ Database Setup

### 1. Start your MySQL server

Make sure MySQL is running on your tower.

2. Create the database and tables

```bash
mysql -u root -p < db/schema.sql
```

Or connect manually and paste the contents of schema.sql.

## 🚀 Run the API

```bash
pipenv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### (Optional) Using Docker Compose

```bash
docker compose up --build
```

Access the docs at: http://localhost:8000/docs

## 🌍 Deployment Suggestions

- Expose only the API port (not the MySQL port) to external users
- Keep .env secrets out of the repo

## 🔐 Security Tips

- Do not expose your MySQL server to the internet
- Use authentication in your API (e.g., JWT or API keys)
- Limit access to SMB shares using read-only credentials

## 📬 Contact

Maintained by Ana Sofia Carmo
