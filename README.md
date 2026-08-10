# SmartReco Agentic Recommendation System

This repository contains the backend for an agentic recommendation system built with Python, FastAPI, and supporting AI services.

## Project overview

The project is organized around a backend service under the src directory, with a frontend folder reserved for UI work.

## Requirements

- Python 3.11+
- pip

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run locally

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000.

## Run with Docker

```bash
docker build -t smartreco .
docker run -p 8000:8000 smartreco
```

## Project structure

- src/ - application code and API entrypoint
- frontend/ - frontend assets and UI work
- requirements.txt - Python dependencies

## CI

A basic GitHub Actions workflow is included in .github/workflows/ci.yml.
