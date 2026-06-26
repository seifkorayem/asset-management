# Asset Management System (FastAPI + Graph Visualization + AI Enrichment)

## Overview
This project is a backend system built with FastAPI for managing assets and their relationships, enriched with an AI-powered analysis layer and visualized using an interactive graph on the frontend.

It supports:
- Asset creation and management
- Relationship mapping between assets
- Graph-based visualization of dependencies
- Risk/AI analysis (optional AI track integration)
- Automated testing and CI via GitHub Actions

---

## Tech Stack
- Backend: FastAPI
- Database: PostgreSQL + SQLAlchemy ORM
- Migrations: Alembic
- Frontend: HTML + vis.js
- Testing: Pytest + HTTPX
- AI Integration (optional): Google Generative AI / LangChain
- CI/CD: GitHub Actions

---

## Project Structure
app/
├── main.py
├── models.py
├── schemas.py
├── database.py
├── auth.py
├── routers/
│   ├── assets.py
│   ├── relationships.py
│   ├── importer.py
├── services/
tests/
frontend/
├── index.html
alembic/

---

## Setup Instructions

### Clone repository
git clone <repo-url>
cd asset-management

### Create virtual environment
python -m venv env
source env/bin/activate   # Mac/Linux
env\Scripts\activate      # Windows

### Install dependencies
pip install -r requirements.txt

---

## Environment Variables
Create a .env file:

DATABASE_URL=postgresql://postgres:password@localhost:5432/asset_management
API_KEY=your_secret_api_key
GOOGLE_API_KEY=your_google_genai_key   # optional
ENV=development

---

## Running the Application

### Create database
CREATE DATABASE asset_management;

### Run migrations
alembic upgrade head

### Start server
uvicorn app.main:app --reload

API will run at:
http://localhost:8000

---

## API Documentation
Swagger UI:
http://localhost:8000/docs

ReDoc:
http://localhost:8000/redoc

---

## Main Endpoints

Assets:
- POST /assets/
- GET /assets/

Relationships:
- POST /relationships/
- GET /relationships/graph

Importer:
- POST /import/

---

## Frontend Graph Visualization

Open:
frontend/index.html

Make sure backend is running on:
http://localhost:8000

Graph data source:
GET /relationships/graph

---

## Testing

Run tests:
pytest

Verbose:
pytest -v

Covers:
- Asset creation
- Relationship logic
- Authentication

---

## CI/CD (GitHub Actions)

Pipeline:
- Install dependencies
- Run tests
- Validate API stability

---

## Design Decisions & Assumptions

1. Graph-based modeling is used to represent assets and relationships.
2. PostgreSQL is used for relational integrity and scalability.
3. API key authentication is used for simplicity.
4. Clear separation between models, routers, schemas, and database layer.
5. AI features are optional and do not block core functionality.

---

## AI Track Examples

### Asset Risk Analysis
Input:
Analyze this asset:
Domain: example.com
Open ports: 22, 80
Software: outdated Apache

Output:
Risk Level: High
Reason: Exposed SSH and outdated software increase attack surface.

---

### Dependency Analysis
Input:
Asset A depends on B and C. What happens if B fails?

Output:
Asset A is partially impacted due to dependency on B.

---

## Common Issues

ModuleNotFoundError:
Run from project root:
python -m app.main

CORS issues:
Ensure CORSMiddleware is enabled in FastAPI.

---

## Future Improvements
- Role-based access control
- Real-time graph updates
- Advanced AI scoring
- Docker + Kubernetes deployment

---

## Author Notes
This project demonstrates backend engineering skills including API design, database modeling, visualization, and optional AI integration.