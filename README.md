# 🤖 ROBUSTA Bot - Chatbot Tư vấn Khóa học IT

AI-powered chatbot tư vấn khóa học IT với React frontend và FastAPI backend.

## 🏗️ Kiến trúc

```
robusta-bot/
├── frontend/               # React app với Gemini-like UI
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── ChatInterface.js
│   │   │   ├── Sidebar.js
│   │   │   ├── UploadInterface.js
│   │   │   └── Settings.js
│   │   ├── utils/         # API utilities
│   │   └── App.js         # Main app
│   └── package.json
├── backend/               # FastAPI server
│   ├── main.py           # API endpoints
│   └── requirements.txt
├── src/                  # Core AI logic
│   ├── routing_chain.py  # Main AI routing
│   ├── llm_models.py     # LLM configurations
│   ├── topic_vectordb.py # Vector database
│   └── document_processing/
└── data/                 # Training documents
```

## 🚀 Khởi chạy nhanh

### 1. Setup môi trường
```bash
# Clone repository
git clone https://github.com/Ne4nf/Robusta.git
cd robusta-bot

# Tạo Python virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd frontend
npm install
cd ..
```

### 2. Cấu hình environment
```bash
# Copy và cấu hình file environment
copy .env.example .env

# Thêm API keys vào .env:
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
```

### 3. Khởi chạy services

**Development Mode (Port 8000):**
```bash
# Sử dụng script development
start_dev.bat

# Hoặc manual:
# Terminal 1 - Backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm start
```

**Production Mode (Port 80):**
```bash
# Sử dụng script production (yêu cầu admin rights)
start.bat

# Hoặc manual:
cd backend
python main.py  # Tự động chạy port 80
```

➡️ **Development**: http://localhost:3000 (proxy to backend:8000)
➡️ **Production**: http://localhost:80
- **Technology**: FastAPI, Python 3.12
- **Features**:
  - Multi-provider AI integration (Groq, OpenAI, Gemini)
  - Intent classification and routing
  - Vector database integration (Qdrant)
  - Course upload and processing
  - Google Sheets logging
  - Conversation memory management

### Chi tiết:
1. **Input**: Người dùng nhập câu hỏi trên giao diện React frontend
2. **Intent Classification**: AI phân loại ý định (tư vấn khóa học, hỏi chính sách, hỏi ưu đãi, lịch học...)
3. **Data Retrieval**: Tìm kiếm thông tin liên quan trong VectorDB hoặc template có sẵn
4. **AI Processing**: Model AI (GPT OSS 120B, Groq, Gemini) sinh câu trả lời phù hợp
5. **Output**: Hiển thị kết quả cho người dùng với thông tin chi tiết
6. **Logging**: Ghi lại cuộc hội thoại vào Google Sheets để theo dõi và phân tích

## Chi tiết từng file/module

###  Giao diện & Điều khiển
**`frontend/`** - React frontend với UI hiện đại (Gemini-like design)
- **`src/components/ChatInterface.js`** - Giao diện chat chính
- **`src/components/Sidebar.js`** - Sidebar navigation
- **`src/components/UploadInterface.js`** - Upload course files
- **`src/components/Settings.js`** - Settings panel


