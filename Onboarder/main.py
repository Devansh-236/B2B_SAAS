#!/usr/bin/env python3
"""
FastAPI Server for Onboarder System

A RESTful API server that manages employee onboarding processes with proper state management
and context sharing between agents.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

from onboarder.database_manager import DatabaseManager
from onboarder.agent_orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database manager
db_manager = DatabaseManager()
agent_orchestrator = AgentOrchestrator(db_manager)

async def _run_onboarding_process_safe(employee_id: str, onboarding_id: str):
    """
    Safely run the onboarding process with proper error handling and timeouts.
    """
    try:
        logger.info(f"Starting safe onboarding process for {employee_id}")
        await agent_orchestrator.start_onboarding_process(employee_id, onboarding_id)
        logger.info(f"Onboarding process completed for {employee_id}")
    except Exception as e:
        logger.error(f"Onboarding process failed for {employee_id}: {e}")
        # Update status to failed
        try:
            db_manager.update_onboarding_record(onboarding_id, {
                'status': 'FAILED',
                'errors': [str(e)],
                'end_time': datetime.now().isoformat()
            })
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class NewHireData(BaseModel):
    full_name: str = Field(..., description="Full name of the new hire")
    personal_email: str = Field(..., description="Personal email address")
    job_title: str = Field(..., description="Job title")
    manager_name: str = Field(..., description="Manager's name")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    employee_id: Optional[str] = Field(None, description="Optional employee ID")
    
    @validator('start_date')
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
    phase: str = Field(..., description="Phase to update (PRE_BOARDING, DAY1_SETUP, INTEGRATION)")
    status: str = Field(..., description="New status (PENDING, IN_PROGRESS, COMPLETED, FAILED)")

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
            "update_phase": "/onboarding/{employee_id}/phase",
            "get_context": "/onboarding/{employee_id}/context",
            "list_onboardings": "/onboardings"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/onboarding", response_model=OnboardingResponse)
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
        onboarding_id = db_manager.create_onboarding_record(
            new_hire_data.dict(),
            new_hire_data.employee_id
        )
        
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

@app.get("/onboarding/{employee_id}/status", response_model=OnboardingStatus)
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

@app.post("/onboarding/{employee_id}/start", response_model=OnboardingResponse)
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
        
        if record["status"] == "IN_PROGRESS":
            raise HTTPException(status_code=400, detail="Onboarding already in progress")
        
        if record["status"] == "COMPLETED":
            raise HTTPException(status_code=400, detail="Onboarding already completed")
        
        # Update status to IN_PROGRESS immediately
        db_manager.update_onboarding_record(record["onboarding_id"], {
            "status": "IN_PROGRESS",
            "start_time": datetime.now().isoformat()
        })
        
        # Start onboarding in background with proper error handling
        background_tasks.add_task(
            _run_onboarding_process_safe,
            employee_id,
            record["onboarding_id"]
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

@app.post("/onboarding/{employee_id}/phase", response_model=OnboardingResponse)
async def update_onboarding_phase(employee_id: str, phase_update: PhaseUpdate):
    """
    Manually update the phase status for an employee's onboarding.
    
    This allows manual control over the onboarding process phases.
    """
    try:
        record = db_manager.get_onboarding_by_employee_id(employee_id)
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        # Validate phase
        valid_phases = ["PRE_BOARDING", "DAY1_SETUP", "INTEGRATION"]
        if phase_update.phase not in valid_phases:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid phase. Must be one of: {valid_phases}"
            )
        
        # Update the phase
        completed_phases = record["completed_phases"].copy()
        if phase_update.status == "COMPLETED" and phase_update.phase not in completed_phases:
            completed_phases.append(phase_update.phase)
        
        # Determine next phase
        next_phase = "COMPLETED"
        if "PRE_BOARDING" not in completed_phases:
            next_phase = "PRE_BOARDING"
        elif "DAY1_SETUP" not in completed_phases:
            next_phase = "DAY1_SETUP"
        elif "INTEGRATION" not in completed_phases:
            next_phase = "INTEGRATION"
        
        db_manager.update_onboarding_record(record["onboarding_id"], {
            "current_phase": next_phase,
            "completed_phases": completed_phases,
            "status": "COMPLETED" if next_phase == "COMPLETED" else "IN_PROGRESS"
        })
        
        return OnboardingResponse(
            success=True,
            message=f"Phase {phase_update.phase} updated to {phase_update.status}",
            data={
                "employee_id": employee_id,
                "current_phase": next_phase,
                "completed_phases": completed_phases
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/onboarding/{employee_id}/context")
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

@app.get("/onboardings")
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
                        "full_name": record["new_hire_data"]["full_name"],
                        "job_title": record["new_hire_data"]["job_title"]
                    }
                }
                for record in records
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing onboardings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/onboarding/{employee_id}/phase/{phase}/execute")
async def execute_phase(employee_id: str, phase: str, background_tasks: BackgroundTasks):
    """
    Execute a specific phase for an employee's onboarding.
    
    This triggers the agent for the specified phase to run.
    """
    try:
        record = db_manager.get_onboarding_by_employee_id(employee_id)
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        # Execute phase in background
        background_tasks.add_task(
            agent_orchestrator.execute_phase,
            employee_id,
            record["onboarding_id"],
            phase
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

@app.get("/stats")
async def get_onboarding_stats():
    """Get summary statistics for all onboarding processes."""
    try:
        summary = db_manager.get_onboarding_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
