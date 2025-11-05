# Customer Service Multi-Agent AI (student starter)
Project scaffold for the customer service AI demo.

## Overview

A full-stack customer service AI application with:
- **Backend**: FastAPI with LangChain agents and ChromaDB vector database
- **Frontend**: Next.js chat interface with real-time streaming
- **RAG**: Retrieval-Augmented Generation for document-based Q&A

## Features

- 📄 PDF upload and automatic ingestion into vector database
- 💬 Real-time streaming chat interface
- 🔍 Multi-agent system with intelligent routing
- 🤖 **Orchestrator Agent**: Routes queries to specialized agents using LangGraph
- 💰 **Billing Support Agent**: Hybrid RAG/CAG for pricing and account questions
- 🔧 **Technical Support Agent**: Pure RAG for technical troubleshooting
- 📜 **Policy & Compliance Agent**: Pure CAG for Terms of Service and Privacy Policy
- 🧠 Conversational memory for context-aware responses
- ☁️ **AWS Bedrock Integration**: Cost-effective routing with Claude Haiku

## Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API key (required)
- AWS Account with Bedrock access (optional, but recommended for cost-effective routing)

## Setup

### 1. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-api-key-here"
export CHROMA_PERSIST_DIR="./chroma_db"  # Optional, defaults to ./chroma_db

# AWS Bedrock for cost-effective routing (RECOMMENDED)
# The orchestrator uses Bedrock Claude Haiku for routing, which is more cost-effective than OpenAI
export AWS_REGION="us-east-1"  # Your AWS region (e.g., us-east-1, us-west-2)
export USE_BEDROCK="true"  # Set to "true" to enable Bedrock (defaults to OpenAI if not set)
# Note: Ensure AWS credentials are configured (via ~/.aws/credentials or environment variables)
```

### 2. Frontend Setup

```bash
cd frontend
npm install

# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
source .venv/bin/activate
cd backend/app
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Usage

1. **Upload PDFs**: Use the sidebar to upload PDF documents
2. **Wait for Processing**: PDFs are automatically processed and indexed into ChromaDB
3. **Ask Questions**: Type questions in the chat interface to get answers based on your documents

## Project Structure

```
customer-ai/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py        # LangGraph orchestrator (routes queries)
│   │   │   ├── billing_agent.py       # Hybrid RAG/CAG for billing
│   │   │   ├── technical_agent.py      # Pure RAG for technical support
│   │   │   ├── policy_agent.py        # Pure CAG for policy/compliance
│   │   │   └── retrieval_agent.py     # General RAG agent (fallback)
│   │   ├── ingest_pdf.py              # PDF ingestion script
│   │   ├── main.py                    # FastAPI application
│   │   └── generate_mock_pdfs.py      # Mock PDF generator
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   │   └── PDFUpload.tsx
│   │   ├── page.tsx                   # Main chat interface
│   │   └── layout.tsx
│   └── package.json
├── .gitignore
└── README.md
```

## Architecture

### Multi-Agent System

The application uses a **LangGraph-based orchestrator** that intelligently routes user queries to specialized agents:

1. **Orchestrator Agent** (Supervisor)
   - Uses AWS Bedrock Claude Haiku (or OpenAI GPT-3.5) for cost-effective routing
   - Analyzes queries and routes to appropriate worker agent
   - Maintains conversation state using LangGraph checkpoints

2. **Billing Support Agent** (Hybrid RAG/CAG)
   - **RAG**: Retrieves relevant billing documents from vector database
   - **CAG**: Caches static policy information after first retrieval
   - Best for: Fees, pricing, invoices, account questions

3. **Technical Support Agent** (Pure RAG)
   - Always retrieves from dynamic knowledge base
   - No caching - always gets latest information
   - Best for: API issues, login problems, technical troubleshooting

4. **Policy & Compliance Agent** (Pure CAG)
   - Uses pre-loaded static context (Terms of Service, Privacy Policy)
   - No vector retrieval - fast, consistent answers
   - Best for: Legal questions, compliance, data privacy

### Retrieval Strategies

- **RAG (Retrieval-Augmented Generation)**: Retrieves relevant chunks from vector database
- **CAG (Context-Augmented Generation)**: Uses static context without retrieval
- **Hybrid RAG/CAG**: Combines both - RAG for initial query, CAG for cached context

## Environment Variables

Copy the example environment file and configure:

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Frontend  
cp frontend/.env.example frontend/.env.local  # If exists
# Or create frontend/.env.local with: NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development

### Generate Mock PDFs (for testing)

```bash
cd backend/app
python generate_mock_pdfs.py
# PDFs will be created in backend/app/mock_docs/
```

### Manual PDF Ingestion

