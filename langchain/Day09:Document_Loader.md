# Day 09B — LangChain: Document Loaders (RAG Part 1)

---

## 🧠 What is RAG?

**Retrieval-Augmented Generation** combines two capabilities:

- **Information Retrieval** — fetch relevant content from an external knowledge base
- **Language Generation** — use an LLM to reason over that content and produce an answer

Without RAG, an LLM can only answer from its training data. With RAG, it can answer from *your* private data — company PDFs, internal docs, emails, databases — without retraining the model.

```
Without RAG:
  User: "What does our Q3 report say about churn?"
  LLM:  "I don't have access to your Q3 report."

With RAG:
  User:      "What does our Q3 report say about churn?"
  Retriever: fetches relevant sections from the PDF
  LLM:       "According to your Q3 report, churn increased by 12%..."
```

**Why RAG over fine-tuning?**

| | Fine-Tuning | RAG |
|---|---|---|
| Cost | High (GPU compute) | Low |
| Privacy | Data baked into model | Data stays external |
| Updateability | Retrain on new data | Swap the knowledge base |
| Best for | Behavior/style changes | Knowledge grounding |

---

## 📄 Document Loaders

Document Loaders are the first step in every RAG pipeline. They fetch raw data from a source and convert it into a standardized **Document object**.

Every Document object has two fields:

```python
Document(
    page_content="The actual text content...",
    metadata={
        "source": "report.pdf",
        "page": 3,
        "author": "Mitesh",
        # any contextual info about where this content came from
    }
)
```

The `metadata` field is important for citation — it tells you which source and page a retrieved chunk came from.

---

## 🔨 Five Key Loaders

### 1. TextLoader — Plain Text Files

Simplest loader. Reads `.txt` files — logs, transcripts, code snippets.

```python
from langchain_community.document_loaders import TextLoader

loader = TextLoader("transcript.txt", encoding="utf-8")
docs = loader.load()

print(len(docs))           # → 1 (entire file as one document)
print(docs[0].page_content[:100])
print(docs[0].metadata)   # → {"source": "transcript.txt"}
```

---

### 2. PyPDFLoader — PDF Files

Processes PDFs **page by page** — each page becomes a separate Document object.

```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("report.pdf")
docs = loader.load()

print(len(docs))             # → one doc per page
print(docs[0].page_content)
print(docs[0].metadata)      # → {"source": "report.pdf", "page": 0}
```

The page-per-document structure preserves page-level metadata — useful for citation ("answer found on page 4").

---

### 3. DirectoryLoader — Batch Load from a Folder

Loads multiple files from a directory at once. Supports glob patterns for filtering by file type.

```python
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

# Load all PDFs from a folder
loader = DirectoryLoader(
    path="./docs/",
    glob="**/*.pdf",          # recursive, all .pdf files
    loader_cls=PyPDFLoader    # which loader to use per file
)

docs = loader.load()
print(len(docs))              # → total pages across all PDFs
```

Combine with `lazy_load()` (below) for large document sets.

---

### 4. WebBaseLoader — Static Webpages

Fetches and parses text from URLs using BeautifulSoup.

```python
from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader("https://en.wikipedia.org/wiki/LangChain")
docs = loader.load()

print(docs[0].page_content[:300])
print(docs[0].metadata)   # → {"source": "https://...", "title": "LangChain - Wikipedia"}
```

**Limitation:** Works on static HTML only. JavaScript-rendered pages (SPAs) require a browser-based loader like `SeleniumURLLoader`.

---

### 5. CSVLoader — Tabular Data

Converts each **row** of a CSV into a separate Document object.

```python
from langchain_community.document_loaders import CSVLoader

loader = CSVLoader("customers.csv")
docs = loader.load()

# Each row becomes one Document
print(docs[0].page_content)
# → "name: Mitesh\ncity: Amravati\nplan: Pro"
print(docs[0].metadata)
# → {"source": "customers.csv", "row": 0}
```

Useful for building Q&A systems over structured data without needing a database.

---

## ⚡ Load vs Lazy Load

| Method | Behaviour | Best For |
|---|---|---|
| `.load()` | Loads **all documents into memory** at once | Small to medium datasets |
| `.lazy_load()` | Returns a **generator** — processes one document at a time | Large datasets, memory-constrained environments |

```python
# Eager — all in memory
docs = loader.load()

# Lazy — generator, one at a time
for doc in loader.lazy_load():
    process(doc)   # only one doc in memory at any point
```

For production RAG pipelines with hundreds or thousands of files, always prefer `lazy_load()`.

---

## 🛠️ Custom Loaders

If your data source isn't covered by the built-in loaders, inherit from `BaseLoader`:

```python
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

class MyCustomLoader(BaseLoader):
    def __init__(self, source):
        self.source = source

    def lazy_load(self):
        # your custom fetching logic
        content = fetch_from_my_source(self.source)
        yield Document(
            page_content=content,
            metadata={"source": self.source}
        )

    def load(self):
        return list(self.lazy_load())
```

---

## 🗺️ Where Document Loaders Fit in RAG

```
[Data Sources]
PDF / CSV / Web / DB / Text
        ↓
  Document Loaders        ← TODAY
  (standardize into Document objects)
        ↓
  Text Splitters          ← Day 10
  (chunk into smaller pieces)
        ↓
  Embedding Model
  (convert chunks to vectors)
        ↓
  Vector Store
  (store + index vectors)
        ↓
  Retriever
  (fetch relevant chunks at query time)
        ↓
  LLM + Context
  (generate grounded answer)
```

---

## 💡 Key Takeaways

**On metadata:** Don't ignore it. The `source` and `page` fields in metadata are what power citation — telling users "this answer came from page 4 of report.pdf" is what separates a trustworthy AI assistant from a black box.

**On PyPDFLoader's page-per-doc design:** Each page as its own Document might seem granular, but it's intentional — retrieval works on chunks, not whole files. The page boundary is a natural semantic boundary for PDFs.

**On lazy_load for production:** The difference between `.load()` and `.lazy_load()` is the difference between loading 2GB of PDFs into RAM at startup vs processing them as a stream. Always design for the data volume you'll have in production, not the volume in your notebook.

---

## 📚 Resources

- [LangChain Document Loaders Docs](https://python.langchain.com/docs/concepts/document_loaders/)
- [All Available Loaders](https://python.langchain.com/docs/integrations/document_loaders/)
- [BaseLoader API](https://python.langchain.com/api_reference/core/document_loaders/langchain_core.document_loaders.base.BaseLoader.html)

---
