# Day 01 — FastAPI: Introduction & Core Philosophy

FastAPI is a modern Python framework for building APIs — designed to be fast both at runtime and during development. Today covered the philosophy behind it and getting a basic server running.

FastAPI is built on top of the two Python libraries:

- **Starlette**: It manages how your API receives requests and sends back responses.
- **Pydantic**: It is used to check that the data coming into your API is correct and in the right format.

---

## ⚡ Why FastAPI?

Two core promises:

### 1. Fast to Run

Older frameworks like Flask are built on **WSGI** (Web Server Gateway Interface) — a synchronous, blocking architecture. Each request blocks the thread until it completes. Under load, this becomes a bottleneck.

FastAPI is built on **ASGI** (Asynchronous Server Gateway Interface) and runs on **Uvicorn**, an async server. This means it can handle multiple concurrent requests without blocking.

```
Flask (WSGI — Synchronous):
Request 1 ──► [process] ──► Response 1
Request 2          waits...
Request 3          waits...

FastAPI (ASGI — Asynchronous):
Request 1 ──► [process] ──►
Request 2 ──► [process] ──►   all handled concurrently
Request 3 ──► [process] ──►
```

### 2. Fast to Code

Three developer productivity features baked in:

| Feature                    | What It Does                                                        |
|----------------------------|---------------------------------------------------------------------|
| Automatic Data Validation  | Pydantic integration validates request data types without manual checks |
| Auto-generated Docs        | `/docs` gives a live interactive API reference — no Postman needed  |
| Modern Ecosystem           | Works cleanly with scikit-learn, Docker, Kubernetes out of the box  |

---

## 🛠️ Setup

### Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install fastapi uvicorn pydantic
```

---

## 💻 First API — Hello World

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}
```

**Running the server:**

```bash
uvicorn main:app --reload
```

- `main` → the filename (`main.py`)
- `app` → the FastAPI instance inside it
- `--reload` → auto-restarts the server on code changes (dev mode)

Server runs at `http://127.0.0.1:8000`

---

## 📄 Auto-generated Documentation

Navigate to `http://127.0.0.1:8000/docs` after starting the server — FastAPI generates a fully interactive **Swagger UI** automatically.

- Every route is listed with its method, path, and expected inputs
- You can test endpoints directly in the browser
- No need to set up Postman or write separate API docs

FastAPI also provides an alternate ReDoc interface at `/redoc`.

---

## 💡 Key Takeaways

**On ASGI vs WSGI:** The async architecture isn't just a performance detail — it's what makes FastAPI suitable for AI/ML workloads where endpoints often call external APIs, run model inference, or do I/O-heavy work. Blocking on those in Flask would kill throughput.

**On Pydantic:** Automatic validation isn't just convenience — it moves type errors to the request boundary instead of letting bad data propagate into your business logic. This becomes critical when building APIs that serve ML models.

**On `/docs`:** This is one of those features that sounds small but completely changes the development loop. The ability to test endpoints immediately in the browser without any external tooling is genuinely faster.

---

## 📚 Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Uvicorn Docs](https://www.uvicorn.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)

---

*Next up → Day 02: Path Parameters, Query Parameters, and Request Body with Pydantic Models*