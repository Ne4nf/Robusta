"""
Routing Chain cho Robusta Chatbot - Version 2.0
Phân loại intent và route đến handler phù hợp dựa trên bảng intent từ company
"""

import os
import sys
from typing import Dict, Any, List, Optional
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from llm_models import llm_manager
    from sheets_logger import log_simple_chat
    from policy_tools import search_promotion_info, search_policy_info
    from course_matcher import course_matcher
    from topic_vectordb import search_course_db
except ImportError as e:
    print(f"Import error in routing_chain.py: {e}")
    # Fallback imports
    llm_manager = None
    log_simple_chat = None
    search_promotion_info = None
    search_policy_info = None
    course_matcher = None
    search_course_db = None
    search_promotion_info = None
    search_policy_info = None
    course_matcher = None

# Intent definitions từ bảng company với hardcode schedule và fixed rules
INTENTS_CONFIG = {
    "course_inquiry": {
        "name": "Thông tin học phí/Giá tiền, tư vấn viên",
        "keywords": ["học phí", "giá", "tiền", "chi phí", "cost", "price", "fee", "bao nhiêu tiền", "giá cả"],
        "action": "Gửi template reply mẫu -> Xin contact",
        "reply_template": "Thông tin này mình sẽ gửi trực tiếp qua tư vấn viên. Bạn vui lòng để lại thông tin liên hệ để được thoại lại nhé."
    },
    
    "course_consultation": {
        "name": "Tư vấn khóa học/Lộ trình",
        "keywords": ["tư vấn", "lộ trình", "roadmap", "học gì", "nên học", "phù hợp", "khóa nào", "course", "cloud computing", "aws", "ai", "machine learning", "devops", "khóa học", "những khóa", "có khóa", "học về", "muốn học", "bắt đầu từ đâu", "lập trình web", "frontend", "backend", "data engineer"],
        "action": "Lấy background, goal -> Gợi ý khóa học/lộ trình -> Xin contact",
        "reply_template": "Bạn có thể chia sẻ nền tảng, mục tiêu để mình tư vấn lộ trình phù hợp không?"
    },
    
    "schedule_inquiry": {
        "name": "Lịch khai giảng", 
        "keywords": ["lịch", "khai giảng", "bắt đầu", "schedule", "when", "khi nào", "tháng", "lịch học"],
        "action": "Lấy lịch từ hardcode trả kết quả -> xin contact",
        "hardcode_schedule": {
            "VMware": [
                {"course": "Triển khai, quản trị ha tầng ảo hóa VMware vSphere [V8]", "date": "15-09-2025", "time": "18h30 - 21h30 Thứ 2-4-6", "duration": "40h"},
                {"course": "Triển khai, quản trị ha tầng ảo hóa VMware vSphere [V8]", "date": "20-09-2025", "time": "8h30 - 17h30 Thứ 7", "duration": "40h"},
                {"course": "Chẩn đoán và khắc phục lỗi vSphere", "date": "20-09-2025", "time": "8h30 - 17h30 Thứ 7", "duration": "40h"},
                {"course": "Vận hành và mở rộng bảo mật ha tầng ảo hóa VMware Vsphere", "date": "11-10-2025", "time": "8h30 - 17h30 Thứ 7", "duration": "40h"}
            ],
            "Cloud": [
                {"course": "AWS Solutions Architect", "date": "25-09-2025", "time": "18h30 - 21h30 Thứ 2-4-6", "duration": "50h"},
                {"course": "Microsoft Azure Fundamentals", "date": "02-10-2025", "time": "18h30 - 21h30 Thứ 3-5-7", "duration": "45h"}
            ]
        },
        "reply_template": "Để cập nhật thông tin chi tiết và mới nhất, bạn gửi thông tin liên lạc để được tư vấn chi tiết hơn nhé?"
    },
    
    "promotion_inquiry": {
        "name": "Ưu đãi/Khuyến mãi",
        "keywords": ["ưu đãi", "khuyến mãi", "giảm giá", "promotion", "discount", "voucher", "giá ưu đãi", "học viên cũ", "nhóm", "đăng ký sớm"],
        "action": "Trả thông tin ưu đãi theo rules -> Xin contact",
        "reply_template": """Ưu đãi khuyến mãi Robusta:
• Giảm giá khi đăng ký sớm (trước 5 ngày khai giảng)
• Ưu đãi cho công ty đối tác
• Giảm 5% cho nhóm từ 3 học viên trở lên
• Học viên cũ có ưu đãi đặc biệt lên đến 50%
• Thanh toán 100% trước 5 ngày khai giảng

Để nhận ưu đãi tốt nhất, bạn để lại thông tin để được tư vấn cụ thể nhé!"""
    },
    
    "company_info": {
        "name": "Thông tin doanh nghiệp Robusta",
        "keywords": ["robusta", "công ty", "doanh nghiệp", "about", "company", "giới thiệu"],
        "action": "Trả thông tin doanh nghiệp từ PDF -> Xin contact",
        "reply_template": "Robusta thành lập từ năm 2015, đã đào tạo cho hơn 300+ doanh nghiệp. Bạn có muốn nhận thêm thông tin chi tiết qua email/sdt không?"
    },
    
    "training_for_company": {
        "name": "Doanh nghiệp cần đào tạo (B2B)",
        "keywords": ["đào tạo", "doanh nghiệp", "công ty", "team", "nhóm", "b2b", "corporate"],
        "action": "Hỏi số lượng, nội dung, thời gian, hình thức -> Xin contact",
        "reply_template": "Bạn có muốn mình xin thông tin liên hệ của người phụ trách để Robusta hỗ trợ xuất đào tạo nhé?"
    },
    
    "tech_consultation": {
        "name": "Trò chuyện công nghệ/định hướng",
        "keywords": ["công nghệ", "technology", "ai", "cloud", "devops", "career", "lập trình", "programming", "mobile", "di động", "android", "ios", "react native", "flutter", "định hướng", "tương lai", "xu hướng"],
        "action": "Trò chuyện chia sẻ kiến thức từ PDF, định hướng -> Xin contact",
        "reply_template": "Mình thấy AI có tốc độ phát triển rất nhanh... Nếu bạn muốn cập nhật những kiến thức mới để áp dụng vào công việc, mình có thể tư vấn khóa học phù hợp tại đây."
    },
    
    "policy_inquiry": {
        "name": "Chính sách & học vụ",
        "keywords": ["chính sách", "học vụ", "policy", "quy định", "điều kiện", "chứng chỉ", "cam kết", "bao đậu", "record", "e-learning", "trả góp", "thẻ tín dụng", "cấp lại", "thi", "cccd", "điều kiện tiền quyết", "yêu cầu", "requirement", "prerequisite", "cần gì", "cần những kiến thức", "kiến thức nền tảng", "cần học gì trước", "ôn luyện"],
        "action": "Trả thông tin theo fixed rules -> Xin contact",
        "reply_template": """Chính sách học vụ Robusta:
• Không cam kết bao đậu, phụ thuộc quá trình học của học viên
• Khóa học thiết kế chuẩn quốc tế với giảng viên chuyên gia có chứng chỉ
• Cấp chứng chỉ khi hoàn thành khóa học (80% buổi học + bài kiểm tra)
• Tất cả khóa học được record, cấp tài khoản e-learning truy cập 1 năm
• Hỗ trợ trả góp thẻ tín dụng tại HCM (HN chưa có)
• Đến trước giờ thi 15p, mang CCCD
• Cấp lại chứng chỉ qua e-learning hoặc để lại SĐT + email + tên khóa

Để biết thêm chi tiết vui lòng để lại thông tin liên hệ nhé!"""
    },
    
    "general_inquiry": {
        "name": "Câu hỏi ngoài phạm vi",
        "keywords": ["other", "general", "khác", "hello", "hi", "chào"],
        "action": "Gửi template reply mẫu -> Xin contact",
        "reply_template": "Mình là chatbot AI chỉ trò chuyện về công nghệ & tư vấn những thông tin liên quan về đào tạo cho robusta. Xin vui lòng hỏi về những điều liên quan học tập & để lại SDT/Gmail để được tư vấn, định hướng cụ thể nhé!"
    }
}

