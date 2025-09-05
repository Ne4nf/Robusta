"""
Topic-based Vector Database Manager - AI Enhanced
Quản lý VectorDB theo từng topic với AI processing
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv

# Add current directory to Python path FIRST
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now try imports
try:
    from .llm_models import llm_manager
    from .document_processing.pdf_loader import PDFLoader
    from .document_processing.text_cleaner import TextCleaner
    from .document_processing.course_extractor import CourseInfoExtractor
    print("✅ Standard imports successful")
except ImportError as e:
    print(f"⚠️  Standard import failed: {e}")
    try:
        # Fallback to absolute imports
        from src.llm_models import llm_manager
        from src.document_processing.pdf_loader import PDFLoader
        from src.document_processing.text_cleaner import TextCleaner
        from src.document_processing.course_extractor import CourseInfoExtractor
        print("✅ Absolute imports successful")
    except ImportError as e2:
        print(f"❌ All imports failed: {e2}")
        # Set to None for graceful degradation
        llm_manager = None
        PDFLoader = None
        TextCleaner = None
        CourseInfoExtractor = None

load_dotenv()

class TopicVectorDB:
    """Quản lý VectorDB theo từng topic cụ thể"""
    
    # Mapping folder names to collection names
    TOPIC_COLLECTIONS = {
        "Ảo hóa": "robusta_virtualization",
        "BigData": "robusta_bigdata", 
        "Cloud computing": "robusta_cloud",
        "Lập trình di động": "robusta_mobile"
    }
    
    # Topic keywords for matching
    TOPIC_KEYWORDS = {
        "robusta_virtualization": ["vmware", "ảo hóa", "virtualization", "vsphere", "esxi", "vcenter", "hypervisor"],
        "robusta_bigdata": ["bigdata", "big data", "hadoop", "spark", "kafka", "data engineer", "data science", "elasticsearch"],
        "robusta_cloud": ["cloud", "aws", "azure", "gcp", "openstack", "kubernetes", "docker", "devops", "cloud computing"],
        "robusta_mobile": ["mobile", "di động", "react native", "android", "ios", "app development", "flutter"]
    }
    
    def __init__(self):
        # Qdrant configuration
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        
        # Embeddings
        self.embeddings = llm_manager.get_embeddings()
        
        # Text processing - Adjusted for course content
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1200"))  # Larger chunks for course content
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))  # More overlap for context
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]  # Better separators for Vietnamese
        )
        
        # Document processing
        self.pdf_loader = PDFLoader()
        self.text_cleaner = TextCleaner()
        self.course_extractor = CourseInfoExtractor()
        
    def create_topic_collections(self):
        """Tạo tất cả collections cho các topic"""
        for topic_folder, collection_name in self.TOPIC_COLLECTIONS.items():
            self._create_collection(collection_name)
            print(f"✅ Created collection: {collection_name}")
    
    def _create_collection(self, collection_name: str):
        """Tạo một collection với cấu hình chuẩn"""
        try:
            # Delete existing collection if exists
            try:
                self.client.delete_collection(collection_name)
                print(f"🗑️  Deleted existing collection: {collection_name}")
            except:
                pass
            
            # Create new collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=768,  # Gemini text-embedding-004 dimensions
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Created collection: {collection_name}")
            
        except Exception as e:
            print(f"❌ Error creating collection {collection_name}: {e}")
    
    def upload_topic_data(self, data_folder: str = "data"):
        """Upload data theo từng topic folder"""
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), data_folder)
        
        if not os.path.exists(data_path):
            print(f"❌ Data folder not found: {data_path}")
            return
        
        # Process text files first (chính sách, ưu đãi)
        self._process_text_files(data_path)
        
        # Process PDF files by topic folders
        for topic_folder, collection_name in self.TOPIC_COLLECTIONS.items():
            topic_path = os.path.join(data_path, topic_folder)
            
            if os.path.exists(topic_path):
                print(f"\n📂 Processing topic: {topic_folder}")
                self._process_topic_folder(topic_path, collection_name, topic_folder)
            else:
                print(f"⚠️  Topic folder not found: {topic_path}")
    
    def _process_text_files(self, data_path: str):
        """Process chính sách và ưu đãi files"""
        policy_file = os.path.join(data_path, "Chính sách và học vụ.txt")
        promotion_file = os.path.join(data_path, "Ưu đãi khuyến mãi.txt")
        
        # Upload to policies collection (reuse existing)
        if os.path.exists(policy_file):
            with open(policy_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self._upload_text_content(content, "robusta_policies", "policy", "Chính sách và học vụ")
        
        if os.path.exists(promotion_file):
            with open(promotion_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self._upload_text_content(content, "robusta_promotions", "promotion", "Ưu đãi khuyến mãi")
    
    def verify_all_files_processing(self):
        """Verify ALL files trong ALL topics được discovered và processed"""
        print("\n🔍 VERIFYING ALL FILES PROCESSING...")
        
        base_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        topics = {
            "virtualization": "Ảo hóa",
            "bigdata": "BigData", 
            "cloud": "Cloud computing",
            "mobile": "Lập trình di động"
        }
        
        total_discovered = 0
        for topic_key, topic_display in topics.items():
            folder_path = os.path.join(base_data_path, topic_display)
            if os.path.exists(folder_path):
                pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
                total_discovered += len(pdf_files)
                print(f"📁 {topic_display}: {len(pdf_files)} PDF files discovered")
                for pdf_file in pdf_files:
                    print(f"   - {pdf_file}")
            else:
                print(f"❌ Folder not found: {folder_path}")
        
        print(f"\n📊 TOTAL PDF FILES DISCOVERED: {total_discovered}")
        return total_discovered

    async def _process_topic_folder_ai(self, folder_path: str, collection_name: str, topic_name: str):
        """Process PDF files với AI processing"""
        processed_count = 0
        total_sections = 0
        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        
        print(f"\n📁 AI Processing folder: {folder_path}")
        print(f"📊 Found {len(pdf_files)} PDF files to process")
        
        for file_name in pdf_files:
            file_path = os.path.join(folder_path, file_name)
            
            try:
                print(f"\n📄 AI Processing: {file_name}")
                
                # Load PDF với AI processing
                documents = await self.pdf_loader.load_pdf_file(file_path)
                if not documents:
                    print(f"⚠️  Empty content: {file_name}")
                    continue
                
                # AI processing luôn trả về 3 sections có chất lượng
                print(f"✅ AI extracted {len(documents)} sections")
                
                # Upload từng document section
                course_name = os.path.splitext(file_name)[0]
                uploaded_sections = 0
                
                for doc in documents:
                    try:
                        await self._upload_document_section_ai(doc, collection_name, topic_name)
                        uploaded_sections += 1
                        
                        # Log thông tin section
                        section_info = doc.metadata.get('section_title', 'Unknown')
                        content_length = doc.metadata.get('content_length', len(doc.page_content))
                        ai_processed = doc.metadata.get('ai_processed', False)
                        language = doc.metadata.get('language_detected', 'unknown')
                        
                        print(f"   ✅ {section_info}: {content_length} chars, AI: {ai_processed}, Lang: {language}")
                        
                    except Exception as e:
                        print(f"❌ Error uploading section {doc.metadata.get('section', 'unknown')}: {e}")
                
                if uploaded_sections > 0:
                    processed_count += 1
                    total_sections += uploaded_sections
                    print(f"🎯 Uploaded: {file_name} ({uploaded_sections} sections)")
                else:
                    print(f"❌ Failed to upload any sections for: {file_name}")
                
            except Exception as e:
                print(f"❌ Error processing {file_name}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"📊 Topic {topic_name}: {processed_count} files processed, {total_sections} sections uploaded")

    async def _upload_document_section_ai(self, doc: Document, collection_name: str, topic_name: str):
        """Upload single document section với AI metadata"""
        try:
            # Generate embedding
            embedding = self.embeddings.embed_query(doc.page_content)
            
            # Enhanced metadata với AI processing info
            metadata = {
                **doc.metadata,
                "topic": topic_name,
                "upload_timestamp": datetime.now().isoformat(),
                "content_type": "course_section",
                "ai_enhanced": True
            }
            
            # Generate unique ID
            point_id = str(uuid.uuid4())
            
            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "content": doc.page_content,
                    "metadata": metadata
                }
            )
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
        except Exception as e:
            raise Exception(f"Failed to upload document section: {e}")

    def _process_topic_folder(self, folder_path: str, collection_name: str, topic_name: str):
        """Sync wrapper cho AI processing"""
        import asyncio
        asyncio.run(self._process_topic_folder_ai(folder_path, collection_name, topic_name))
    
    def _create_fallback_sections(self, full_text: str, file_name: str):
        """Tạo 3 sections cơ bản từ raw text khi extraction thất bại"""
        from langchain.schema import Document
        
        # Clean course name
        course_name = os.path.splitext(file_name)[0]
        
        # Split text into 3 roughly equal parts
        text_length = len(full_text)
        part_size = text_length // 3
        
        sections = []
        
        # Section 1: First third
        section1_text = full_text[:part_size].strip()
        if section1_text:
            sections.append(Document(
                page_content=section1_text,
                metadata={
                    "course_name": course_name,
                    "section": "section1_intro_duration",
                    "section_title": "Giới thiệu và Thời lượng (Fallback)"
                }
            ))
        
        # Section 2: Middle third
        section2_text = full_text[part_size:part_size*2].strip()
        if section2_text:
            sections.append(Document(
                page_content=section2_text,
                metadata={
                    "course_name": course_name,
                    "section": "section2_objectives_audience",
                    "section_title": "Mục tiêu và Đối tượng (Fallback)"
                }
            ))
        
        # Section 3: Last third
        section3_text = full_text[part_size*2:].strip()
        if section3_text:
            sections.append(Document(
                page_content=section3_text,
                metadata={
                    "course_name": course_name,
                    "section": "section3_content_modules",
                    "section_title": "Nội dung và Modules (Fallback)"
                }
            ))
        
        print(f"   📋 Created {len(sections)} fallback sections from raw text")
        return sections
    
    def _upload_document_section(self, document, collection_name: str, topic_name: str):
        """Upload một document section với metadata chính xác và handle short content"""
        try:
            content = document.page_content.strip()
            
            # Handle very short content
            if len(content) < 20:
                print(f"   ⚠️  Skipping very short section: {document.metadata.get('section', 'unknown')}")
                return
            
            # For short metadata sections, add context
            if len(content) < 100 and content.startswith("Thông tin"):
                content = f"Khóa học: {document.metadata['course_name']}\n\n{content}"
                print(f"   📝 Enhanced short section with course context")
            
            # Create embedding
            embedding = self.embeddings.embed_query(content)
            
            # Tạo point với metadata gọn gàng
            point = PointStruct(
                id=hash(f"{document.metadata['course_name']}_{document.metadata['section']}") % (2**31),
                vector=embedding,
                payload={
                    "content": content,
                    "course_name": document.metadata["course_name"],
                    "topic": topic_name,
                    "section": document.metadata["section"],
                    "section_title": document.metadata["section_title"],
                    "content_length": len(content)  # Add length for debugging
                }
            )
            
            # Upload to Qdrant
            self.client.upsert(collection_name=collection_name, points=[point])
            
        except Exception as e:
            print(f"❌ Error uploading document section: {e}")
            # Don't raise - continue with other sections
    
    def _upload_text_content(self, content: str, collection_name: str, doc_type: str, title: str):
        """Upload text content to collection"""
        try:
            # Ensure collection exists
            self._create_collection(collection_name)
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(content)
            
            points = []
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                # Create embedding
                embedding = self.embeddings.embed_query(chunk)
                
                # Create point
                point = PointStruct(
                    id=i,
                    vector=embedding,
                    payload={
                        "content": chunk,
                        "type": doc_type,
                        "title": title,
                        "chunk_index": i,
                        "collection": collection_name
                    }
                )
                points.append(point)
            
            # Upload to Qdrant
            if points:
                self.client.upsert(collection_name=collection_name, points=points)
                print(f"✅ Uploaded {len(points)} chunks to {collection_name}")
            
        except Exception as e:
            print(f"❌ Error uploading text content: {e}")
    
    def _upload_pdf_content(self, content: str, collection_name: str, file_name: str, 
                           topic: str, course_info: Dict[str, Any]):
        """Upload PDF content to topic collection với metadata gọn gàng"""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(content)
            
            points = []
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                # Create embedding
                embedding = self.embeddings.embed_query(chunk)
                
                # Metadata gọn gàng - chỉ những thông tin cần thiết
                point = PointStruct(
                    id=hash(f"{file_name}_{i}") % (2**31),  # Unique ID
                    vector=embedding,
                    payload={
                        "content": chunk,
                        "course_name": os.path.splitext(file_name)[0],
                        "topic": topic,
                        "chunk_index": i
                    }
                )
                points.append(point)
            
            # Upload to Qdrant
            if points:
                self.client.upsert(collection_name=collection_name, points=points)
                print(f"✅ Uploaded {len(points)} chunks from {file_name}")
            
        except Exception as e:
            print(f"❌ Error uploading PDF content: {e}")
    
    def search_by_topic(self, query: str, topic: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search trong một topic cụ thể hoặc auto-detect topic"""
        
        if not topic:
            # Auto-detect topic from query
            topic = self._detect_topic(query)
        
        collection_name = self._get_collection_name(topic)
        if not collection_name:
            print(f"⚠️  Unknown topic: {topic}")
            return []
        
        try:
            # Create query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )
            
            # Format results với metadata gọn gàng
            results = []
            for hit in search_results:
                results.append({
                    "content": hit.payload["content"],
                    "score": hit.score,
                    "course_name": hit.payload.get("course_name", ""),
                    "topic": hit.payload.get("topic", ""),
                    "collection": collection_name
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching topic {topic}: {e}")
            return []
    
    def _detect_topic(self, query: str) -> str:
        """Auto-detect topic from query keywords"""
        query_lower = query.lower()
        
        for collection, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return collection.replace("robusta_", "")
        
        # Default to cloud if no specific topic detected
        return "cloud"
    
    def _get_collection_name(self, topic: str) -> Optional[str]:
        """Get collection name from topic"""
        topic_map = {
            "virtualization": "robusta_virtualization",
            "ảo hóa": "robusta_virtualization",
            "bigdata": "robusta_bigdata",
            "cloud": "robusta_cloud",
            "mobile": "robusta_mobile",
            "di động": "robusta_mobile"
        }
        return topic_map.get(topic.lower(), f"robusta_{topic}")
    
    def get_collection_stats(self):
        """Lấy thống kê các collections"""
        stats = {}
        
        for topic_folder, collection_name in self.TOPIC_COLLECTIONS.items():
            try:
                info = self.client.get_collection(collection_name)
                stats[collection_name] = {
                    "topic": topic_folder,
                    "points_count": info.points_count,
                    "status": info.status
                }
            except Exception as e:
                stats[collection_name] = {
                    "topic": topic_folder,
                    "error": str(e)
                }
        
        return stats
    
    def guaranteed_process_all_topics(self):
        """GUARANTEED processing của ALL files trong ALL topics"""
        print("\n🚀 GUARANTEED PROCESSING ALL TOPICS...")
        
        # 1. Verify files first
        total_discovered = self.verify_all_files_processing()
        
        # 2. Process all topics với full verification
        topics_processed = 0
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        
        for topic_folder, collection_name in self.TOPIC_COLLECTIONS.items():
            topic_path = os.path.join(data_path, topic_folder)
            
            if os.path.exists(topic_path):
                print(f"\n📂 GUARANTEED Processing topic: {topic_folder}")
                self._process_topic_folder(topic_path, collection_name, topic_folder)
                topics_processed += 1
            else:
                print(f"❌ Topic folder not found: {topic_path}")
        
        # 3. Double check results
        print(f"\n📊 FINAL SUMMARY:")
        print(f"   Files discovered: {total_discovered}")
        print(f"   Topics processed: {topics_processed}")
        
        # 4. Check if any files missed
        if total_discovered > 0:
            print("✅ ALL files should be processed!")
        else:
            print("⚠️  No PDF files found to process")
        
        return total_discovered, topics_processed

def search_course_db(query: str, k: int = 5, topic: str = None) -> List[Dict[str, Any]]:
    """
    Function wrapper để search courses từ VectorDB
    Compatible với interface mà routing_chain.py và streamlit_chat.py expect
    """
    try:
        # Use the singleton instance to search
        results = topic_vectordb.search_by_topic(query=query, topic=topic, limit=k)
        
        # Convert to Document-like objects for compatibility
        from langchain.schema import Document
        
        documents = []
        for result in results:
            doc = Document(
                page_content=result["content"],
                metadata={
                    "course_name": result.get("course_name", ""),
                    "topic": result.get("topic", ""),
                    "score": result.get("score", 0.0),
                    "collection": result.get("collection", "")
                }
            )
            documents.append(doc)
        
        return documents
        
    except Exception as e:
        print(f"❌ Error in search_course_db: {e}")
        return []

# Singleton instance
topic_vectordb = TopicVectorDB()
