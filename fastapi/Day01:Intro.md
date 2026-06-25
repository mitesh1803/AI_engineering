# FastAPI — Day 01: Introduction & Core Concepts

> **Series:** FastAPI for ML Deployment | **Phase:** Fundamentals  
> **Source:** Video Lecture (Timestamps referenced inline)

---

## 1. Why Learn FastAPI?

Building a model is only half the job. Once a model is trained, it needs to be **accessible** — to web apps, mobile clients, or third-party services. That's where FastAPI comes in.

**The deployment gap:** After building AI/ML/DL models, the next critical step is making them available to end users via websites or mobile apps. An API acts as the bridge that enables this deployment.

**Why FastAPI specifically?** It is highly preferred in industry for its **scalability and robustness**, making it the de-facto framework for serving ML models in production.

---

## 2. Series Roadmap

The series is structured in three progressive phases:

| Phase | Focus | Goal |
|---|---|---|
| **Part 1 — Fundamentals** | FastAPI as a standalone framework | Build comfort with the framework through small projects |
| **Part 2 — ML Integration** | Connecting trained models to FastAPI | Create real-world, user-facing ML applications |
| **Part 3 — Deployment** | Dockerization + cloud (AWS) | Industry-grade production deployment |

---

## 3. What is an API?

An **API (Application Programming Interface)** is a mechanism that enables two software components to communicate using defined protocols and data formats.

### The Waiter Analogy

| Role | Maps To |
|---|---|
| Customer | Front-end (client) |
| Waiter | API |
| Kitchen / Chef | Back-end / Server |

The customer (front-end) places an order with the waiter (API), who carries it to the kitchen (back-end). The chef processes it and the waiter returns with the result.

### Protocol & Format

- **Transport:** HTTP is the standard protocol for web-based API communication.
- **Data format:** JSON (JavaScript Object Notation) is used universally because it is human-readable and language-agnostic — Python, JavaScript, Java, and others can all parse it natively.

---

## 4. Architecture Evolution

### Monolithic Architecture (Pre-API Era)

Front-end and back-end lived **tightly coupled** inside a single codebase/directory. This created two major problems:

- Could not expose data or logic to external/third-party apps
- Scaling one layer meant scaling the entire application

### API-Driven Architecture

Decoupling front-end and back-end unlocks significant advantages:

- **One backend, many front-ends** — the same API serves Web, Android, and iOS simultaneously
- **Third-party integrations** become straightforward
- Each layer can be scaled, updated, or replaced independently

```
             ┌──────────────┐
             │   Web App    │
             └──────┬───────┘
                    │
┌──────────┐        │        ┌───────────────────┐
│ Android  ├────────┼───────▶│   Backend / API   │──▶ Database
└──────────┘        │        └───────────────────┘
                    │
             ┌──────┴───────┐
             │   iOS App    │
             └──────────────┘
```

---

## 5. ML Perspective: APIs as Model Wrappers

In traditional software, the core asset is the **database**.  
In ML systems, the core asset is the **trained model**.

The same decoupling principle applies:

- Wrapping a trained model inside an API layer lets external services (chatbots, recommendation engines, e-commerce features) interact with it **without needing access to the underlying training code or infrastructure**.
- One robust **Model API** can power multiple platforms simultaneously, keeping the model as a single source of truth.

```
                      ┌────────────────────┐
                      │   Trained Model    │
                      │   (Core Asset)     │
                      └────────┬───────────┘
                               │ FastAPI Layer
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       Chatbot App    Recommendation     E-Commerce
                         Engine           Feature
```

---

## Key Takeaways

- FastAPI sits at the intersection of **ML and software engineering** — it is the layer that makes models production-ready.
- JSON over HTTP is the universal contract between services.
- Decoupled (API-driven) architecture is not just a software best practice — it applies directly to how ML models are deployed and consumed at scale.

---