###  Xử lý AI & Logic 
**`src/routing_chain.py`** - Bộ não chính của hệ thống
- **Intent Classification**: Phân loại ý định người dùng thành 9 categories, chi tiết ở:
  - [Sheet 3](https://docs.google.com/spreadsheets/d/1ifGKB2hlJQaeL1ml7Wb1kGhpk0t-CMLSgk7deI2orL4/edit?gid=164103885#gid=164103885)


- **Smart Routing**: Điều hướng đến handler phù hợp dựa trên intent
- **Context Management**: Quản lý ngữ cảnh cuộc hội thoại
- **Response Generation**: Kết hợp RAG và AI để tạo câu trả lời chính xác


**`src/llm_models.py`** - Quản lý Model AI
- **Multi-Provider Support**: Tích hợp 3 providers (OpenRouter, Groq, Gemini)
- **Auto-Fallback**: Tự động chuyển đổi model khi gặp lỗi
- **Model Configuration**: Cấu hình temperature, max_tokens tối ưu
- **Embedding Management**: Quản lý text embedding cho vector search

###  Xử lý & Quản lý Dữ liệu
**`src/topic_vectordb.py`** - Kho dữ liệu course outline
- **Multi-Collection Management**: Quản lý collections theo chủ đề:
  - Cloud Computing (robusta_cloud)
  - BigData (robusta_bigdata)
  - Ảo hóa (robusta_virtualization)
  - Lập trình di động (robusta_mobile)
  - ....
- **Enhanced PDF Processing**: Xử lý file PDF với quality assurance
- **Semantic Search**: Tìm kiếm ngữ nghĩa với độ chính xác cao
- **Content Quality Control**: Đảm bảo chất lượng nội dung

**`src/policy_tools.py`** - Xử lý câu hỏi chính sách và ưu đãi,...
- Sau này sẽ thêm info robusta, lịch,...

**`src/document_processing/`** - Bộ xử lý tài liệu
- **`pdf_loader.py`**: Load và đọc file PDF khóa học
- **`course_extractor.py`**: Trích xuất thông tin khóa học có cấu trúc
- **`text_cleaner.py`**: Làm sạch và chuẩn hóa text


###  Logging & Theo dõi
**`src/sheets_logger.py`** - Ghi log và theo dõi
- Tự động log cuộc hội thoại vào Google Sheets
- Theo dõi intent distribution, user behavior
- Export data để phân tích và cải thiện hệ thống

###  Modules hỗ trợ
**`src/course_matcher.py`** - Match khóa học phù hợp với nhu cầu học viên

**`src/schedule_crawler.py`** - Quản lý lịch khai giảng ( Phần này sẽ tạo lịch crawl sau)

**`src/user_profile.py`** - Quản lý profile người dùng



## Technical Stack 
- **Frontend**: React 18, Tailwind CSS, Framer Motion
- **Backend**: FastAPI, Python 3.12
- **AI Models**: OpenAI GPT OSS 120B, Groq, Google Gemini
- **Vector Database**: Qdrant Cloud
- **Document Processing**: PyPDF, LangChain
- **Logging**: Google Sheets API
- **Embedding**: Google Text-Embedding-004

## Demo Features
Phần handle data 1 file pdf khóa học sẽ gồm các mục như: Giới thiêu / Thời lượng / Hình thức đào tạo / Mục tiêu khóa học / Đối tượng tham gia / Yêu cầuu tiên quyết / Nội dung khóa học

 - Có những file pdf tiếng anh ( Có cần dịch qua tiếng việt hết không???)
 - Có những file không đảm đủ các phần như trên và chứa các hình, thông tin nhiễu ( Nên phần process course outline này chưa được clean)
 - Hiện tại sẽ clipping là 3 section rồi mới đưa vào vectorDB là:
       1. Giới thiệu & thời lượng ( Để reply cho khách cần thông tin tổng quan)
       2. Mục tiêu, đối tượng tham gia, yêu cầu tiên quyết (Phần này quan trọng để tính confidnece matching với background khách hàng)
       3. Nội dung chi tiết (Reply chi tiết khóa học)
       4. Phần hình thức đào tạo bỏ luôn để đưa sang chính sách học vụvụ

1. Về ưu đãi, chính sách học vụ,... thì đã xong (vì data ít)
2. Lịch khai giảng sẽ tạo AI agent tự động crawl data trên web robusta sau:
   - Dùng CrewAI + Playwright để tổ chức crawl định kì lịch khai giảng theo tuần.

3. Về tư vấn khóa học từ các course outline:
   - Khi người dùng hỏi đúng tên khóa học trong database --> Tư vấn luôn khóa đó
   - Khi người dùng đang mông lung trong lĩnh lực (Tôi muốn học Cloud không biết nên học gì?....) --> Reply theo mẫu để confirm mức độ phù hợp:
          1. Lĩnh vực học tập, làm việc
          2. Kỹ năng & kinh nghiệm
          3. Mong đợi sau khóa học
     Sau khi có được info background đối tượng thì đưa qua 1 model tính score confidence(mức độ liên quan), sau đó lấy top K khóa có điểm cao nhất đưa qua 1 hàm rerank nữa để đề xuất 3 khóa phù hợp nhất
     (Hiện tại thì em chỉ prompt cho AI tự chấm điểm)
   - Còn về tư vấn lộ trình thì "có thể" dùng model khác để classify theo level rồi tư vấn lộ trình





