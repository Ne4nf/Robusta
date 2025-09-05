"""
Policy Tools - Quản lý 3 collections riêng cho courses, promotions, policies
Sử dụng Gemini text-embedding-004 cho tất cả
"""

import os
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import document processing
try:
    from document_processing.pdf_loader import PDFLoader
    from document_processing.course_extractor import CourseInfoExtractor
    from document_processing.text_cleaner import TextCleaner
    DOCUMENT_PROCESSING_AVAILABLE = True
except ImportError as e:
    print(f"Document processing not available: {e}")
    DOCUMENT_PROCESSING_AVAILABLE = False
    PDFLoader = None
    CourseInfoExtractor = None
    TextCleaner = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustaVectorDB:
    """Quản lý 2 collections: robusta_promotions, robusta_policies (chỉ cho policy & promotion)"""
    
    def __init__(self):
        # Qdrant configuration
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        # Collections - chỉ còn 2 collections
        self.promotions_collection = "robusta_promotions"
        self.policies_collection = "robusta_policies"
        
        # Gemini embeddings
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
        
        # Validation
        missing_vars = []
        if not self.qdrant_url:
            missing_vars.append("QDRANT_URL")
        if not self.qdrant_api_key:
            missing_vars.append("QDRANT_API_KEY")
        if not self.google_api_key:
            missing_vars.append("GOOGLE_API_KEY")
            
        if missing_vars:
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
        
        # Initialize clients
        self.client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
        )
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=self.embedding_model_name,
            google_api_key=self.google_api_key
        )
        
        # Initialize document processor
        if DOCUMENT_PROCESSING_AVAILABLE:
            self.pdf_loader = PDFLoader()
            logger.info("PDF processing enabled")
        else:
            self.pdf_loader = None
            logger.warning("PDF processing disabled - document_processing not available")
        
        logger.info("RobustaVectorDB initialized with 2 collections (promotions, policies)")
    
    def reset_collections(self):
        """Xóa và tạo lại 2 collections với dimension đúng"""
        collections = [
            self.promotions_collection, 
            self.policies_collection
        ]
        
        try:
            for collection_name in collections:
                # Try to delete collection if exists
                try:
                    self.client.delete_collection(collection_name)
                    logger.info(f"Deleted collection: {collection_name}")
                except Exception as e:
                    logger.info(f"Collection {collection_name} doesn't exist or can't be deleted: {e}")
                
                # Create new collection with correct dimension
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=768,  # text-embedding-004 dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {collection_name} with dimension 768")
                    
        except Exception as e:
            logger.error(f"Error resetting collections: {e}")
            raise
    
    def setup_collections(self):
        """Tạo 3 collections nếu chưa có"""
        collections = [
            self.courses_collection,
            self.promotions_collection, 
            self.policies_collection
        ]
        
        try:
            existing_collections = self.client.get_collections().collections
            existing_names = [col.name for col in existing_collections]
            
            for collection_name in collections:
                if collection_name not in existing_names:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=768,  # text-embedding-004 dimension
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created collection: {collection_name}")
                else:
                    logger.info(f"Collection {collection_name} already exists")
                    
        except Exception as e:
            logger.error(f"Error setting up collections: {e}")
            raise
    
    def upload_promotion_data(self):
        """Upload dữ liệu ưu đãi khuyến mãi"""
        try:
            data_file = os.path.join(os.path.dirname(__file__), "..", "data", "Ưu đãi khuyến mãi.txt")
            
            if not os.path.exists(data_file):
                logger.error(f"File not found: {data_file}")
                return
                
            with open(data_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Text splitting
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=300,
                chunk_overlap=30,
                separators=["\n\n", "\n", "- ", "+ ", ". "]
            )
            
            chunks = text_splitter.split_text(content)
            points = []
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    # Generate embedding
                    embedding = self.embeddings.embed_query(chunk.strip())
                    
                    point = PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={
                            "content": chunk.strip(),
                            "source": "Ưu đãi khuyến mãi.txt",
                            "type": "promotion",
                            "chunk_id": f"promotion_{i}"
                        }
                    )
                    points.append(point)
            
            # Upload to promotions collection
            if points:
                self.client.upsert(
                    collection_name=self.promotions_collection,
                    points=points
                )
                logger.info(f"Uploaded {len(points)} promotion documents")
                
        except Exception as e:
            logger.error(f"Error uploading promotion data: {e}")
            raise
    
    def upload_policy_data(self):
        """Upload dữ liệu chính sách học vụ"""
        try:
            data_file = os.path.join(os.path.dirname(__file__), "..", "data", "Chính sách và học vụ.txt")
            
            if not os.path.exists(data_file):
                logger.error(f"File not found: {data_file}")
                return
                
            with open(data_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Text splitting
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=300,
                chunk_overlap=30,
                separators=["\n\n", "\n", "- ", "+ ", ". "]
            )
            
            chunks = text_splitter.split_text(content)
            points = []
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    # Generate embedding
                    embedding = self.embeddings.embed_query(chunk.strip())
                    
                    point = PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={
                            "content": chunk.strip(),
                            "source": "Chính sách và học vụ.txt",
                            "type": "policy",
                            "chunk_id": f"policy_{i}"
                        }
                    )
                    points.append(point)
            
            # Upload to policies collection
            if points:
                self.client.upsert(
                    collection_name=self.policies_collection,
                    points=points
                )
                logger.info(f"Uploaded {len(points)} policy documents")
                
        except Exception as e:
            logger.error(f"Error uploading policy data: {e}")
            raise
    
    def search_promotions(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search trong promotions collection"""
        try:
            query_embedding = self.embeddings.embed_query(query)
            
            search_result = self.client.search(
                collection_name=self.promotions_collection,
                query_vector=query_embedding,
                limit=top_k
            )
            
            results = []
            for hit in search_result:
                results.append({
                    "content": hit.payload["content"],
                    "metadata": {k: v for k, v in hit.payload.items() if k != "content"},
                    "score": hit.score
                })
            
            logger.info(f"Found {len(results)} promotion results for: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching promotions: {e}")
            return []
    
    def search_policies(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search trong policies collection"""
        try:
            query_embedding = self.embeddings.embed_query(query)
            
            search_result = self.client.search(
                collection_name=self.policies_collection,
                query_vector=query_embedding,
                limit=top_k
            )
            
            results = []
            for hit in search_result:
                results.append({
                    "content": hit.payload["content"],
                    "metadata": {k: v for k, v in hit.payload.items() if k != "content"},
                    "score": hit.score
                })
            
            logger.info(f"Found {len(results)} policy results for: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching policies: {e}")
            return []

# Initialize vectorDB
try:
    vector_db = RobustaVectorDB()
except Exception as e:
    logger.error(f"Failed to initialize RobustaVectorDB: {e}")
    vector_db = None

def search_promotion_info(query: str) -> str:
    """Tìm kiếm thông tin ưu đãi"""
    if not vector_db:
        return "Không thể truy cập thông tin ưu đãi. Vui lòng liên hệ Robusta Training."
    
    try:
        results = vector_db.search_promotions(query, top_k=3)
        if results:
            content_parts = [result["content"] for result in results]
            return "\n\n".join(content_parts)
        else:
            return "Không tìm thấy thông tin ưu đãi phù hợp."
    except Exception as e:
        logger.error(f"Error searching promotion: {e}")
        return "Có lỗi khi tìm kiếm thông tin ưu đãi."

def search_policy_info(query: str) -> str:
    """Tìm kiếm thông tin chính sách"""
    if not vector_db:
        return "Không thể truy cập thông tin chính sách. Vui lòng liên hệ Robusta Training."
    
    try:
        results = vector_db.search_policies(query, top_k=3)
        if results:
            content_parts = [result["content"] for result in results]
            return "\n\n".join(content_parts)
        else:
            return "Không tìm thấy thông tin chính sách phù hợp."
    except Exception as e:
        logger.error(f"Error searching policy: {e}")
        return "Có lỗi khi tìm kiếm thông tin chính sách."

if __name__ == "__main__":
    # Setup and upload data
    if vector_db:
        print("🔄 Resetting collections with correct dimensions...")
        vector_db.reset_collections()
        
        print("🔄 Uploading promotion data...")
        vector_db.upload_promotion_data()
        
        print("🔄 Uploading policy data...")
        vector_db.upload_policy_data()
        
        print("🔄 Uploading course data...")
        vector_db.upload_course_data()
        
        print("✅ All data uploaded!")
        
        # Test searches
        print("\n🔍 Testing promotion search...")
        promo_result = search_promotion_info("học viên cũ")
        print(f"Promotion result: {promo_result[:200]}...")
        
        print("\n🔍 Testing policy search...")
        policy_result = search_policy_info("bao đậu")
        print(f"Policy result: {policy_result[:200]}...")
        
        print("✅ Cleanup completed! Policy tools now only handles promotions and policies.")
