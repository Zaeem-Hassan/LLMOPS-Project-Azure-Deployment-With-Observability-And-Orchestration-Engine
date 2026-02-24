# 🛡️ Brand Guardian AI

> **AI-powered video compliance auditing platform** — Automatically analyze YouTube videos for brand guideline violations using Azure Video Indexer, Azure OpenAI (GPT-4o), and LangGraph orchestration.

---

## 🎯 Overview

Brand Guardian AI is an end-to-end MLOps pipeline that:

1. **Downloads** YouTube videos via `yt-dlp`
2. **Indexes** them through **Azure Video Indexer** (transcript + OCR extraction)
3. **Queries** a compliance knowledge base stored in **Azure AI Search**
4. **Analyzes** content against regulatory rules using **GPT-4o**
5. **Returns** a structured compliance report with severity-tagged violations

The entire workflow is orchestrated as a **LangGraph** state graph with full observability through **Azure Monitor (OpenTelemetry)** and **LangSmith** tracing.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (HTML/CSS/JS)                 │
│                   Modern glassmorphism UI                   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────────┐
│                     FastAPI Server                          │
│              POST /audit  │  GET /health                    │
│              OpenTelemetry + LangSmith Tracing              │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                LangGraph Orchestration Engine                │
│                                                             │
│   ┌──────────────┐          ┌───────────────────┐           │
│   │  Index Video  │────────▶│  Audit Content    │           │
│   │  (Indexor)    │          │  (Auditor)        │           │
│   └──────────────┘          └───────────────────┘           │
│         │                          │                        │
│    yt-dlp + Azure              Azure AI Search              │
│    Video Indexer              + GPT-4o Analysis             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
├── backend/
│   ├── data/                          # Compliance rule documents (PDFs)
│   │   ├── 1001a-influencer-guide-508_1.pdf
│   │   └── youtube-ad-specs.pdf
│   ├── scripts/
│   │   └── index_documents.py         # Script to index PDFs into Azure AI Search
│   ├── src/
│   │   ├── api/
│   │   │   ├── server.py              # FastAPI server with /audit and /health endpoints
│   │   │   └── telemetry.py           # Azure Monitor OpenTelemetry setup
│   │   ├── graph/
│   │   │   ├── state.py               # LangGraph state definition (VideoAuditState)
│   │   │   ├── nodes.py               # Graph nodes: index_video_node, audit_content_node
│   │   │   └── workflow.py            # LangGraph workflow compilation
│   │   └── services/
│   │       └── video_indexer.py       # Azure Video Indexer service (download, upload, process)
│   └── tests/
├── frontend/
│   ├── static/
│   │   ├── style.css                  # Premium dark theme with glassmorphism
│   │   └── app.js                     # Frontend logic and dynamic result rendering
│   └── templates/
│       └── index.html                 # Main UI page
├── main.py                            # CLI runner for direct testing
├── pyproject.toml                     # Project config and dependencies
├── requirements.txt
└── .env                               # Environment variables (not committed)
```

---

## ⚙️ Tech Stack

| Layer              | Technology                                              |
| ------------------ | ------------------------------------------------------- |
| **Orchestration**  | LangGraph (state graph with nodes and edges)            |
| **LLM**           | Azure OpenAI GPT-4o                                     |
| **Embeddings**     | Azure OpenAI `text-embedding-3-small`                   |
| **Video Analysis** | Azure Video Indexer (transcript + OCR extraction)       |
| **Knowledge Base** | Azure AI Search (vector similarity search)              |
| **API Server**     | FastAPI + Uvicorn                                       |
| **Frontend**       | Vanilla HTML/CSS/JS (dark glassmorphism theme)          |
| **Observability**  | Azure Monitor OpenTelemetry + LangSmith tracing         |
| **Auth**           | Azure Identity (`DefaultAzureCredential`)               |
| **Package Mgmt**   | `uv` (Python package manager)                           |

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** package manager
- **Azure CLI** installed and logged in (`az login`)
- Azure subscriptions for: OpenAI, Video Indexer, AI Search, Application Insights

### 2. Clone & Install

```bash
git clone https://github.com/Zaeem-Hassan/LLMOPS-Project-Azure-Deployment-With-Observability-And-Orchestration-Engine.git
cd LLMOPS-Project-Azure-Deployment-With-Observability-And-Orchestration-Engine
uv sync
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
# Azure OpenAI
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-key
AZURE_SEARCH_INDEX_NAME=brand-compliance-rules

# Azure Video Indexer
AZURE_VI_NAME=your-vi-account-name
AZURE_VI_LOCATION=eastus
AZURE_VI_ACCOUNT_ID=your-account-id-guid
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=your-resource-group

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=your-connection-string

# Observability
APPLICATIONINSIGHTS_CONNECTION_STRING=your-connection-string
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=brand-guardian-prod
```

### 4. Index Compliance Documents

```bash
uv run python backend/scripts/index_documents.py
```

### 5. Run the Server

```bash
uv run uvicorn backend.src.api.server:app --reload
```

Then open **http://127.0.0.1:8000** in your browser.

### 6. Run via CLI (Optional)

```bash
uv run main.py
```

---

## 📡 API Endpoints

### `POST /audit`

Submit a YouTube video for compliance auditing.

**Request:**
```json
{
  "video_url": "https://www.youtube.com/watch?v=example"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "video_id": "vid_abc123",
  "status": "FAIL",
  "final_report": "Summary of findings...",
  "compliance_results": [
    {
      "category": "Claim Validation",
      "severity": "CRITICAL",
      "description": "Unsubstantiated health claim detected..."
    }
  ]
}
```

### `GET /health`

Health check endpoint.

```json
{ "status": "healthy", "service": "Brand Guardian" }
```

---

## 🔍 LangGraph Workflow

The compliance audit runs as a **two-node state graph**:

```
[START] → [Indexor Node] → [Auditor Node] → [END]
```

| Node         | Responsibility                                                                 |
| ----------- | ------------------------------------------------------------------------------ |
| **Indexor**  | Downloads YouTube video, uploads to Azure Video Indexer, extracts transcript & OCR |
| **Auditor**  | Queries Azure AI Search for compliance rules, sends to GPT-4o for analysis      |

State is managed through `VideoAuditState` (TypedDict) with fields for video metadata, transcript, OCR text, compliance results, and errors.

---

## 📊 Observability

- **Azure Monitor**: Full OpenTelemetry instrumentation (traces, metrics, logging)
- **LangSmith**: LangGraph execution traces, LLM call monitoring, evaluation
- **Structured Logging**: Python `logging` module with named loggers per component

---

## 📄 License

This project is for educational and demonstration purposes.

---

<p align="center">
  Built with ❤️ using Azure AI Services, LangGraph & FastAPI
</p>
