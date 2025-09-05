"""
LLM Models Configuration
LLM: OpenRouter/Groq | Embeddings: Gemini text-embedding-004
"""

import os
from typing import Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

class LLMManager:
    """Quản lý LLM (OpenRouter/Groq) và Embeddings (Gemini)"""
    
    def __init__(self):
        # LLM Provider selection - priority: groq -> openrouter -> fallback
        self.llm_provider = os.getenv("LLM_PROVIDER", "auto")  # "groq", "openrouter", or "auto"
        
        # OpenRouter configuration
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        
        # Groq configuration
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        
        # Gemini configuration for Embeddings only
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
        
        # Common settings
        self.temperature = float(os.getenv("TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        
        # Auto-detect available provider if set to auto
        if self.llm_provider == "auto":
            if self.groq_api_key:
                self.llm_provider = "groq"
                print("🤖 Using Groq as LLM provider")
            elif self.openrouter_api_key:
                self.llm_provider = "openrouter" 
                print("🤖 Using OpenRouter as LLM provider")
            else:
                raise ValueError("No LLM API key found. Please provide GROQ_API_KEY or OPENROUTER_API_KEY")
        
        # Validate based on selected provider
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        elif self.llm_provider == "openrouter" and not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
            
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY required for embeddings")
    
    def get_llm(self):
        """Khởi tạo LLM theo provider được chọn"""
        if self.llm_provider == "groq":
            return self._get_groq_llm()
        else:
            return self._get_openrouter_llm()
    
    def _get_groq_llm(self) -> ChatGroq:
        """Khởi tạo Groq LLM"""
        return ChatGroq(
            model=self.groq_model,
            groq_api_key=self.groq_api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
    
    def _get_openrouter_llm(self) -> ChatOpenAI:
        """Khởi tạo OpenRouter LLM"""
        return ChatOpenAI(
            model=self.openrouter_model,
            openai_api_key=self.openrouter_api_key,
            openai_api_base=self.openrouter_base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
    
    def get_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Khởi tạo Gemini Embeddings"""
        return GoogleGenerativeAIEmbeddings(
            model=self.embedding_model,
            google_api_key=self.google_api_key
        )

# Singleton instance
llm_manager = LLMManager()