class IntentClassifier:
    """Phân loại intent từ user input"""
    
    def __init__(self):
        if llm_manager is None:
            raise ImportError("llm_manager not available")
        self.llm = llm_manager.get_llm()
        self.intent_prompt = self._create_intent_prompt()
    
    def _create_intent_prompt(self) -> ChatPromptTemplate:
        """Tạo prompt để phân loại intent"""
        
        intent_descriptions = []
        for intent_id, config in INTENTS_CONFIG.items():
            keywords = ", ".join(config["keywords"])
            intent_descriptions.append(f"- {intent_id}: {config['name']} (keywords: {keywords})")
        
        intent_list = "\n".join(intent_descriptions)
        
        return ChatPromptTemplate.from_template("""
Bạn là AI classifier cho chatbot Robusta Training. Nhiệm vụ: phân loại intent của user.

DANH SÁCH INTENT:
{intent_list}

NGUYÊN TẮC PHÂN LOẠI:
1. Đọc kỹ user input và hiểu ý nghĩa
2. So sánh với keywords và ý nghĩa của từng intent
3. Chọn intent phù hợp nhất dựa trên context
4. Nếu không rõ ràng, ưu tiên các intent chính: course_consultation, tech_consultation
5. Chỉ chọn general_inquiry khi thực sự ngoài phạm vi

EXAMPLES:
- "Học phí AWS bao nhiêu?" → course_inquiry
- "Tôi muốn học về cloud computing" → course_consultation  
- "Khóa AI khi nào khai giảng?" → schedule_inquiry
- "Có ưu đãi gì cho sinh viên không?" → promotion_inquiry
- "AI và Machine Learning khác nhau thế nào?" → tech_consultation
- "Robusta Training có bao nhiều năm kinh nghiệm?" → company_info
- "Công ty tôi muốn đào tạo 50 nhân viên về DevOps" → training_for_company
- "Điều kiện để nhận chứng chỉ là gì?" → policy_inquiry
- "Hôm nay thời tiết thế nào?" → general_inquiry

USER INPUT: {user_input}

HÃY PHÂN TÍCH VÀ CHỈ TRẢ VỀ INTENT ID DUY NHẤT (ví dụ: course_inquiry):
""".strip()).partial(intent_list=intent_list)
    
    def classify(self, user_input: str) -> str:
        """Phân loại intent của user input"""
        try:
            chain = self.intent_prompt | self.llm | StrOutputParser()
            result = chain.invoke({"user_input": user_input})
            
            # Clean result
            intent = result.strip().lower()
            
            # Validate intent exists
            if intent in INTENTS_CONFIG:
                return intent
            else:
                return "general_inquiry"
                
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return "general_inquiry"

