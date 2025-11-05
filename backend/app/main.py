from fastapi import FastAPI, Request, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import shutil, os, asyncio, json
from agents.orchestrator import orchestrate_question

# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message to send to the AI agent")

class ChatResponse(BaseModel):
    """Response model for streaming chunks."""
    chunk: str = Field(..., description="Streaming chunk of the AI response")

class UploadResponse(BaseModel):
    """Response model for PDF upload."""
    status: str = Field(..., description="Upload status")
    filename: str = Field(..., description="Name of uploaded file")
    message: str = Field(..., description="Additional message about the upload")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")

UPLOAD_DIR = "./uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="Customer AI - Backend",
    description="Multi-agent customer service AI with LangGraph orchestrator",
    version="1.0.0"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Orchestrator is stateless, no initialization needed

async def stream_agent_answer(user_msg: str):
    """Stream answer from orchestrator agent."""
    try:
        # Use orchestrator to route and get answer
        answer = orchestrate_question(user_msg)
        
        if not answer:
            answer = "No answer was generated. Please ensure documents are uploaded and try again."
        
        # Stream the answer in chunks
        for i in range(0, len(answer), 150):
            await asyncio.sleep(0.02)
            yield f"data: {json.dumps({'chunk': answer[i:i+150]})}\n\n"
        yield f"data: {json.dumps({'chunk': '[DONE]'})}\n\n"
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}. Please ensure documents are uploaded and OPENAI_API_KEY is set."
        yield f"data: {json.dumps({'chunk': error_msg})}\n\n"
        yield f"data: {json.dumps({'chunk': '[DONE]'})}\n\n"

@app.post("/chat", response_model=None)
async def chat(chat_request: ChatRequest):
    """
    Chat endpoint that routes queries to appropriate specialized agents.
    
    - **message**: User's question or message
    - Returns: Streaming SSE response with AI-generated answer
    """
    return StreamingResponse(
        stream_agent_answer(chat_request.message),
        media_type="text/event-stream"
    )

# ---- PDF upload endpoint with ingestion ----
def ingest_pdf_background(pdf_path: str):
    """Background task to ingest PDF into ChromaDB."""
    try:
        import sys
        import importlib.util
        # Import ingest_pdf module
        spec = importlib.util.spec_from_file_location("ingest_pdf", os.path.join(os.path.dirname(__file__), "ingest_pdf.py"))
        ingest_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ingest_module)
        
        metadata = {"source": pdf_path, "filename": os.path.basename(pdf_path)}
        ingest_module.ingest_pdf_file(pdf_path, metadata=metadata)
        print(f"Successfully ingested {pdf_path}")
        # Note: Orchestrator is stateless, no reset needed
    except Exception as e:
        print(f"Error ingesting {pdf_path}: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Customer AI Backend"}

@app.post("/upload-pdf", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload and ingest PDF document into ChromaDB vector database.
    
    - **file**: PDF file to upload and process
    - Returns: Upload status and filename
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    # Save uploaded file
    dest = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Trigger ingestion in background
    if background_tasks:
        background_tasks.add_task(ingest_pdf_background, dest)
    else:
        # Fallback: ingest synchronously if background_tasks not available
        ingest_pdf_background(dest)
    
    return UploadResponse(
        status="uploaded",
        filename=file.filename,
        message="PDF will be processed and indexed shortly"
    )

