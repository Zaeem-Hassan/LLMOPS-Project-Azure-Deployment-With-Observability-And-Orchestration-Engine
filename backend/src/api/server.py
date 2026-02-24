import uuid
import logging
from pathlib import Path
from fastapi import HTTPException, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel
from typing import List,Optional

from dotenv import load_dotenv
load_dotenv(override=True)

from  backend.src.api.telemetry import setup_telemetry

setup_telemetry()

from backend.src.graph.workflow import app as compliance_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-server")

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title = "Brand Guardian AI API",
    version = "1.0.0"
)

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse(str(FRONTEND_DIR / "templates" / "index.html"))

class AuditRequest(BaseModel):
    video_url : str

class ComplianceIssue(BaseModel):
    category : str
    severity : str
    description : str

class AuditResponse(BaseModel): 
    session_id : str   
    video_id : str
    status : str
    final_report : str
    compliance_results: List[ComplianceIssue]

@app.post("/audit",response_model=AuditResponse)

async def audit_video(requests:AuditRequest):

    session_id = str(uuid.uuid4())
    logger.info(f"Received audit request {session_id}")

    initial_state = {
        "video_url" : requests.video_url,
        "video_id" : f"vid_{session_id[:8]}",
        "compliance_results" : [],
        "errors" : []
    }

    try:
        final_state = compliance_graph.invoke(initial_state)
        return AuditResponse(
            session_id=session_id,
            video_id=final_state.get("video_id"),
            status=final_state.get("final_status"),
            final_report=final_state.get("final_report"),
            compliance_results=final_state.get("compliance_results",[])
        )
    except Exception as e:
        logger.error(f"Audit failed for session {session_id}: {e}")
        raise HTTPException(status_code=500,detail=str(e))


@app.get("/health")

def health_check():
    return {"status":"healthy","service":"Brand Guardian"}