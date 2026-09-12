# MedoraAI

MedoraAI is an agentic medical assistant that helps users navigate common healthcare tasks through a Chainlit chat interface. The current system is built around one central agent orchestrator that can call multiple healthcare tools for doctor discovery, appointment schedule lookup, hospitals and channeling centers, pharmacy search, emergency triage, medical document retrieval, and long-term memory.

> MedoraAI is not a replacement for a doctor, pharmacist, emergency service, or licensed medical professional. It is designed to provide helpful guidance, route users to relevant healthcare resources, and escalate urgent situations.

## What It Can Do

- Find doctors by specialty, city, hospital, language, gender, fee range, rating, experience, and availability.
- Search appointment schedules and available doctor slots from the local schedule database.
- Find hospitals and channeling centers, including emergency-capable hospitals.
- Search pharmacies and medicine-related availability data from local pharmacy records.
- Triage urgent symptoms and provide basic emergency guidance.
- Search uploaded medical documents using the local RAG pipeline.
- Remember useful long-term health context with Mem0 and maintain a compact conversation summary.
- Provide a Chainlit frontend with health profile/sidebar support and PDF report upload workflow.

## Architecture

```text
User
  |
  v
Chainlit Frontend
  |
  v
main.run_agent()
  |
  +--> Load long-term memory and conversation summary
  |
  v
Medora Agent Orchestrator
  |
  +--> Doctor Tools
  +--> Schedule Tools
  +--> Hospital / Channeling Center Tools
  +--> Pharmacy Tools
  +--> Emergency Tools
  +--> RAG Document Search Tool
  |
  v
Final healthcare response
  |
  v
Save memory and update conversation summary
```

The orchestrator lives in `app/orchestrator/agent.py`. It uses LangGraph's ReAct agent pattern with a single shared medical system prompt and a tool list covering the healthcare domains in the app.

## Main Components

### Agent Orchestrator

The central Medora agent decides which tool or sequence of tools should be used for each user request. It handles healthcare intent, appointment and schedule questions, medicine and pharmacy lookup, document search, emergency assessment, and safe final response generation.

Key files:

- `app/orchestrator/agent.py`
- `app/orchestrator/prompts.py`
- `app/orchestrator/state.py`

### Tools

Tools are the domain actions available to the orchestrator:

- `app/tools/doctor_tools.py` - doctor search, doctor details, available slots, doctor availability.
- `app/tools/schedule_tools.py` - available schedule search, schedule details, doctor schedules.
- `app/tools/hospital_tools.py` - hospitals, channeling centers, emergency hospitals.
- `app/tools/pharmacy_tools.py` - pharmacy search and pharmacy details.
- `app/tools/emergency_tools.py` - symptom triage, emergency assessment, emergency protocols.
- `app/tools/rag_tools.py` - semantic search over uploaded medical documents.

### Local Data

The app uses JSON datasets for local healthcare information:

- `app/database/doctors.json`
- `app/database/schedules.json`
- `app/database/hospitals.json`
- `app/database/channeling_centers.json`
- `app/database/pharmacies.json`

### RAG System

MedoraAI includes a local Retrieval-Augmented Generation pipeline for uploaded medical reports and healthcare documents.

- Embedding model: `BAAI/bge-m3`
- Vector database: Qdrant
- Reranking: FlagEmbedding / reranker flow
- Collection name: `documents_bge_m3_1024`

Key files:

- `app/rag/ingestion/`
- `app/rag/retrieval/`
- `app/rag/qdrant_db.py`
- `app/config/embeddings.py`

### Memory

The app uses Mem0 with Qdrant-backed storage for long-term memory. It also keeps a short recent chat window and summarizes older conversation context so medical discussions remain coherent without sending the full history every time.

Key files:

- `app/memory/mem0_service.py`
- `app/memory/conversation.py`
- `app/nodes/memory_node.py`
- `app/nodes/memory_save_node.py`

### Chainlit Frontend

The UI is built with Chainlit. Users can chat with the medical agent, maintain a health profile, and upload medical report PDFs for RAG ingestion and later question answering.

Key files:

- `app/ui/chainlit_app.py`
- `app/ui/home.py`
- `app/ui/health_profile_sidebar.py`
- `app/ui/report_upload_workflow.py`
- `public/custom.css`


## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root.

```env
# Choose one: lmstudio, gemini, groq
LLM_PROVIDER=lmstudio

# LM Studio
LMSTUDIO_BASE_URL=http://127.0.0.1:1234
LMSTUDIO_API_KEY=lm-studio
LMSTUDIO_MODEL=your-local-model-name

# Gemini
GEMINI_API_KEY=
GEMINI_MODEL=Gemini 2.5 Flash Lite

# Groq
GROQ_API_KEY=
GROQ_MODEL=

# Required by settings
GEOAPIFY_API_KEY=your-geoapify-key

# Optional
TAVILY_API_KEY=
QDRANT_URL=localhost
QDRANT_PORT=6333
REDIS_HOST=
REDIS_PORT=
LANGSMITH_API_KEY=
```

### 4. Start Qdrant

Mem0 and the RAG system expect Qdrant to be available. A common local option is Docker:

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 5. Run the Chainlit app

```bash
chainlit run app/ui/chainlit_app.py
```

Then open the local Chainlit URL shown in the terminal, usually:

```text
http://localhost:8000
```

## Example Prompts

```text
Find me a cardiologist in Colombo.
```

```text
Are there any dermatologists available tomorrow?
```

```text
Find a pharmacy near Kandy.
```

```text
I have chest pain and shortness of breath. What should I do?
```

```text
Can you explain my uploaded blood report?
```

## Medical Safety

MedoraAI is built to prioritize safety:

- It should escalate possible emergencies immediately.
- It should avoid inventing doctors, hospitals, schedules, medicine facts, or prices.
- It should use local tool results where available.
- It should communicate uncertainty clearly.
- It should recommend professional medical care when appropriate.

For emergencies, users should contact local emergency services or go to the nearest emergency department immediately.

## Development Notes

- `main.py` creates the initial state and runs each user turn.
- Memory is loaded before the agent runs and saved after the response.
- Uploaded reports are processed through the Chainlit report upload workflow and indexed into Qdrant.
- The local healthcare datasets are currently JSON files under `app/database/`.
- The current implementation uses one orchestrator agent with many tools, rather than separate standalone agents.
