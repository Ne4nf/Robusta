"""
AI-Powered Course Content Processor
Sử dụng AI để phân tích và trích xuất nội dung khóa học từ PDF
"""

import logging
from typing import Dict, List, Optional, Tuple
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from ..llm_models import llm_manager

logger = logging.getLogger(__name__)

class AICourseProcessor:
    """Xử lý nội dung khóa học bằng AI thay vì rules cứng"""
    
    def __init__(self):
        self.llm = llm_manager.get_llm()
        
        # Template để phân tích và dịch nội dung PDF
        self.analysis_prompt = PromptTemplate(
            input_variables=["content"],
            template="""
Bạn là chuyên gia phân tích tài liệu khóa học. Nhiệm vụ của bạn:

1. **Phát hiện ngôn ngữ**: Xác định nội dung tiếng Anh hay tiếng Việt
2. **Dịch thuật**: Nếu là tiếng Anh, dịch toàn bộ sang tiếng Việt tự nhiên
3. **Phân tích cấu trúc**: Trích xuất 3 phần chính của khóa học

**Nội dung cần phân tích:**
{content}

**Yêu cầu output JSON:**
```json
{{
    "language_detected": "en" hoặc "vi",
    "course_sections": {{
        "overview": "Tên khóa học, mô tả tổng quan, thời lượng học",
        "objectives_audience": "Mục tiêu khóa học, đối tượng tham gia, yêu cầu tiên quyết", 
        "detailed_content": "Nội dung chi tiết, chương trình học, module"
    }},
    "translated_content": "Toàn bộ nội dung đã dịch tiếng Việt (nếu cần)"
}}
```

**Lưu ý quan trọng:**
- Nếu phát hiện tiếng Anh: dịch sang tiếng Việt tự nhiên, giữ nguyên thuật ngữ kỹ thuật
- Phân chia nội dung thành 3 phần rõ ràng theo yêu cầu
- Bỏ qua phần "hình thức đào tạo" - không đưa vào content
- Giữ nguyên cấu trúc, định dạng quan trọng
"""
        )
        
        # Template để matching profile khách hàng
        self.matching_prompt = PromptTemplate(
            input_variables=["course_info", "user_profile"],
            template="""
Bạn là chuyên gia tư vấn khóa học IT. Hãy phân tích mức độ phù hợp giữa khóa học và profile khách hàng.

**Thông tin khóa học:**
{course_info}

**Profile khách hàng:**
{user_profile}

**Phân tích confidence matching:**
```json
{{
    "confidence_score": 0.85,
    "matching_analysis": {{
        "strengths": ["Điểm mạnh phù hợp với khóa học"],
        "gaps": ["Kỹ năng cần bổ sung trước khi học"],
        "recommendations": ["Gợi ý cụ thể cho khách hàng"]
    }},
    "suitability_level": "high/medium/low"
}}
```
"""
        )
        
        # Template cho tư vấn mông lung
        self.consultation_prompt = PromptTemplate(
            input_variables=["field", "available_courses"],
            template="""
Khách hàng đang quan tâm đến lĩnh vực: {field}

**Khóa học có sẵn trong lĩnh vực:**
{available_courses}

**Tạo response tư vấn theo format:**

🎯 **Khóa học trong lĩnh vực {field}:**
[Liệt kê 3-5 khóa phù hợp nhất với mô tả ngắn gọn]

📋 **Để tư vấn chính xác hơn, bạn có thể chia sẻ:**
1. **Lĩnh vực học tập/làm việc hiện tại:** [?]
2. **Kỹ năng & kinh nghiệm có sẵn:** [?] 
3. **Mong đợi sau khóa học:** [?]

💡 *Dựa vào thông tin này, tôi sẽ gợi ý khóa học phù hợp nhất với mục tiêu của bạn!*
"""
        )

    async def process_pdf_content(self, raw_content: str) -> Dict:
        """
        Xử lý nội dung PDF bằng AI
        
        Args:
            raw_content: Nội dung thô từ PDF
            
        Returns:
            Dict chứa nội dung đã xử lý theo cấu trúc mới
        """
        try:
            # Gọi AI để phân tích và xử lý
            prompt_text = self.analysis_prompt.format(content=raw_content)
            response = await self.llm.ainvoke([HumanMessage(content=prompt_text)])
            
            # Parse JSON response
            result = self._parse_ai_response(response.content)
            
            logger.info(f"✅ AI processed PDF: language={result.get('language_detected')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI processing failed: {e}")
            # Fallback to basic processing
            return self._fallback_processing(raw_content)
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse JSON response từ AI"""
        try:
            import json
            # Tìm JSON block trong response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse AI response: {e}")
            # Return basic structure if parsing fails
            return {
                "language_detected": "vi",
                "course_sections": {
                    "overview": response_text[:500],
                    "objectives_audience": response_text[500:1000], 
                    "detailed_content": response_text[1000:]
                }
            }
    
    def _fallback_processing(self, content: str) -> Dict:
        """Fallback processing nếu AI fail"""
        # Split content thành 3 phần đều nhau
        content_length = len(content)
        third = content_length // 3
        
        return {
            "language_detected": "vi",
            "course_sections": {
                "overview": content[:third],
                "objectives_audience": content[third:2*third],
                "detailed_content": content[2*third:]
            }
        }
    
    async def calculate_matching_confidence(self, course_info: str, user_profile: str) -> Dict:
        """
        Tính confidence score giữa khóa học và profile user
        
        Args:
            course_info: Thông tin khóa học (objectives_audience section)
            user_profile: Profile khách hàng
            
        Returns:
            Dict chứa confidence score và phân tích
        """
        try:
            prompt_text = self.matching_prompt.format(
                course_info=course_info,
                user_profile=user_profile
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt_text)])
            return self._parse_ai_response(response.content)
            
        except Exception as e:
            logger.error(f"❌ Confidence calculation failed: {e}")
            # Default medium confidence
            return {
                "confidence_score": 0.5,
                "matching_analysis": {
                    "strengths": ["Cần phân tích thêm"],
                    "gaps": ["Chưa xác định được"],
                    "recommendations": ["Vui lòng cung cấp thêm thông tin"]
                },
                "suitability_level": "medium"
            }
    
    async def generate_field_consultation(self, field: str, available_courses: List[str]) -> str:
        """
        Tạo response tư vấn cho khách hàng mông lung
        
        Args:
            field: Lĩnh vực quan tâm (ví dụ: "Cloud Computing")
            available_courses: List khóa học có sẵn
            
        Returns:
            String response cho khách hàng
        """
        try:
            courses_text = "\n".join([f"- {course}" for course in available_courses])
            
            prompt_text = self.consultation_prompt.format(
                field=field,
                available_courses=courses_text
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt_text)])
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Consultation generation failed: {e}")
            return f"Hiện tại chúng tôi có các khóa học về {field}. Bạn có thể chia sẻ thêm về background để được tư vấn chính xác hơn?"

# Global instance
ai_course_processor = AICourseProcessor()