class IntentHandler:
    """Handle các intent cụ thể"""
    
    def __init__(self):
        if llm_manager is None or search_course_db is None:
            raise ImportError("Required modules not available")
        self.llm = llm_manager.get_llm()
    
    def _check_qualification_info(self, user_input: str) -> bool:
        """Kiểm tra xem user đã cung cấp đủ thông tin qualification chưa"""
        user_text = user_input.lower()
        
        # Các keywords chỉ ra user đã cung cấp thông tin về background
        background_indicators = [
            # Trình độ/Kinh nghiệm
            "sinh viên", "năm cuối", "năm", "developer", "senior", "junior", "fresher", 
            "newbie", "mới vào nghề", "mới học", "đang làm", "làm việc",
            
            # Vị trí công việc
            "system admin", "devops", "it support", "qa tester", "business analyst",
            "project manager", "team lead", "tech lead", "data engineer", "frontend", "backend",
            
            # Kiến thức nền tảng
            "đã học", "đã có kiến thức", "biết về", "có nền tảng", "html", "css", "java", "python",
            
            # Mục tiêu rõ ràng
            "muốn học xong", "để đi làm", "với role", "mục tiêu", "định hướng", "career",
            "lấy chứng chỉ", "nâng cao kỹ năng", "thăng tiến", "chuyển nghề",
            
            # Ngân sách cụ thể
            "triệu", "budget", "chi phí", "khoảng",
            
            # Thời gian cụ thể
            "ngày/tuần", "buổi/tuần", "cuối tuần", "tối", "sáng", "part time", "full time"
        ]
        
        # Đếm số lượng indicators
        indicator_count = sum(1 for indicator in background_indicators if indicator in user_text)
        
        # Nếu có ít nhất 3 indicators hoặc input dài (>80 chars) thì coi như có qualification
        has_info = indicator_count >= 3 or len(user_input) > 80
        
        print(f"Qualification check: '{user_input}' -> {indicator_count} indicators, {len(user_input)} chars -> {has_info}")
        return has_info
    
    def _process_qualified_consultation(self, user_input: str, session_id: str, config: dict) -> Dict[str, Any]:
        """Xử lý consultation khi đã có qualification - Query RAG và dùng LLM để format"""
        try:
            # Query RAG để lấy thông tin khóa học
            rag_results = self._query_rag_for_consultation(user_input, session_id)
            
            if not rag_results:
                # Fallback nếu RAG không có kết quả
                return {
                    "intent": "course_consultation",
                    "answer": config["reply_template"],
                    "action": config["action"],
                    "next_step": "collect_contact",
                    "sources": []
                }
            
            # Dùng LLM để tạo câu trả lời tự nhiên từ RAG results
            personalized_answer = self._generate_personalized_response(user_input, rag_results)
            
            return {
                "intent": "course_consultation",
                "answer": personalized_answer,
                "action": config["action"],
                "next_step": "schedule_follow_up",
                "sources": ["Robusta Course Database"],
                "used_rag": True,
                "qualified": True
            }
            
        except Exception as e:
            print(f"Error in qualified consultation: {e}")
            return {
                "intent": "course_consultation",
                "answer": config["reply_template"],
                "action": config["action"],
                "next_step": "collect_contact",
                "sources": [],
                "error": str(e)
            }
    
    def _generate_personalized_response(self, user_input: str, rag_results: str) -> str:
        """Dùng LLM để tạo câu trả lời cá nhân hóa từ RAG results"""
        try:
            personalization_prompt = ChatPromptTemplate.from_template("""
Bạn là tư vấn viên Robusta Training. Dựa trên thông tin khách hàng và database, tư vấn NGẮN GỌN.

KHÁCH HÀNG: {user_input}

KHÓA HỌC PHÙHỢP: {rag_results}

TƯ VẤN NGẮN GỌN (2-3 câu):
- Phân tích nhu cầu của khách
- Recommend 1-2 khóa học phù hợp nhất
- Mời để lại thông tin tư vấn chi tiết

TONE: Thân thiện, không dài dòng.
""")
            
            chain = personalization_prompt | self.llm | StrOutputParser()
            result = chain.invoke({
                "user_input": user_input,
                "rag_results": rag_results
            })
            
            return result.strip()
            
        except Exception as e:
            print(f"Error generating personalized response: {e}")
            # Fallback: trả về RAG results trực tiếp
            return rag_results
    
    def _check_if_qualified(self, user_input: str) -> bool:
        """Kiểm tra xem user đã cung cấp đủ thông tin qualification chưa"""
        user_text = user_input.lower()
        qualification_indicators = [
            "năm kinh nghiệm", "đang làm", "mục tiêu", "muốn đạt", 
            "developer", "system admin", "sinh viên", "học", "chuyển nghề",
            "ngân sách", "thời gian", "tuần", "tháng"
        ]
        return any(indicator in user_text for indicator in qualification_indicators)
    
    def _query_rag_for_consultation(self, user_input: str, session_id: str) -> str:
        """Query RAG để lấy thông tin khóa học cụ thể sau khi đã qualification"""
        try:
            # Sử dụng search_course_db để lấy thông tin khóa học
            search_results = search_course_db(user_input, k=3)
            
            if search_results and len(search_results) > 0:
                # Ghép kết quả tìm kiếm thành course_info
                course_info = "\n\n".join([doc.page_content for doc in search_results])
                
                # Kiểm tra kết quả có hợp lệ không
                if course_info and len(course_info) > 50:
                    return course_info
                else:
                    print(f"Search returned insufficient data: {course_info}")
                    return None
            else:
                print("No search results found")
                return None
                
        except Exception as e:
            print(f"Course search error: {e}")
            return None
    
    def handle_course_inquiry(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Handle thông tin học phí - Template reply mẫu"""
        config = INTENTS_CONFIG["course_inquiry"]
        return {
            "intent": "course_inquiry",
            "answer": config["reply_template"],
            "action": config["action"],
            "next_step": "collect_contact",
            "sources": []
        }
    
    def handle_course_consultation(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Handle tư vấn khóa học - Sử dụng course matcher mới"""
        config = INTENTS_CONFIG["course_consultation"]
        
        try:
            # Sử dụng course matcher để xử lý
            if course_matcher is None:
                # Fallback to old method
                return self._fallback_course_consultation(user_input, config)
            
            # Extract user profile
            user_profile = course_matcher.extract_user_profile(user_input)
            
            # Format consultation response
            response = course_matcher.format_consultation_response(user_profile, user_input)
            
            # Determine next step
            if not user_profile.work_field or not user_profile.goal:
                next_step = "await_qualification"
                needs_qualification = True
            else:
                next_step = "collect_contact"
                needs_qualification = False
            
            return {
                "intent": "course_consultation",
                "answer": response,
                "action": config["action"],
                "next_step": next_step,
                "sources": [],
                "needs_qualification": needs_qualification,
                "user_profile": {
                    "work_field": user_profile.work_field,
                    "skills": user_profile.current_skills,
                    "goal": user_profile.goal,
                    "experience": user_profile.experience_level
                }
            }
            
        except Exception as e:
            print(f"Error in course consultation: {e}")
            return self._fallback_course_consultation(user_input, config)
    
    def _fallback_course_consultation(self, user_input: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback method cho course consultation"""
        qualification_questions = """🎯 Để tư vấn khóa học phù hợp, bạn vui lòng chia sẻ:

1. Lĩnh vực làm việc hiện tại:
   • Developer, IT Support, System Admin, Student, Business Analyst...

2. Kỹ năng và kinh nghiệm:
   • Những công nghệ/tools đã biết (VD: Python, AWS, Linux...)
   • Số năm kinh nghiệm trong IT

3. Mục tiêu sau khóa học:
   • Chuyển đổi nghề nghiệp, thăng tiến, lấy chứng chỉ, nâng cao kỹ năng...

💡 Với thông tin này, mình sẽ tư vấn khóa học cụ thể và phù hợp nhất!"""
        
        return {
            "intent": "course_consultation",
            "answer": qualification_questions,
            "action": config["action"],
            "next_step": "await_qualification",
            "sources": [],
            "needs_qualification": True
        }
    
    def handle_schedule_inquiry(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Handle lịch khai giảng - Dùng LLM format lịch ngắn gọn"""
        config = INTENTS_CONFIG["schedule_inquiry"]
        
        try:
            # Lấy hardcode schedule
            schedule_data = config["hardcode_schedule"]
            user_text = user_input.lower()
            
            # Detect course type
            if "vmware" in user_text or "vsphere" in user_text:
                courses = schedule_data["VMware"]
                course_type = "VMware"
            elif "aws" in user_text or "cloud" in user_text:
                courses = schedule_data["Cloud"] 
                course_type = "Cloud"
            else:
                # Show all courses
                courses = schedule_data["VMware"] + schedule_data["Cloud"]
                course_type = "Tất cả"
            
            # Sử dụng LLM để format lịch đẹp và ngắn gọn
            schedule_prompt = ChatPromptTemplate.from_template("""
Bạn là tư vấn viên Robusta Training. Khách hỏi lịch khai giảng, trả lời NGẮN GỌN.

LỊCH KHAI GIẢNG {course_type}:
{course_list}

CÂU HỎI: {user_input}

TRẢ LỜI NGẮN GỌN:
- Hiển thị 1-2 khóa phù hợp nhất
- Mời để lại thông tin để cập nhật lịch mới nhất

TONE: Thân thiện, tự nhiên.
""")
            
            # Format course list for LLM
            course_list = ""
            for course in courses[:3]:  # Limit to top 3
                course_list += f"• {course['course']} - {course['date']} ({course['time']})\n"
            
            chain = schedule_prompt | self.llm | StrOutputParser()
            formatted_answer = chain.invoke({
                "course_type": course_type,
                "course_list": course_list,
                "user_input": user_input
            })
            
            return {
                "intent": "schedule_inquiry",
                "answer": formatted_answer.strip(),
                "action": config["action"], 
                "next_step": "collect_contact",
                "sources": [{"file": "hardcode", "page": "internal", "content_preview": "Hardcode schedule data"}],
                "used_llm": True
            }
        except Exception as e:
            print(f"Error formatting schedule: {e}")
            return {
                "intent": "schedule_inquiry",
                "answer": config["reply_template"],
                "action": config["action"],
                "next_step": "collect_contact",
                "sources": []
            }
    
    def handle_promotion_inquiry(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Handle ưu đãi - Lấy từ vectorDB và format qua LLM"""
        config = INTENTS_CONFIG["promotion_inquiry"]
        
        try:
            # Lấy thông tin ưu đãi từ vectorDB
            if search_promotion_info:
                promotion_data = search_promotion_info(user_input)
            else:
                promotion_data = "Không thể truy cập thông tin ưu đãi."
            
            # Sử dụng LLM để format câu trả lời dựa trên data từ vectorDB
            promotion_prompt = ChatPromptTemplate.from_template("""
Bạn là tư vấn viên Robusta Training. Khách hỏi về ưu đãi, trả lời NGẮN GỌN, TRỰC TIẾP.

THÔNG TIN ƯU ĐÃI TỪ DATABASE:
{promotion_data}

CÂU HỎI KHÁCH HÀNG: {user_input}

HƯỚNG DẪN TRẢ LỜI:
- Trả lời ngắn gọn (2-3 câu) dựa trên thông tin database
- Tập trung vào ưu đãi phù hợp với câu hỏi
- Kết thúc bằng mời để lại thông tin để tư vấn

TONE: Thân thiện, tự nhiên.
""")
            
            chain = promotion_prompt | self.llm | StrOutputParser()
            formatted_answer = chain.invoke({
                "user_input": user_input,
                "promotion_data": promotion_data
            })
            
            return {
                "intent": "promotion_inquiry",
                "answer": formatted_answer.strip(),
                "action": config["action"],
                "next_step": "collect_contact",
                "sources": ["Robusta Promotions VectorDB"],
                "used_llm": True,
                "used_vectordb": True
            }
            
        except Exception as e:
            print(f"Error formatting promotion response: {e}")
            return {
                "intent": "promotion_inquiry",
                "answer": config["reply_template"],
                "action": config["action"],
                "next_step": "collect_contact", 
                "sources": []
            }
    
    def handle_company_info(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Handle thông tin doanh nghiệp - Template reply mẫu"""
        config = INTENTS_CONFIG["company_info"]
        return {
            "intent": "company_info",
            "answer": config["reply_template"],
            "action": config["action"],
            "next_step": "collect_contact",
            "sources": []
        }
    
    def handle_training_for_company(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Handle đào tạo doanh nghiệp - Qualification questions cho B2B"""
        config = INTENTS_CONFIG["training_for_company"]
        
        # Qualification questions cho doanh nghiệp
        b2b_questions = """🏢 **Để tư vấn gói đào tạo doanh nghiệp tốt nhất, vui lòng cung cấp thông tin:**

• **Quy mô:** Số lượng nhân viên cần đào tạo?
• **Vị trí:** Nhân viên đang làm việc ở vị trí nào? (Dev, IT, Manager...)
• **Nội dung:** Muốn đào tạo về lĩnh vực gì? (Cloud, AI, DevOps, Security...)
• **Thời gian:** Dự kiến thời gian đào tạo? (1 tuần, 1 tháng, 3 tháng...)
• **Hình thức:** Ưu tiên hình thức nào? (Onsite, Online, Hybrid)
• **Mục tiêu:** Mục tiêu cụ thể sau đào tạo? (Lấy chứng chỉ, nâng cao kỹ năng, áp dụng vào dự án...)

💼 **Robusta có kinh nghiệm đào tạo cho 300+ doanh nghiệp với các gói ưu đãi đặc biệt cho B2B!**

📞 **Bạn có muốn để lại thông tin liên hệ để nhận tư vấn chi tiết từ team B2B không?**"""
        
        return {
            "intent": "training_for_company",
            "answer": b2b_questions,
            "action": config["action"],
            "next_step": "collect_company_info",
            "sources": [],
            "needs_qualification": True
        }
    
    def handle_tech_consultation(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Handle trò chuyện công nghệ - Chỉ query RAG khi hỏi về khóa học cụ thể"""
        config = INTENTS_CONFIG["tech_consultation"]
        
        user_text = user_input.lower()
        
        # Kiểm tra xem có phải câu hỏi về khóa học cụ thể không
        course_specific_keywords = [
            "khóa học", "chứng chỉ", "lộ trình học", "đào tạo", "học tập",
            "aws certification", "azure certification", "vmware certification",
            "devops course", "ai course", "machine learning course"
        ]
        
        is_course_question = any(keyword in user_text for keyword in course_specific_keywords)
        
        if is_course_question:
            # Redirect to course consultation intent instead of querying RAG here
            return {
                "intent": "tech_consultation",
                "answer": """🎯 **Để tư vấn khóa học phù hợp nhất, mình cần chuyển sang chế độ tư vấn chuyên sâu.**

Bạn vui lòng hỏi lại câu hỏi dưới dạng: "Tôi muốn được tư vấn khóa học về [lĩnh vực]"

Ví dụ:
• "Tôi muốn được tư vấn khóa học về AWS"
• "Tư vấn lộ trình học DevOps cho mình"
• "Khóa học AI nào phù hợp với người mới bắt đầu?"

💡 **Như vậy mình sẽ thu thập thông tin của bạn để tư vấn chính xác nhất!**""",
                "action": config["action"],
                "next_step": "redirect_to_course_consultation",
                "sources": [],
                "redirect": "course_consultation"
            }
        
        # Template reply về xu hướng công nghệ chung - KHÔNG query RAG
        tech_guidance = """🚀 **Xu hướng công nghệ 2025 và định hướng phát triển:**

• **AI/Generative AI:** Cách mạng hóa mọi ngành - ChatGPT, Copilot, AI Integration
• **Cloud-First Strategy:** Multi-cloud, Hybrid cloud là bắt buộc
• **DevSecOps:** Tích hợp Security vào toàn bộ development lifecycle  
• **Edge Computing:** Xử lý dữ liệu gần user, giảm latency
• **Quantum Computing:** Công nghệ đột phá cho tương lai gần

💼 **Kỹ năng HOT nhất hiện tại:**
• **Cloud Architects:** AWS, Azure, GCP
• **AI Engineers:** Machine Learning, Deep Learning
• **DevOps Engineers:** Kubernetes, Docker, CI/CD
• **Cybersecurity Specialists:** Zero Trust, Cloud Security
• **Data Engineers:** Big Data, Analytics, Data Pipeline

🎯 **Lộ trình phát triển sự nghiệp:**
1. **Xác định specialization** - Chọn 1-2 lĩnh vực chuyên sâu
2. **Hands-on practice** - Project thực tế, not just theory
3. **Certification** - Chứng chỉ uy tín (AWS, Azure, CISSP...)
4. **Community** - Network với professionals cùng lĩnh vực

📚 **Muốn biết khóa học cụ thể? Hãy hỏi: "Tư vấn khóa học về [lĩnh vực]"**"""

        return {
            "intent": "tech_consultation",
            "answer": tech_guidance,
            "action": config["action"],
            "next_step": "tech_follow_up",
            "sources": [],
            "used_rag": False
        }
    
    def handle_policy_inquiry(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Handle chính sách học vụ - Lấy từ vectorDB và format qua LLM"""
        config = INTENTS_CONFIG["policy_inquiry"]
        
        try:
            # Lấy thông tin chính sách từ vectorDB
            if search_policy_info:
                policy_data = search_policy_info(user_input)
            else:
                policy_data = "Không thể truy cập thông tin chính sách."
            
            # Sử dụng LLM để format câu trả lời dựa trên data từ vectorDB
            policy_prompt = ChatPromptTemplate.from_template("""
Bạn là tư vấn viên Robusta Training. Khách hỏi về chính sách học vụ, trả lời NGẮN GỌN, CHÍNH XÁC.

THÔNG TIN CHÍNH SÁCH TỪ DATABASE:
{policy_data}

CÂU HỎI KHÁCH HÀNG: {user_input}

HƯỚNG DẪN TRẢ LỜI:
- Trả lời ngắn gọn (1-2 câu) dựa trên thông tin database
- Tập trung vào chính xác câu hỏi được hỏi
- Kết thúc bằng mời để lại thông tin nếu cần hỗ trợ thêm

TONE: Chuyên nghiệp, chính xác.
""")
            
            chain = policy_prompt | self.llm | StrOutputParser()
            formatted_answer = chain.invoke({
                "user_input": user_input,
                "policy_data": policy_data
            })
            
            return {
                "intent": "policy_inquiry",
                "answer": formatted_answer.strip(),
                "action": config["action"],
                "next_step": "collect_contact",
                "sources": ["Robusta Policies VectorDB"],
                "used_llm": True,
                "used_vectordb": True
            }
            
        except Exception as e:
            print(f"Error formatting policy response: {e}")
            return {
                "intent": "policy_inquiry",
                "answer": config["reply_template"],
                "action": config["action"],
                "next_step": "collect_contact",
                "sources": []
            }
    
    def handle_general_inquiry(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Handle câu hỏi tổng quát - Dùng LLM để đáp ứng linh hoạt"""
        config = INTENTS_CONFIG["general_inquiry"]
        
        try:
            # Sử dụng LLM để trả lời câu hỏi tổng quát về Robusta Training
            general_prompt = ChatPromptTemplate.from_template("""
Bạn là tư vấn viên Robusta Training. Trả lời NGẮN GỌN về các câu hỏi tổng quát.

THÔNG TIN ROBUSTA:
• Trung tâm đào tạo công nghệ hàng đầu
• Chuyên: Cloud Computing, DevOps, Container, Kubernetes, CI/CD
• Giảng viên giàu kinh nghiệm từ các công ty lớn
• Học thực hành, dự án thực tế, hỗ trợ việc làm
• Địa điểm: Hà Nội và TP.HCM
• Hình thức: Offline và Online

CÂU HỎI: {user_input}

TRẢ LỜI NGẮN GỌN (1-2 câu):
- Trả lời trực tiếp câu hỏi
- Mời tư vấn thêm nếu cần

TONE: Thân thiện, tự nhiên.
""")
            
            chain = general_prompt | self.llm | StrOutputParser()
            formatted_answer = chain.invoke({"user_input": user_input})
            
            return {
                "intent": "general_inquiry",
                "answer": formatted_answer.strip(),
                "action": config["action"],
                "next_step": "offer_consultation",
                "sources": ["Robusta Training Information"],
                "used_llm": True
            }
            
        except Exception as e:
            print(f"Error formatting general response: {e}")
            return {
                "intent": "general_inquiry",
                "answer": config["reply_template"],
                "action": config["action"],
                "next_step": "offer_consultation",
                "sources": []
            }

class RoutingChain:
    """Main routing chain manager"""
    
    def __init__(self):
        try:
            self.classifier = IntentClassifier()
            self.handler = IntentHandler()
        except ImportError as e:
            print(f"Error initializing routing chain: {e}")
            self.classifier = None
            self.handler = None
    
    def chat(self, user_input: str, session_id: str, enable_logging: bool = True) -> Dict[str, Any]:
        """
        Main chat function với routing
        """
        # Check if components are available
        if self.classifier is None or self.handler is None:
            return {
                "intent": "error",
                "answer": "Routing chain không khả dụng. Sử dụng RAG chain thông thường.",
                "action": "fallback_to_rag",
                "next_step": "retry",
                "sources": [],
                "session_id": session_id,
                "user_input": user_input,
                "routing_used": False,
                "error": "Components not initialized"
            }
        
        try:
            # Step 1: Classify intent
            intent = self.classifier.classify(user_input)
            print(f"🎯 Classified intent: {intent}")
            
            # Step 2: Route to appropriate handler
            handler_method = getattr(self.handler, f"handle_{intent}", None)
            
            if handler_method:
                response = handler_method(user_input, session_id)
            else:
                # Fallback to general handler
                response = self.handler.handle_general_inquiry(user_input, session_id)
            
            # Step 3: Add metadata
            response.update({
                "session_id": session_id,
                "user_input": user_input,
                "routing_used": True
            })
            
            # Step 4: Log if enabled
            if enable_logging and log_simple_chat is not None:
                try:
                    log_simple_chat(
                        question=user_input,
                        answer=response["answer"],
                        metadata={
                            "intent": intent,
                            "next_step": response.get("next_step"),
                            "routing": True
                        }
                    )
                except Exception as log_error:
                    print(f"Warning: Failed to log: {log_error}")
            
            return response
            
        except Exception as e:
            # Error fallback
            error_response = {
                "intent": "error",
                "answer": "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại hoặc liên hệ Robusta Training để được hỗ trợ.",
                "action": "error_handling",
                "next_step": "retry",
                "sources": [],
                "session_id": session_id,
                "user_input": user_input,
                "error": str(e),
                "routing_used": True
            }
            
            if enable_logging and log_simple_chat is not None:
                try:
                    log_simple_chat(
                        question=user_input,
                        answer=error_response["answer"],
                        metadata={"error": str(e), "routing": True}
                    )
                except:
                    pass
            
            return error_response

# Global routing chain manager - with safe initialization
try:
    routing_chain_manager = RoutingChain()
except Exception as e:
    print(f"Warning: Could not initialize routing chain manager: {e}")
    routing_chain_manager = None

def get_routing_chain():
    """Get routing chain manager instance"""
    return routing_chain_manager

# Legacy compatibility
def get_routing_chain_manager():
    """Legacy function name compatibility"""
    return routing_chain_manager