```bash
cd backend/app
python ingest_pdf.py path/to/your/document.pdf
```

## API Endpoints

### `POST /chat`
Send a message to the AI agent and receive a streaming response.

**Request Body:**
```json
{
  "message": "What are the account fees?"
}
```

**Response:** Server-Sent Events (SSE) stream with chunks:
```
data: {"chunk": "Based on the account..."}

data: {"chunk": "[DONE]"}
```

**Example:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the account fees?"}'
```

### `POST /upload-pdf`
Upload and ingest a PDF document into ChromaDB.

**Request:** Multipart form data with `file` field

**Response:**
```json
{
  "status": "uploaded",
  "filename": "document.pdf",
  "message": "PDF will be processed and indexed shortly"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/upload-pdf \
  -F "file=@document.pdf"
```

### API Documentation
Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

## Example Queries

Try these queries to test different agents:

- **Billing**: "What are the account fees?" or "How much does a Pro subscription cost?"
- **Technical**: "I can't log in, what should I do?" or "How do I use the API?"
- **Policy**: "What is your privacy policy?" or "What are the terms of service?"

## Multi-Provider LLM Strategy

The application implements a strategic multi-LLM approach:

1. **Orchestrator (Routing)**: Uses AWS Bedrock Claude Haiku (cost-effective) or OpenAI GPT-3.5-turbo
   - Purpose: Classify queries and route to appropriate agent
   - Why Bedrock: Lower cost for simple classification tasks

2. **Worker Agents (Response Generation)**: Uses OpenAI GPT-3.5-turbo
   - Purpose: Generate high-quality responses with RAG/CAG
   - Why OpenAI: Better performance for complex reasoning

**Cost Optimization**: By using Bedrock for routing (~$0.25 per 1M tokens) vs OpenAI GPT-3.5 (~$0.50 per 1M tokens), we reduce costs by ~50% for routing operations while maintaining quality for response generation.

## Troubleshooting

### Backend Issues

**Error: "Agent not initialized"**
- Ensure `OPENAI_API_KEY` is set in environment variables
- Check that ChromaDB has documents ingested (upload PDFs first)

**Error: "Could not initialize agent"**
- Verify ChromaDB collection exists: Check `./chroma_db` directory
- Ensure PDFs have been uploaded and processed
- Check logs for specific error messages

**Error: "Bedrock not available"**
- Verify AWS credentials are configured (`aws configure` or environment variables)
- Check that Bedrock is enabled in your AWS region
- Ensure `USE_BEDROCK=true` is set (falls back to OpenAI if not available)

**PDF Ingestion Fails**
- Ensure PDF file is not corrupted
- Check file permissions on `uploaded_pdfs/` directory
- Verify OpenAI API key is valid (needed for embeddings)

### Frontend Issues

**Cannot connect to backend**
- Verify backend is running on `http://localhost:8000`
- Check CORS settings if accessing from different origin
- Ensure `NEXT_PUBLIC_API_URL` is set correctly in `.env.local`

**Streaming not working**
- Check browser console for errors
- Verify backend is sending SSE responses correctly
- Ensure network isn't blocking Server-Sent Events

**Upload fails**
- Check file size limits (if any)
- Verify backend `/upload-pdf` endpoint is accessible
- Check browser console for error messages

### Common Issues

**ChromaDB Collection Not Found**
- Upload PDFs first to create collections
- Collections are auto-created: `billing_docs`, `tech_docs`, `pdf_docs`
- Run manual ingestion: `python backend/app/ingest_pdf.py path/to/file.pdf`

**Agent Routing Issues**
- Check that query contains relevant keywords (billing, technical, policy)
- Review orchestrator logs for routing decisions
- Test with explicit agent-specific queries

## Deployment

### Backend Deployment

For production deployment, consider:
- Use a production ASGI server: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`
- Set up proper environment variables
- Configure persistent ChromaDB storage
- Enable logging and monitoring

### Frontend Deployment

For production:
- Build: `npm run build`
- Start: `npm start`
- Or deploy to Vercel/Netlify with environment variables configured

## Development

### Testing Agents Individually

You can test agents directly:

```python
# Test billing agent
from agents.billing_agent import make_billing_agent, answer_with_hybrid_rag_cag
agent = make_billing_agent()
answer = answer_with_hybrid_rag_cag("What are the fees?", agent)

# Test technical agent
from agents.technical_agent import make_technical_agent
agent = make_technical_agent()
result = agent({"question": "How do I use the API?"})

# Test policy agent
from agents.policy_agent import make_policy_agent, answer_with_cag
chain, memory = make_policy_agent()
answer = answer_with_cag("What is your privacy policy?", chain, memory)
```

## License

Student project - educational use only.
