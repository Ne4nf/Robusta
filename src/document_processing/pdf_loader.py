"""
PDF Loader Module
Handles PDF loading and document creation
"""

import os
import logging
from typing import List, Dict
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .course_extractor import CourseInfoExtractor

logger = logging.getLogger(__name__)

class PDFLoader:
    """Load và process PDF files thành structured documents"""
    
    def __init__(self):
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "800"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "100"))
        self.extractor = CourseInfoExtractor()
        
        # Text splitter for fallback chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def load_pdf_file(self, file_path: str) -> List[Document]:
        """Load single PDF file and create structured documents"""
        try:
            logger.info(f"Loading PDF: {file_path}")
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            
            logger.info(f"Loaded {len(pages)} pages from {file_path}")
            
            # Combine all pages for full course extraction
            full_text = "\n".join([page.page_content for page in pages])
            
            # Extract structured course information
            logger.info("Extracting structured course information...")
            course_info = self.extractor.extract_course_info(full_text)
            
            documents = []
            course_name = os.path.splitext(os.path.basename(file_path))[0]
            
            if course_info and len(course_info) >= 2:  # At least 2 sections found
                logger.info(f"Found {len(course_info)} course sections - creating 3 fixed documents")
                
                # Luôn tạo chính xác 3 documents từ 3 sections cố định
                section_configs = {
                    "section1_intro_duration": {
                        "title": "Giới thiệu và Thời lượng",
                        "type": "intro_duration"
                    },
                    "section2_objectives_audience": {
                        "title": "Mục tiêu và Đối tượng", 
                        "type": "objectives_audience"
                    },
                    "section3_content": {
                        "title": "Nội dung Khóa học",
                        "type": "course_content"
                    }
                }
                
                for section_key, config in section_configs.items():
                    content = course_info.get(section_key, f"Thông tin {config['title']} của khóa học.")
                    
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": os.path.basename(file_path),
                            "course_name": course_name,
                            "section": section_key,
                            "section_title": config["title"],
                            "section_type": config["type"]
                        }
                    )
                    documents.append(doc)
                    logger.info(f"  ✅ {section_key}: {len(content)} chars")
                
            else:
                # Fallback to chunking if structured extraction fails
                logger.warning("Structured extraction failed, using fallback chunking")
                documents = self.fallback_chunking(pages, file_path, course_name)
            
            logger.info(f"Created {len(documents)} documents from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def create_course_summary(self, course_name: str, course_info: Dict[str, str]) -> str:
        """Create a comprehensive but concise course summary"""
        summary_lines = [f"Khóa học: {course_name}\n"]
        
        # Priority order for summary
        priority_sections = ["overview", "objectives", "duration", "audience", "prerequisites", "content"]
        
        for section_name in priority_sections:
            if section_name in course_info:
                content = course_info[section_name]
                section_config = self.extractor.section_configs[section_name]
                section_title = section_config["title"]
                
                # Take first 200 chars for summary, but try to end at sentence boundary
                summary_text = content[:200]
                if len(content) > 200:
                    # Try to find last sentence ending
                    last_period = summary_text.rfind('.')
                    last_exclaim = summary_text.rfind('!')
                    last_question = summary_text.rfind('?')
                    
                    sentence_end = max(last_period, last_exclaim, last_question)
                    if sentence_end > 100:  # Make sure we have reasonable content
                        summary_text = summary_text[:sentence_end + 1]
                    else:
                        summary_text += "..."
                
                summary_lines.append(f"{section_title}: {summary_text}\n")
        
        return "\n".join(summary_lines).strip()
    
    def fallback_chunking(self, pages: List[Document], file_path: str, course_name: str) -> List[Document]:
        """Fallback chunking method when structured extraction fails"""
        logger.info("Applying fallback chunking...")
        
        # Clean pages before chunking
        cleaned_pages = []
        for i, page in enumerate(pages):
            cleaned_content = self.extractor.text_cleaner.clean_text(page.page_content)
            if len(cleaned_content) > 50:
                page.page_content = cleaned_content
                page.metadata.update({
                    "source": os.path.basename(file_path),
                    "file_path": file_path,
                    "course_name": course_name,
                    "page": i + 1,
                    "total_pages": len(pages),
                    "section_type": "raw_page",
                    "extraction_method": "fallback_chunking"
                })
                cleaned_pages.append(page)
        
        if not cleaned_pages:
            return []
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(cleaned_pages)
        
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "section": "raw_content",
                "section_title": "Nội dung thô",
                "section_type": "chunked"
            })
        
        logger.info(f"Created {len(chunks)} chunks via fallback method")
        return chunks
    
    def load_pdf_folder(self, folder_path: str) -> List[Document]:
        """Load all PDF files from a folder"""
        folder = Path(folder_path)
        if not folder.exists():
            logger.error(f"Folder {folder_path} does not exist")
            return []
        
        pdf_files = list(folder.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {folder_path}")
            return []
        
        logger.info(f"Found {len(pdf_files)} PDF files in {folder_path}")
        
        all_documents = []
        for pdf_file in pdf_files:
            documents = self.load_pdf_file(str(pdf_file))
            all_documents.extend(documents)
        
        logger.info(f"Total loaded: {len(all_documents)} documents from {len(pdf_files)} PDF files")
        return all_documents
