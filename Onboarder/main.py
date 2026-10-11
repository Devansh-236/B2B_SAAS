#!/usr/bin/env python3
"""
FastAPI Server for Onboarder System

A RESTful API server that manages employee onboarding processes with proper state management
and context sharing between agents.
"""

import os
import secrets
import logging
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import uvicorn

from onboarder.database_manager import DatabaseManager, DuplicateRecordError
from onboarder.agent_orchestrator import AgentOrchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration (see env.example)
HOST = os.getenv("ONBOARDER_HOST", "127.0.0.1")
PORT = int(os.getenv("ONBOARDER_PORT", "8050"))
RELOAD = os.getenv("ONBOARDER_RELOAD", "false").lower() in ("1", "true", "yes")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ONBOARDER_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8050,http://127.0.0.1:8050"
    ).split(",")
    if origin.strip()
]

VALID_PHASES = ["PRE_BOARDING", "DAY1_SETUP", "INTEGRATION"]

# Initialize database manager
db_manager = DatabaseManager()
agent_orchestrator = AgentOrchestrator(db_manager)


async def require_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Require the X-API-Key header when ONBOARDER_API_KEY is set.
    
    If ONBOARDER_API_KEY is not set, the API is open (intended for local development only).
    """
    expected_key = os.getenv("ONBOARDER_API_KEY")
    if not expected_key:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key.encode(), expected_key.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


async def _run_onboarding_process_safe(employee_id: str, onboarding_id: str, run_id: str):
    """
    Safely run the onboarding process with proper error handling and timeouts.
    """
    try:
        logger.info(f"Starting safe onboarding process for {employee_id}")
        await agent_orchestrator.start_onboarding_process(employee_id, onboarding_id, run_id)
        logger.info(f"Onboarding process finished for {employee_id}")
    except Exception as e:
        logger.error(f"Onboarding process failed for {employee_id}: {e}")
        # Update status to failed (only if this run still owns the record)
        try:
            if not db_manager.update_onboarding_record(onboarding_id, {
                'status': 'FAILED',
                'errors': [str(e)],
                'end_time': datetime.now().isoformat()
            }, expected_status='IN_PROGRESS', run_id=run_id):
                logger.error(f"Could not record failure for {employee_id}")
        except Exception as update_error:
            logger.error(f"Failed to update failed status for {employee_id}: {update_error}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Onboarder API Server...")
    yield
    logger.info("Shutting down Onboarder API Server...")

# Initialize FastAPI app
app = FastAPI(
    title="Onboarder API",
    description="Employee Onboarding Management System",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware (explicit origins from ONBOARDER_CORS_ORIGINS; no cookies/credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Pydantic models for request/response
class NewHireData(BaseModel):
    full_name: str = Field(..., description="Full name of the new hire")
    personal_email: str = Field(..., description="Personal email address")
    job_title: str = Field(..., description="Job title")
    manager_name: str = Field(..., description="Manager's name")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    employee_id: Optional[str] = Field(None, description="Optional employee ID")
    
    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v):
        """Validate that start_date is in YYYY-MM-DD format."""
        try:
            # Try to parse the date to ensure it's valid
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('start_date must be in YYYY-MM-DD format (e.g., 2024-01-15)')

class OnboardingStatus(BaseModel):
    employee_id: str
    status: str
    current_phase: str
    completed_phases: List[str]
    start_time: Optional[str]
    last_updated: str
    process_log: List[str]

class PhaseUpdate(BaseModel):
    phase: Literal["PRE_BOARDING", "DAY1_SETUP", "INTEGRATION"] = Field(
        ..., description="Phase to update (PRE_BOARDING, DAY1_SETUP, INTEGRATION)"
    )
    status: Literal["PENDING", "COMPLETED", "FAILED"] = Field(
        ..., description="New phase status (PENDING, COMPLETED, FAILED). Use the start or execute endpoints to run a phase."
    )

class OnboardingResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# API Routes

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Onboarder API Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "create_onboarding": "/onboarding",
            "get_status": "/onboarding/{employee_id}/status",
            "start_onboarding": "/onboarding/{employee_id}/start",
            "reset_onboarding": "/onboarding/{employee_id}/reset",
            "update_phase": "/onboarding/{employee_id}/phase",
            "execute_phase": "/onboarding/{employee_id}/phase/{phase}/execute",
            "get_context": "/onboarding/{employee_id}/context",
            "list_onboardings": "/onboardings",
            "stats": "/stats"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/onboarding", response_model=OnboardingResponse, dependencies=[Depends(require_api_key)])
async def create_onboarding(new_hire_data: NewHireData):
    """
    Create a new onboarding record for an employee.
    
    This endpoint creates an onboarding record but doesn't start the process.
    Use the /onboarding/{employee_id}/start endpoint to begin onboarding.
    """
    try:
        # Validate required fields
        if not all([new_hire_data.full_name, new_hire_data.personal_email, 
                   new_hire_data.job_title, new_hire_data.manager_name, new_hire_data.start_date]):
            raise HTTPException(status_code=400, detail="All required fields must be provided")
        
        # Create onboarding record
        try:
            onboarding_id = db_manager.create_onboarding_record(
                new_hire_data.model_dump(),
                new_hire_data.employee_id
            )
        except DuplicateRecordError as e:
            raise HTTPException(status_code=409, detail=str(e))
        
        if not onboarding_id:
            raise HTTPException(status_code=500, detail="Failed to create onboarding record")
        
        # Get the created record
        record = db_manager.get_onboarding_record(onboarding_id)
        
        return OnboardingResponse(
            success=True,
            message="Onboarding record created successfully",
            data={
                "employee_id": record["employee_id"],
                "onboarding_id": onboarding_id,
                "status": record["status"],
                "current_phase": record["current_phase"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating onboarding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/onboarding/{employee_id}/status", response_model=OnboardingStatus,
         dependencies=[Depends(require_api_key)])
async def get_onboarding_status(employee_id: str):
    """
    Get the current status of an employee's onboarding process.
    """
    try:
        record = db_manager.get_onboarding_by_employee_id(employee_id)
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        return OnboardingStatus(
            employee_id=record["employee_id"],
            status=record["status"],
            current_phase=record["current_phase"],
            completed_phases=record["completed_phases"],
            start_time=record["start_time"],
            last_updated=record["last_updated"],
            process_log=record["process_log"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting onboarding status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/onboarding/{employee_id}/start", response_model=OnboardingResponse,
          dependencies=[Depends(require_api_key)])
async def start_onboarding(employee_id: str, background_tasks: BackgroundTasks):
    """
    Start the onboarding process for an employee.
    
    This will begin the onboarding process from the current phase.
    The process runs in the background and can be monitored via the status endpoint.
    """
    try:
        record = db_manager.get_onboarding_by_employee_id(employee_id)
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        # Atomically move the record to IN_PROGRESS (fails if already running or completed)
        run_id = db_manager.claim_onboarding(record["onboarding_id"])
        if not run_id:
            current = db_manager.get_onboarding_record(record["onboarding_id"]) or record
            if current["status"] == "IN_PROGRESS":
                raise HTTPException(
                    status_code=409,
                    detail="Onboarding already in progress. If it is stuck, POST /onboarding/{employee_id}/reset first."
                )
            if current["status"] == "COMPLETED":
                raise HTTPException(status_code=409, detail="Onboarding already completed")
            raise HTTPException(status_code=500, detail="Failed to start onboarding")
        
        # Start onboarding in background with proper error handling
        background_tasks.add_task(
            _run_onboarding_process_safe,
            employee_id,
            record["onboarding_id"],
            run_id
        )
        
        return OnboardingResponse(
            success=True,
            message="Onboarding process started",
            data={
                "employee_id": employee_id,
                "onboarding_id": record["onboarding_id"],
                "current_phase": record["current_phase"],
                "status": "IN_PROGRESS"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting onboarding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/onboarding/{employee_id}/phase", response_model=OnboardingResponse,
          dependencies=[Depends(require_api_key)])
async def update_onboarding_phase(employee_id: str, phase_update: PhaseUpdate):
    """
    Manually update the phase status for an employee's onboarding.
    
    This allows manual control over the onboarding process phases. It only records
    state; it does not run any agents. Not allowed while a run is IN_PROGRESS.
    """
    try:
        record = db_manager.get_onboarding_by_employee_id(employee_id)
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        if record["status"] == "IN_PROGRESS":
            raise HTTPException(
                status_code=409,
                detail="Cannot update phases while onboarding is in progress"
            )
        
        # Update the phase
        completed_phases = list(record["completed_phases"] or [])
        if phase_update.status == "COMPLETED":
            if phase_update.phase not in completed_phases:
                completed_phases.append(phase_update.phase)
        elif phase_update.phase in completed_phases:
            # PENDING or FAILED: the phase is no longer complete
            completed_phases.remove(phase_update.phase)
        
        # Determine next phase
        next_phase = agent_orchestrator.get_first_incomplete_phase(completed_phases)
        
        if next_phase == "COMPLETED":
            new_status = "COMPLETED"
        elif phase_update.status == "FAILED":
            new_status = "FAILED"
        else:
            # Nothing is running; the onboarding can be (re)started from next_phase
            new_status = "PENDING"
        
        updates = {
            "current_phase": next_phase,
            "completed_phases": completed_phases,
            "status": new_status
        }
        if new_status == "COMPLETED":
            updates["end_time"] = datetime.now().isoformat()
        
        # Conditional on the status we checked, so a run started meanwhile is not overwritten
        if not db_manager.update_onboarding_record(
            record["onboarding_id"], updates, expected_status=record["status"]
        ):
            raise HTTPException(status_code=409, detail="Onboarding record changed; please retry")
        
        return OnboardingResponse(
            success=True,
            message=f"Phase {phase_update.phase} updated to {phase_update.status}",
            data={
                "employee_id": employee_id,
                "status": new_status,
                "current_phase": next_phase,
                "completed_phases": completed_phases
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/onboarding/{employee_id}/reset", response_model=OnboardingResponse,
          dependencies=[Depends(require_api_key)])
async def reset_onboarding(employee_id: str):
    """
    Reset a stuck or failed onboarding back to PENDING so it can be started again.
    
    Completed phases are kept, so a restart resumes from the first incomplete phase.
    Any phase still running from the previous run can no longer update the record.
    """
    try:
        record = db_manager.get_onboarding_by_employee_id(employee_id)
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        if record["status"] == "COMPLETED":
            raise HTTPException(status_code=409, detail="Onboarding already completed")
        
        completed_phases = record["completed_phases"] or []
        errors = list(record.get("errors") or [])
        errors.append(f"Reset from {record['status']} at {datetime.now().isoformat()}")
        next_phase = agent_orchestrator.get_first_incomplete_phase(completed_phases)
        
        # Clearing run_id invalidates writes from any still-running phase of the old run
        if not db_manager.update_onboarding_record(record["onboarding_id"], {
            "status": "PENDING",
            "current_phase": next_phase,
            "run_id": None,
            "errors": errors
        }, expected_status=record["status"]):
            raise HTTPException(status_code=409, detail="Onboarding record changed; please retry")
        
        return OnboardingResponse(
            success=True,
            message="Onboarding reset to PENDING",
            data={
                "employee_id": employee_id,
                "status": "PENDING",
                "current_phase": next_phase,
                "completed_phases": completed_phases
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting onboarding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/onboarding/{employee_id}/context", dependencies=[Depends(require_api_key)])
async def get_onboarding_context(employee_id: str):
    """
    Get the onboarding context (markdown templates) for an employee.
    
    This returns the relevant context information for the current phase.
    """
    try:
        record = db_manager.get_onboarding_by_employee_id(employee_id)
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        context = record.get("onboarding_context", {})
        current_phase = record["current_phase"]
        
        # Return relevant context for current phase
        phase_context = context.get(current_phase, {})
        
        return {
            "employee_id": employee_id,
            "current_phase": current_phase,
            "context": phase_context,
            "all_context": context
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/onboardings", dependencies=[Depends(require_api_key)])
async def list_onboardings(status: Optional[str] = None):
    """
    List all onboarding records, optionally filtered by status.
    
    Status options: PENDING, IN_PROGRESS, COMPLETED, FAILED
    """
    try:
        if status:
            records = db_manager.get_onboarding_records_by_status(status)
        else:
            records = db_manager.get_all_onboarding_records()
        
        return {
            "total": len(records),
            "onboardings": [
                {
                    "employee_id": record["employee_id"],
                    "onboarding_id": record["onboarding_id"],
                    "status": record["status"],
                    "current_phase": record["current_phase"],
                    "start_time": record["start_time"],
                    "last_updated": record["last_updated"],
                    "new_hire_data": {
                        "full_name": (record["new_hire_data"] or {}).get("full_name"),
                        "job_title": (record["new_hire_data"] or {}).get("job_title")
                    }
                }
                for record in records
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing onboardings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/onboarding/{employee_id}/phase/{phase}/execute", response_model=OnboardingResponse,
          dependencies=[Depends(require_api_key)])
async def execute_phase(employee_id: str, phase: str, background_tasks: BackgroundTasks):
    """
    Execute a specific phase for an employee's onboarding.
    
    This triggers the agent for the specified phase to run.
    """
    try:
        if phase not in VALID_PHASES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase. Must be one of: {VALID_PHASES}"
            )
        
        record = db_manager.get_onboarding_by_employee_id(employee_id)
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        # Atomically claim the record so this cannot run alongside another run
        run_id = db_manager.claim_onboarding(record["onboarding_id"], blocked_statuses=("IN_PROGRESS",))
        if not run_id:
            raise HTTPException(status_code=409, detail="Onboarding already in progress")
        
        # Execute phase in background
        background_tasks.add_task(
            agent_orchestrator.run_single_phase,
            employee_id,
            record["onboarding_id"],
            phase,
            run_id
        )
        
        return OnboardingResponse(
            success=True,
            message=f"Phase {phase} execution started",
            data={
                "employee_id": employee_id,
                "phase": phase,
                "status": "EXECUTING"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", dependencies=[Depends(require_api_key)])
async def get_onboarding_stats():
    """Get summary statistics for all onboarding processes."""
    try:
        summary = db_manager.get_onboarding_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the server (configure with ONBOARDER_HOST, ONBOARDER_PORT, ONBOARDER_RELOAD)
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level="info"
    )
