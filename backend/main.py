"""
FastAPI main application for Robusta AI Chatbot
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import asyncio
from datetime import datetime
import logging

# Import backend modules - Updated to match current working code
from src.routing_chain import RoutingChain
from src.llm_models import LLMManager  
from src.sheets_logger import log_chat_to_sheets
from src.topic_vectordb import search_course_db
from src.policy_tools import RobustaVectorDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Robusta AI Chatbot API",
    description="AI-powered chatbot for course information and general queries",
    version="2.0.0"
)

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://localhost:80", "http://127.0.0.1:80"],  # React dev servers + production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components - Using current working logic
llm_manager = LLMManager()
routing_chain = RoutingChain()
vector_db = RobustaVectorDB()

# Session memory storage
session_memory = {}

# Pydantic models for API requests/responses
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    session_id: str
    timestamp: str

class CourseUploadResponse(BaseModel):
    message: str
    courses_processed: int
    failed_files: List[str]
    success: bool

class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]

# API Routes
@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        services={
            "llm": "operational",
            "vector_db": "operational",
            "memory": "operational"
        }
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint - Updated with current logic"""
    try:
        print(f"🔄 Received message: {message.message}")
        session_id = message.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get or create session memory
        if session_id not in session_memory:
            session_memory[session_id] = []
        
        # Process message with routing chain
        result = routing_chain.chat(
            user_input=message.message,
            session_id=session_id,
            enable_logging=True
        )
        
        # Extract response from result
        response = result.get('answer', 'Xin lỗi, tôi không thể xử lý yêu cầu này.')
        intent = result.get('intent', 'general')
        
        # Update session memory
        session_memory[session_id].append({
            "role": "user", 
            "content": message.message,
            "timestamp": datetime.now().isoformat()
        })
        session_memory[session_id].append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages per session
        if len(session_memory[session_id]) > 20:
            session_memory[session_id] = session_memory[session_id][-20:]
        
        # Log to sheets
        try:
            log_chat_to_sheets(
                user_message=message.message,
                bot_response=response,
                session_id=session_id
            )
        except Exception as e:
            logger.warning(f"Failed to log to sheets: {e}")
        
        return ChatResponse(
            response=response,
            intent=intent,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/courses", response_model=CourseUploadResponse)
async def upload_courses(files: List[UploadFile] = File(...)):
    """Upload multiple course PDF files"""
    try:
        processed_count = 0
        failed_files = []
        
        for file in files:
            if not file.filename.endswith('.pdf'):
                failed_files.append(f"{file.filename}: Không phải file PDF")
                continue
                
            try:
                # Save uploaded file temporarily
                temp_path = f"/tmp/{file.filename}"
                with open(temp_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                # Use current topic vectordb for processing
                success = search_course_db(temp_path, upload_mode=True)
                
                if success:
                    processed_count += 1
                else:
                    failed_files.append(f"{file.filename}: Lỗi xử lý PDF")
                
                # Clean up temp file
                os.remove(temp_path)
                
            except Exception as e:
                failed_files.append(f"{file.filename}: {str(e)}")
        
        return CourseUploadResponse(
            message=f"Đã xử lý thành công {processed_count} khóa học",
            courses_processed=processed_count,
            failed_files=failed_files,
            success=processed_count > 0
        )
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation history for a session"""
    try:
        messages = session_memory.get(session_id, [])
        return {"session_id": session_id, "messages": messages}
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversations/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session"""
    try:
        if session_id in session_memory:
            del session_memory[session_id]
        return {"message": f"Đã xóa lịch sử trò chuyện {session_id}"}
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test LLM connection
        llm_status = "operational"
        try:
            test_llm = llm_manager.get_llm()
            llm_status = "operational"
        except Exception:
            llm_status = "error"
        
        # Test vector DB connection
        vector_status = "operational"
        try:
            vector_db = RobustaVectorDB()
            vector_status = "operational"
        except Exception:
            vector_status = "error"
        
        return {
            "status": "healthy",
            "services": {
                "llm": llm_status,
                "vector_db": vector_status,
                "memory": "operational",
                "sheets": "operational"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve React static files in production
if os.getenv("ENVIRONMENT") == "production":
    app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
