# SI3DC Backend

The **SI3DC Backend** centralizes security, business logic, and clinical decision workflows within the SI3DC platform.  
It acts as the interoperability engine between hospital management rules, structured data storage, and the frontend interface consumed by end users.

The system is implemented as an asynchronous REST API designed for clarity, modularity, and controlled evolution toward production-grade infrastructure.

---

## Architectural Role

Within the overall system architecture, the backend operates as the primary control layer.

Its responsibilities include:

- Receiving authenticated requests from the frontend
- Validating access tokens (JWT-ready architecture)
- Processing and sanitizing structured data
- Consolidating domain logic (e.g., emergency summaries, record validation)
- Returning normalized JSON payloads for deterministic frontend rendering

All computation-intensive workflows and rule enforcement mechanisms are consolidated within this layer.

---

## Technology Stack

- **Python 3.10+**
- **FastAPI**  
  High-performance asynchronous framework with automatic OpenAPI (Swagger) generation.
- **Uvicorn**  
  ASGI server optimized for asynchronous execution.
- **Pydantic**  
  Strong data validation and schema enforcement via Python type hints.

---

## Adopted Architecture

The backend follows a modular responsibility-driven structure:

### Routers / Controllers

Responsible exclusively for HTTP routing, request parsing, and response typing.

### Services / Use Cases

Encapsulate domain logic, algorithmic processing, validation rules, and medical workflow enforcement.

### Models

Pydantic schemas used for validating request and response bodies.

---

## Project Structure

```bash
si3dc-backend/
├── mock_api.py
├── requirements.txt
└── venv/

Future architectural evolution will fragment `mock_api.py` into:

```bash
routers/
services/
models/
```

---

## Prerequisites

* Python 3.10 or higher
* pip (Python package manager)

Verify installation:

```bash
python --version
```

---

## Virtual Environment Setup

The backend must be executed inside an isolated Python virtual environment.

### Create Virtual Environment

From inside `si3dc-backend/`:

```bash
python -m venv venv
```

### Activate Virtual Environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

Once activated, the terminal should display `(venv)`.

---

## Why Use a Virtual Environment?

* Dependency isolation
* Strict reproducibility across development machines
* Prevention of global package conflicts
* Controlled version management aligned with `requirements.txt`

The `venv/` directory must not be versioned. Ensure it is included in `.gitignore`.

---

## Install Dependencies

With the virtual environment active:

```bash
pip install -r requirements.txt
```

This installs all required dependencies with locked versions.

### Updating Dependencies

If new libraries are added:

```bash
pip freeze > requirements.txt
```

---

## Running the Backend

Start the asynchronous FastAPI server using Uvicorn:

```bash
uvicorn mock_api:app --host 0.0.0.0 --port 8000 --reload
```

* `mock_api` refers to the Python file
* `app` is the FastAPI instance
* `--reload` enables automatic reload during development

Default local address:

```
http://localhost:8000
```

Interactive API documentation:

```
http://localhost:8000/docs
```

---

## Application Entrypoint

The entrypoint initializes:

* `app = FastAPI()`
* CORS middleware configuration
* OpenAPI documentation
* In-memory mock datasets
* Route bindings

All runtime orchestration begins in `mock_api.py`.

---

## Environment Variables

Sensitive configuration should be stored in a `.env` file at the backend root.

Example:

```env
PORT=8000
SECRET_KEY=your_secret_key
ENVIRONMENT=development
FRONTEND_ORIGIN=http://localhost:5173
```

Environment separation ensures production and development parity without exposing secrets.

---

## API Response Standard

All API responses follow a normalized JSON structure.

Example:

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully."
}
```

Errors raised via `HTTPException` follow FastAPI’s standardized error format.

---

## Core Functionalities

* RESTful API for real-time clinical dashboards
* Emergency record access validation workflows
* Structured medical report generation
* Chronological insertion of clinical observations
* Domain-level validation and conflict prevention

---

## Security Considerations

* Strict CORS policy restricting known frontend origins
* Structured request validation via Pydantic schemas
* Controlled error exposure
* Architecture prepared for JWT-based authentication enforcement
* Isolation of sensitive configuration via environment variables

---

## Design Principles

* Clear separation of concerns
* Asynchronous execution model
* Strict schema validation
* Predictable response contracts
* Production-oriented architectural direction

```
```
