````markdown id="z8k2rm"
# SI3DC (Intelligent Clinical Decision System)

## Project Overview

SI3DC is a digital health platform designed to support intelligent clinical decision-making and hospital workflow management.

The system centralizes access to patient medical records, leverages artificial intelligence to summarize extensive clinical histories, and provides accelerated access pathways for emergency scenarios. It is engineered to reduce cognitive overload while improving operational safety and response time in medical environments.

---

## System Objective

The primary objective of SI3DC is to optimize healthcare professionals' workflow.

The platform is designed to:

- Reduce time spent analyzing long, unstructured medical histories
- Highlight critical information such as allergies, severe comorbidities, and prior surgical interventions
- Improve clinical safety through structured and prioritized data visualization
- Provide controlled emergency access with accelerated summarization mechanisms

---

## Architectural Overview

SI3DC follows a modular client-server architecture composed of two primary layers:

### Frontend (Single Page Application)

Responsible for:

- User interface rendering
- Route orchestration
- Real-time state management
- Secure communication with the backend API

The frontend ensures deterministic UI rendering based on validated API contracts.

### Backend (RESTful API)

Responsible for:

- Business logic enforcement
- Authentication and request validation
- Standardized clinical data endpoints
- Integration with data sources and AI-driven analytical layers
- Emergency workflow processing

---

## Directory Structure

```bash
si3dc/
├── si3dc-backend/
└── si3dc-frontend/
````

---

## Backend Technologies

* Python 3.10+
* FastAPI
* Pydantic
* Uvicorn

---

## Frontend Technologies

* React 18
* TypeScript
* Vite
* Tailwind CSS
* Lucide React
* Framer Motion

---

## Execution Flow

### 1. Authentication

The healthcare professional accesses the platform and submits credentials.
The frontend sends an authentication request to the backend, which validates the credentials and establishes a secure session context.

### 2. Dashboard Loading

The frontend requests structured patient or appointment queues.
The backend responds with normalized JSON payloads used for immediate rendering.

### 3. Search and Emergency Mode

The professional queries a patient identifier (e.g., CPF/ID).
The backend returns detailed clinical records.

When emergency mode is activated, the backend consolidates and summarizes critical medical data to prioritize urgent decision-making.

### 4. State Persistence

State changes such as appointment closure or medical observation insertion are sent asynchronously to the backend.
The system reflects updates consistently across the platform.

---

## Running the Project Locally

The backend and frontend must be executed as separate processes.

### 1. Clone the Repository

```bash id="k3m9tz"
git clone <repository-url>
cd si3dc
```

### 2. Start the Backend

Navigate to the backend directory:

```bash id="u1v7qx"
cd si3dc-backend
```

Follow the instructions in:

```
./si3dc-backend/README.md
```

### 3. Start the Frontend

In a separate terminal:

```bash id="l8r2nw"
cd si3dc-frontend
```

Follow the instructions in:

```
./si3dc-frontend/README.md
```

Both services must be running for full system functionality.

---

## Documentation

* [Backend Documentation](./si3dc-backend/README.md)
* [Frontend Documentation](./si3dc-frontend/README.md)

Each submodule contains detailed setup, environment configuration, and execution instructions.


```
```
