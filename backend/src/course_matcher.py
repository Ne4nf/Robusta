"""
Course Matching Logic - Cleaned Version
Smart matching với qualification check
"""

import os
import sys
from typing import Dict, List, Any, Optional
import json

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from smart_course_analyzer import smart_analyzer
    from llm_models import llm_manager
    from user_profile import UserProfile
except ImportError as e:
    print(f"Import error in course_matcher.py: {e}")
    smart_analyzer = None
    llm_manager = None

class CourseMatchingService:
    """Service để match khóa học với qualification check logic"""
    
    # Simplified qualification questions (3 main categories only)
    QUALIFICATION_TEMPLATE = """🎯 **Để tư vấn khóa học phù hợp, bạn vui lòng chia sẻ:**

**1. Lĩnh vực làm việc hiện tại:**
   • Developer, IT Support, System Admin, Student, Business Analyst...

**2. Kỹ năng và kinh nghiệm:**
   • Những công nghệ/tools đã biết (VD: Python, AWS, Linux...)
   • Số năm kinh nghiệm trong IT

**3. Mục tiêu sau khóa học:**
   • Chuyển đổi nghề nghiệp, thăng tiến, lấy chứng chỉ, nâng cao kỹ năng...

💡 **Với thông tin này, mình sẽ tư vấn khóa học cụ thể và phù hợp nhất!**"""
    
    def __init__(self):
        if llm_manager:
            self.llm = llm_manager.get_llm()
        else:
            self.llm = None
    
    def extract_user_profile(self, user_input: str) -> UserProfile:
        """Extract user profile from input using LLM"""
        
        if not self.llm:
            return UserProfile()
        
        extraction_prompt = f"""
Phân tích thông tin user và trích xuất theo format JSON:

USER INPUT: {user_input}

Hãy trích xuất thông tin và trả về JSON format:
{{
    "work_field": "lĩnh vực làm việc hiện tại",
    "current_skills": ["skill1", "skill2"],
    "goal": "mục tiêu sau khóa học", 
    "experience_level": "beginner/intermediate/advanced",
    "time_availability": "part-time/full-time",
    "budget": "ngân sách nếu có"
}}

Nếu thông tin không đủ, để trống string "".
CHỈ TRẢ VỀ JSON, KHÔNG GIẢI THÍCH THÊM.
"""
        
        try:
            response = self.llm.invoke(extraction_prompt)
            
            # Try to parse JSON from response
            response_text = response.content.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            profile_data = json.loads(response_text)
            
            return UserProfile(
                work_field=profile_data.get("work_field", ""),
                current_skills=profile_data.get("current_skills", []),
                goal=profile_data.get("goal", ""),
                experience_level=profile_data.get("experience_level", ""),
                time_availability=profile_data.get("time_availability", ""),
                budget=profile_data.get("budget", "")
            )
            
        except Exception as e:
            print(f"Error extracting user profile: {e}")
            return UserProfile()
    
    def format_consultation_response(self, user_profile: UserProfile, user_input: str) -> str:
        """Format complete consultation response using Smart Analyzer"""
        
        try:
            # Use Smart Course Analyzer for intelligent matching
            if smart_analyzer is None:
                return self.QUALIFICATION_TEMPLATE
            
            # Analyze user query with profile
            analysis_result = smart_analyzer.analyze_user_query(user_input, user_profile)
            
            if analysis_result["type"] == "specific_course":
                # User asked about specific course
                if analysis_result["found"]:
                    return analysis_result["course_info"]
                else:
                    return analysis_result["message"]
            
            elif analysis_result["type"] == "topic_based":
                # User asked about topic/field
                if not analysis_result["found"]:
                    # Check if needs qualification
                    if analysis_result.get("needs_qualification", False):
                        return analysis_result["message"]  # Qualification questions
                    else:
                        return analysis_result["message"]  # Error message
                else:
                    # Has recommendations
                    return analysis_result["recommendations"]
            
            else:
                return self.QUALIFICATION_TEMPLATE
            
        except Exception as e:
            print(f"Error in consultation response: {e}")
            return self.QUALIFICATION_TEMPLATE

# Singleton instance
course_matcher = CourseMatchingService()
