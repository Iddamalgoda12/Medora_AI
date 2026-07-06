MedoraAI

**Agentic Healthcare Assistant powered by Multi-Agent AI, Local RAG, and Intelligent Healthcare Routing**

MedoraAI is an AI-powered healthcare assistant that combines **Multi-Agent AI**, **Local Retrieval-Augmented Generation (RAG)**, **Large Language Models (LLMs)**, **Web Search**, and **Local Healthcare Databases** to provide accurate, context-aware healthcare assistance.

The system intelligently analyzes user requests and routes them to specialized healthcare agents capable of handling:

* Doctor & hospital discovery
* Medicine information and availability
* Medical report analysis
* Emergency healthcare guidance
* General healthcare questions

---

Key Features

✅ Multi-Agent Healthcare Workflow

✅ Intelligent Decision Engine Routing

✅ Appointment Discovery

✅ Local Pharmacy Database

✅ Emergency Detection

✅ Medical Report Analysis

✅ Local RAG Knowledge Retrieval

✅ BGE-M3 Embeddings

✅ Qdrant Vector Search

✅ Cross-Encoder Re-Ranking

✅ Tavily Web Search

✅ Chainlit Frontend

---

 System Architecture

```text
                    ┌─────────────┐
                    │    User     │
                    └──────┬──────┘
                           │
                           ▼
                 ┌─────────────────┐
                 │ Decision Engine │
                 └────────┬────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
 Appointment Agent   Pharmacy Agent   Report Agent

        ▼                 ▼                 ▼
 Emergency Agent    Clarifier Agent  Direct Answer Agent
```

The **Decision Engine** acts as the central router, selecting the most appropriate agent based on user intent and managing the overall workflow.

---
Agents

## Decision Engine

The Decision Engine is responsible for:

* Intent Classification
* Agent Selection
* Workflow Orchestration
* State Management

---

## Appointment Agent

Helps users discover healthcare providers.

### Capabilities

* Extract doctor specialty
* Extract location
* Detect missing information
* Request clarification when necessary
* Search doctors and hospitals using Tavily
* Recommend healthcare providers

### Example

**User**

```text
I need a cardiologist in Colombo
```

**Response**

```text
Recommended Cardiologists
Recommended Hospitals
Available Healthcare Providers
```

---

## Clarifier Agent

Collects missing information required by other agents.

Examples:

* Doctor specialty
* Location
* Appointment preferences

---

## Pharmacy Agent

Uses a local pharmacy database for medicine retrieval.

### Database

```text
pharmacy_mock.db
```

### Capabilities

* Medicine lookup
* Alternative medicine suggestions
* Availability checking
* Fast local retrieval

---

## Report Agent

Analyzes medical reports and healthcare documents.

### Capabilities

* Medical report summarization
* Key finding extraction
* Clinical insight generation
* Patient-friendly explanations

---

## Emergency Agent

Detects healthcare emergencies and prioritizes patient safety.

### Detects

* Chest pain
* Difficulty breathing
* Stroke symptoms
* Severe bleeding
* Other urgent medical conditions

### Response

Provides immediate emergency recommendations and escalation guidance.

---

## Direct Answer Agent

Handles general healthcare questions that do not require specialized workflows.

---

Local RAG Pipeline

MedoraAI uses a fully local Retrieval-Augmented Generation (RAG) architecture.

## Embedding Model

### BGE-M3

Used for generating dense vector embeddings.

Benefits:

* High-quality retrieval
* Multi-lingual support
* Efficient semantic search

---

## Vector Database

### Qdrant

Runs locally for privacy-preserving document retrieval.

Benefits:

* Low latency
* Local storage
* No external vector database dependency

---

## Re-Ranker

### Cross-Encoder Re-Ranker

Improves retrieval quality by re-ranking candidate documents before passing them to the LLM.

---

## RAG Workflow

```text
User Query
    │
    ▼
BGE-M3 Embedding
    │
    ▼
Qdrant Vector Search
    │
    ▼
Top-K Documents
    │
    ▼
Cross-Encoder Re-Ranker
    │
    ▼
Relevant Context
    │
    ▼
LLM Response
```

This pipeline significantly improves response accuracy while reducing hallucinations.

---

Data Sources

## Medical Knowledge Base

Location:

```text
app/rag/data/pdfs/
```

Current Sample Documents:

```text
sample_clinical_report_01.pdf
sample_clinical_report_02.pdf
```

---

## Local Pharmacy Database

```text
pharmacy_mock.db
```

Used by the Pharmacy Agent for medicine lookup and recommendations.

---

## Web Search

Powered by **Tavily Search API**

Used for:

* Doctor discovery
* Hospital search
* Healthcare provider recommendations

---

#Technology Stack

## Backend

* Python
* AsyncIO
* LangGraph

## LLM

* Gemini 2.5 Flash

## Retrieval

* BGE-M3
* Qdrant
* Cross-Encoder Re-Ranker

## Search

* Tavily

## Memory

* Mem0

## Frontend

* Chainlit

---

#Project Structure

```text
app/
├── agents/
├── config/
├── graphs/
├── llms/
├── memory/
├── nodes/
├── rag/
├── tools/
└── main.py

frontend/
├── app.py
├── chainlit.md
└── public/

qdrant/
├── storage/
└── snapshots/

pharmacy_mock.db
README.md
requirements.txt
```

---

#Installation

## 1. Clone Repository

```bash
git clone <repository-url>
cd AGENTRIX26-TEAM32-AGENTleMEN
```

## 2. Create Virtual Environment

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key

QDRANT_URL=http://localhost
QDRANT_PORT=6333
```

---

## 5. Start Qdrant

```bash
docker run -p 6333:6333 \
-v $(pwd)/qdrant:/qdrant/storage \
qdrant/qdrant
```

Verify:

```bash
curl http://localhost:6333
```

---

## 6. Ingest Medical Documents

Place PDFs inside:

```text
app/rag/data/pdfs/
```

Run:

```bash
python -m app.rag.ingestion.ingestion
```

This process:

* Loads PDFs
* Chunks documents
* Creates BGE-M3 embeddings
* Stores vectors in Qdrant

---

## 7. Seed Pharmacy Database

```bash
python -m app.tools.seed_pharmacy_db
```

Creates:

```text
pharmacy_mock.db
```

---

## 8. Run Backend

```bash
python -m app.main
```

---

## 9. Run Frontend

```bash
chainlit run frontend/app.py -w
```

Application:

```text
http://localhost:8000
```

---

#Example Queries

### Appointment Agent

```text
I need a cardiologist in Colombo
```

### Pharmacy Agent

```text
Do you have Paracetamol?
```

### Emergency Agent

```text
I have chest pain and difficulty breathing
```

### Report Agent

```text
Summarize this medical report
```

---

#Future Improvements

* Appointment Booking Integration
* Hospital Scheduling APIs
* Expanded Medical Knowledge Base
* Enhanced Patient Memory
* Multi-Language Support
* Electronic Medical Record (EMR) Integration

---

#Team

**AGENTRIX26 – TEAM32 – AGENTleMEN**

Built for the Agentrix Hackathon
