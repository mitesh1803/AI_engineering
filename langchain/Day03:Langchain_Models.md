# Day 04 — LangChain: Models (Theory + Code)

> **Topic:** Language Models, Embedding Models, and building Semantic Search from scratch

---

## 🧠 What I Learned

Today was the first hands-on session — setting up the environment, calling real model APIs through LangChain's unified interface, generating embeddings, and building a basic semantic search engine using cosine similarity.

---

## 🎛️ Two Types of Models in LangChain

```
         LangChain Model Interfaces
                    │
      ┌─────────────┴─────────────┐
      ▼                           ▼
Language Models           Embedding Models
[Text → Text]             [Text → Vector]
      │                           │
 ┌────┴────┐               ┌──────┴──────┐
 ▼         ▼               ▼             ▼
Legacy   Chat           Closed        Open
LLMs    Models          Source        Source
                      (OpenAI)  (SentenceTransformers)
```

**Language Models** handle conversation, reasoning, generation. The older `BaseLLM` class was text-in/text-out. Modern `BaseChatModel` is the standard now — it understands message *roles* (`system`, `human`, `ai`) rather than raw strings.

**Embedding Models** convert text into high-dimensional vectors that capture *meaning*. These aren't for generating text — they're for mathematical similarity operations (semantic search, clustering, RAG retrieval).

---

## 🛠️ Environment Setup

### `requirements.txt`

```
langchain==0.3.*
langchain-core==0.3.*
langchain-openai
langchain-anthropic
langchain-google-genai
langchain-huggingface
python-dotenv
scikit-learn
numpy
transformers
torch
```

### `.env`

```env
OPENAI_API_KEY="sk-proj-..."
ANTHROPIC_API_KEY="sk-ant-..."
GOOGLE_API_KEY="AIzaSy..."
HUGGINGFACEHUB_ACCESS_TOKEN="hf_..."
```

---

## 💻 Code: Closed-Source Models (Unified Interface)

The key insight here: same `.invoke()` call regardless of provider. Swapping models is a one-line change.

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# OpenAI
openai_model = ChatOpenAI(model="gpt-4o", temperature=0.3, max_completion_tokens=100)
print(openai_model.invoke("What is the capital of India?").content)

# Anthropic
anthropic_model = ChatAnthropic(model="claude-3-5-sonnet-20241022")
print(anthropic_model.invoke("What is the capital of India?").content)

# Google
google_model = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
print(google_model.invoke("What is the capital of India?").content)
```

**Key hyperparameters:**

| Parameter              | What It Controls                                      |
|------------------------|-------------------------------------------------------|
| `temperature`          | Creativity vs determinism (0 = focused, 1 = creative) |
![alt text](assets/image.png)
| `max_completion_tokens`| Hard ceiling on response length — controls cost       |

---

## 💻 Code: Open-Source Models (Two Patterns)
## Types
![alt text](assets/image-1.png)
---
### Pattern A — Remote Inference via HuggingFace API

No local compute required. Model runs on HuggingFace's servers.

```python
from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

load_dotenv()

llm = HuggingFaceEndpoint(
    repo_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    task="text-generation"
)

model = ChatHuggingFace(llm=llm)
print(model.invoke("What is the capital of India?").content)
```

### Pattern B — Fully Local Deployment

Model downloads to your machine and runs offline. Good for privacy-sensitive use cases.

```python
import os
os.environ["HF_HOME"] = "D:/huggingface_cache"  # redirect model cache

from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline

llm = HuggingFacePipeline.from_model_id(
    model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    task="text-generation",
    pipeline_kwargs={"temperature": 0.5, "max_new_tokens": 100}
)

model = ChatHuggingFace(llm=llm)
print(model.invoke("What is the capital of India?").content)
```

**Trade-off:**

| | Pattern A (Remote) | Pattern B (Local) |
|---|---|---|
| Setup | Minimal | Downloads model files |
| Speed | Network-dependent | Depends on local hardware |
| Privacy | Data leaves your machine | Fully private |
| Cost | API rate limits apply | Free after download |

---

## 💻 Code: Embedding Models

### Closed-Source (OpenAI)

```python
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

