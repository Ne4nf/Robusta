"""
Google Sheets Logger - Log conversations with simple format
"""

import json
import os
from datetime import datetime

def log_simple_chat(question: str, answer: str, metadata: dict = None):
    """
    Log simple chat với format time/question/answer + metadata
    
    Args:
        question: Câu hỏi của user
        answer: Trả lời của bot
        metadata: Optional metadata dict
    """
    log_data = {
        "time": datetime.now().isoformat(),
        "question": question,
        "answer": answer
    }
    
    # Add metadata if provided
    if metadata:
        log_data.update(metadata)
    
    # Log to local file
    log_file = "chat_logs.jsonl"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        print(f"✅ Logged chat: {question[:50]}...")
    except Exception as e:
        print(f"❌ Error logging chat: {e}")

def log_chat_to_sheets(question: str, answer: str, user_name: str = "user", 
                      intent: str = None, session_id: str = None, 
                      response_time: float = None, tokens_used: int = None,
                      context_used: str = None):
    """
    Compatibility function for old logging calls
    Simplifies to log_simple_chat
    """
    log_simple_chat(question, answer)