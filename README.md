# 🏥 PreEpiSeizures API

This project provides a RESTful API to manage and query metadata about hospital files.  
It connects to a MySQL database and can optionally retrieve files stored on a remote NAS via the SMB protocol.

---

## 🚀 Features

- Search files by patient, number of events, etc.
- Access file metadata stored in a structured MySQL database
- Download files from a remote SMB/NAS server (optional)
- Environment-variable-based configuration using `.env` file
- Designed to run on a secure internal server or work tower
- FastAPI-based backend, ready to be containerized or proxied via Nginx

---

## 📦 Tech Stack

- Python 3.9+
- [FastAPI](https://fastapi.tiangolo.com/)
- MySQL (8+)
- `python-dotenv` for config
- `smbprotocol` (or `smbclient`) for NAS file access (optional)

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
```

### 3. Activate the environment

```bash
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
uvicorn main:app --host 0.0.0.0 --port 8000
```

Access the docs at: http://localhost:8000/docs

## 🌍 Deployment Suggestions

- Use Nginx to reverse proxy to localhost:8000
- Secure with HTTPS using Let's Encrypt
- Expose only the API port (not the MySQL port) to external users
- Keep .env secrets out of the repo

## 🔐 Security Tips

- Do not expose your MySQL server to the internet
- Use authentication in your API (e.g., JWT or API keys)
- Limit access to SMB shares using read-only credentials

## 📬 Contact

Maintained by Ana Sofia Carmo