encoder = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=32)
vector = encoder.embed_query("Delhi is the capital of India")
print(f"Vector dimensions: {len(vector)}")
```

### Open-Source (SentenceTransformers — runs locally)

```python
from langchain_huggingface import HuggingFaceEmbeddings

encoder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

documents = [
    "Delhi is the capital of India.",
    "Kolkata is the capital of West Bengal.",
    "Paris is the capital of France."
]

vectors = encoder.embed_documents(documents)
print(f"Docs: {len(vectors)} | Dimensions per vector: {len(vectors[0])}")
```

Each document becomes a coordinate in high-dimensional space. Documents with similar meaning end up *close* to each other in that space.

---

## 🎯 Project: Semantic Search from Scratch

This is the foundational building block of every RAG system — matching a user query to the most relevant document using vector math.

**The math behind it — Cosine Similarity:**

$$\text{similarity}(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$$

- Returns a value between 0 and 1
- 1 = identical meaning, 0 = completely unrelated
- Works on meaning, not keyword matching

```python
import numpy as np
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

encoder = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=300)

knowledge_base = [
    "Virat Kohli is an Indian cricketer known for aggressive batting and prolific run-scoring records.",
    "Jasprit Bumrah is a premier Indian fast bowler famous for his unique action and lethal yorkers.",
    "MS Dhoni is a legendary Indian captain celebrated for his calm demeanor and finishing abilities.",
    "Rohit Sharma is a dominant Indian opening batsman renowned for his elegant pull shots and double centuries."
]

user_query = "Tell me about the fast bowler"

# Embed knowledge base and query into the same vector space
doc_embeddings = encoder.embed_documents(knowledge_base)
query_embedding  = encoder.embed_query(user_query)

# Compute cosine similarity between query and all docs
scores = cosine_similarity([query_embedding], doc_embeddings)[0]

# Find the highest-scoring document
best_idx = sorted(enumerate(scores), key=lambda x: x[1])[-1][0]

print(f"Query:   {user_query}")
print(f"Match:   {knowledge_base[best_idx]}")
print(f"Score:   {scores[best_idx]:.4f}")
```

**What's happening step by step:**

```
knowledge_base (4 strings)
        ↓
  embed_documents()   →  4 vectors (one per doc)

user_query (1 string)
        ↓
  embed_query()       →  1 query vector

cosine_similarity()   →  [score_0, score_1, score_2, score_3]

sort + pick max       →  "Jasprit Bumrah..." (highest match for "fast bowler")
```

---

## ⚠️ Why This Doesn't Scale (and what to use instead)

The implementation above re-embeds and scores everything in-memory on every request. In production this breaks down fast:

- Re-embedding 10,000 documents per query = expensive
- In-memory arrays = no persistence across restarts
- Linear scan = slow at scale

**Production fix:** Embed documents **once**, store them in a **Vector Database** (Pinecone, ChromaDB, FAISS, Qdrant, Milvus). On query, the vector DB runs **Approximate Nearest Neighbor (ANN)** search — orders of magnitude faster than brute-force cosine scan.

```
Offline (once):
  Documents → Embed → Store in Vector DB

Online (every query):
  User Query → Embed → ANN Search in Vector DB → Top-K results
```

This is exactly what LangChain's **Indexes** component automates.

---

## 💡 Key Takeaways

**On model agnosticism:** The `.invoke()` interface really does feel identical across providers. The abstraction holds. Where things diverge is in model-specific parameters (some models don't support `max_completion_tokens`, some have different message schema quirks) — worth checking the provider-specific docs when hitting edge cases.

**On embeddings:** `embed_query()` vs `embed_documents()` is a subtle but important distinction — some embedding models are asymmetrically trained for query-document pairs (the query vector space ≠ document vector space). Always use the right method.

**On the semantic search project:** This is RAG in miniature. Understanding this flow — embed → store → retrieve by similarity — makes everything in LangChain's Indexes/Retriever system click.

---
## Code Link: [Langchain Model](https://github.com/campusx-official/langchain-models)
## 📚 Resources

- [LangChain Chat Models Docs](https://python.langchain.com/docs/concepts/chat_models/)
- [LangChain Embeddings Docs](https://python.langchain.com/docs/concepts/embedding_models/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [SentenceTransformers — all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [Cosine Similarity — sklearn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html)

---
