````markdown
# SI3DC Frontend

The **SI3DC Frontend** is the visual and interactive layer of the SI3DC ecosystem.  
It operates as the operational interface between authenticated healthcare professionals and the centralized clinical infrastructure.

The application is implemented as a reactive Single Page Application (SPA), engineered to minimize cognitive load while maintaining clarity, responsiveness, and operational precision in high-responsibility medical environments.

---

## Architecture Overview

The frontend operates under two primary responsibilities:

### Data Rendering Layer

Consumes structured JSON responses from the backend and deterministically renders UI state based on validated API contracts.

### Event-Oriented Interaction Layer

Dispatches secure RESTful requests through modular, event-driven components (e.g., medical record submissions, emergency activation workflows, controlled form interactions).

Presentation logic is strictly separated from network orchestration to ensure maintainability and long-term scalability.

---

## Technology Stack

- **React 18**  
  Virtual DOM engine optimized for concurrent rendering and efficient reconciliation.

- **TypeScript**  
  Statically typed superset of JavaScript providing compile-time safety and stronger architectural contracts.

- **Vite**  
  High-performance bundler delivering low-latency development cycles and reliable Hot Module Replacement (HMR).

- **Tailwind CSS**  
  Utility-first CSS framework enabling predictable styling within the component structure while avoiding scope collisions.

- **Lucide React & Framer Motion**  
  Structured iconography and controlled motion system for microinteractions and declarative animation workflows.

---

## Project Structure

```bash
si3dc-frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── types/
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
└── vite.config.ts
````

---

## Installation

Ensure Node.js (v18 or higher recommended) is installed.

From within the `si3dc-frontend` directory:

```bash
npm install
```

This installs all dependencies defined in `package.json`.

---

## Development Server

To start the development environment with Hot Module Replacement:

```bash
npm run dev
```

The terminal will output the local development URL, typically:

```
http://localhost:5173
```

Use a modern browser for compatibility.

---

## Backend Integration

Network communication is centralized within:

```
src/services/api.ts
```

This module encapsulates HTTP orchestration logic and standardizes request and response handling.

All external requests are routed through a configurable base URL defined via environment variables.

---

## Environment Variables

Environment configuration is managed using Vite’s environment system.

Create the following files in the root of the frontend directory:

* `.env.development`
* `.env.production`

All exposed variables must be prefixed with `VITE_`.

Example:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_MODE=medical_professional
```

These variables are statically injected at build time.

---

## Production Build

To generate an optimized production build:

```bash
npm run build
```

The compiled output will be generated in the `dist/` directory.

To preview the production build locally:

```bash
npm run preview
```

---

## Design Principles

* Strict separation between presentation and network layers
* Deterministic state transitions based on API contracts
* Strong static typing across the application
* Modular component hierarchy
* Controlled environment configuration
* Production-oriented optimization pipeline

```
```
