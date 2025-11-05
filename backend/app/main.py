from fastapi import FastAPI, Request, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
import shutil, os, asyncio, json
from agents.retrieval_agent import make_conversational_agent

UPLOAD_DIR = "./uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Customer AI - Backend")

# Initialize the conversational agent
agent_chain = make_conversational_agent()

async def stream_agent_answer(user_msg: str):
    result = agent_chain({"question": user_msg})
    answer = result.get("answer","")
    for i in range(0, len(answer), 150):
        await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'chunk': answer[i:i+150]})}\n\n"
    yield f"data: {json.dumps({'chunk':'[DONE]'})}\n\n"

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_msg = body.get("message","")
    return StreamingResponse(stream_agent_answer(user_msg), media_type="text/event-stream")

# ---- PDF upload endpoint (synchronous ingest hook) ----
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    if not file.filename.lower().endswith(".pdf"):
        return {"error": "only pdf allowed"}
    dest = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # placeholder: triggered ingestion (we'll add ingest script)
    return {"status": "uploaded", "filename": file.filename}

