"""
Smart Course Analyzer
AI-powered course matching system với intelligent analysis
"""

import os
import sys
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from topic_vectordb import topic_vectordb
    from llm_models import llm_manager
    from user_profile import UserProfile
except ImportError as e:
    print(f"Import error in smart_course_analyzer.py: {e}")

@dataclass
class CourseInfo:
    """Structured course information"""
    name: str
    topic: str
    description: str
    target_audience: str = ""
    prerequisites: str = ""
    objectives: str = ""
    duration: str = ""
    level: str = "intermediate"  # beginner, intermediate, advanced
    score: float = 0.0
    source_file: str = ""

class SmartCourseAnalyzer:
    """AI-powered course analysis và matching system"""
    
    def __init__(self):
        self.llm = llm_manager.get_llm()
        self.vectordb = topic_vectordb
        
        # Course name patterns for exact matching
        self.course_name_patterns = [
            r"khóa học (.+?)(?:\s|$)",
            r"course (.+?)(?:\s|$)", 
            r"(.+?)\s*(?:course|khóa học)",
            r"(?:về|about)\s+(.+?)(?:\s|$)"
        ]
    
    def analyze_user_query(self, user_input: str, user_profile: UserProfile = None) -> Dict[str, Any]:
        """Phân tích query và quyết định strategy"""
        
        # Step 1: Detect if user mentions specific course name
        specific_course = self._detect_specific_course(user_input)
        
        if specific_course:
            # Strategy A: Direct course information retrieval
            return self._get_specific_course_info(specific_course, user_profile)
        else:
            # Strategy B: Topic-based matching with AI scoring
            return self._get_topic_based_recommendations(user_input, user_profile)
    
    def _detect_specific_course(self, user_input: str) -> Optional[str]:
        """Detect if user mentions a specific course name"""
        
        # Known course names (từ VectorDB)
        known_courses = [
            "Đào Tạo Lập Trình Ứng Dụng Trên Thiết Bị Di Động Nâng Cao",
            "Khám phá và triển khai giải pháp Ảo hóa thay thế VMware",
            "ROBUSTA - CLOUD COMPUTING FUNDAMENTALS",
            "Cài đặt, cấu hình và quản trị cơ bản OpenStack",
            "BigData Nâng Cao",
            "Quản trị hệ thống Big Data",
            "VMware vSphere",
            "React Native",
            "Cloud Computing",
            "Big Data"
        ]
        
        user_lower = user_input.lower()
        
        # Exact or partial matches
        for course in known_courses:
            course_lower = course.lower()
            # Check if significant portion of course name is mentioned
            words = course_lower.split()
            significant_words = [w for w in words if len(w) > 3]  # Skip short words
            
            if len(significant_words) > 0:
                matched_words = sum(1 for word in significant_words if word in user_lower)
                match_ratio = matched_words / len(significant_words)
                
                if match_ratio >= 0.6:  # 60% of significant words match
                    return course
        
        return None
    
    def _get_specific_course_info(self, course_name: str, user_profile: UserProfile = None) -> Dict[str, Any]:
        """Get detailed information about a specific course"""
        
        try:
            # Search across all collections for this course
            all_results = []
            
            for collection in ["robusta_cloud", "robusta_virtualization", "robusta_bigdata", "robusta_mobile"]:
                try:
                    results = self.vectordb.search_by_topic(course_name, collection.replace("robusta_", ""), limit=5)
                    for result in results:
                        result["collection"] = collection
                    all_results.extend(results)
                except:
                    continue
            
            if not all_results:
                return {
                    "type": "specific_course",
                    "course_name": course_name,
                    "found": False,
                    "message": f"Không tìm thấy thông tin về khóa học '{course_name}'. Vui lòng liên hệ để được tư vấn chi tiết."
                }
            
            # Sort by relevance score
            all_results.sort(key=lambda x: x["score"], reverse=True)
            
            # Use LLM to format course information
            course_info = self._format_course_info_with_llm(course_name, all_results[:3], user_profile)
            
            return {
                "type": "specific_course",
                "course_name": course_name,
                "found": True,
                "course_info": course_info,
                "sources": all_results[:3]
            }
            
        except Exception as e:
            print(f"Error getting specific course info: {e}")
            return {
                "type": "specific_course",
                "course_name": course_name,
                "found": False,
                "message": "Có lỗi xảy ra khi tìm kiếm thông tin khóa học. Vui lòng thử lại."
            }
    
    def _get_topic_based_recommendations(self, user_input: str, user_profile: UserProfile = None) -> Dict[str, Any]:
        """Get AI-powered topic-based course recommendations - Kiểm tra qualification trước"""
        
        try:
            # Step 1: Check if we have enough user profile information
            if not user_profile or not self._has_sufficient_profile_info(user_profile):
                return {
                    "type": "topic_based",
                    "found": False,
                    "needs_qualification": True,
                    "message": self._get_qualification_questions()
                }
            
            # Step 2: Detect interested topics
            interested_topics = self._detect_topics_from_input(user_input)
            
            # Step 3: Get all courses from relevant collections
            all_courses = []
            
            for topic in interested_topics:
                collection_name = f"robusta_{topic}"
                try:
                    # Get broader search to capture all courses in topic
                    results = self.vectordb.search_by_topic(user_input, topic, limit=10)
                    
                    for result in results:
                        course_info = CourseInfo(
                            name=result.get("course_title", result.get("file_name", "Unknown Course")),
                            topic=topic,
                            description=result["content"],
                            source_file=result.get("file_name", ""),
                            score=result["score"]
                        )
                        all_courses.append(course_info)
                        
                except Exception as e:
                    print(f"Error searching topic {topic}: {e}")
                    continue
            
            if not all_courses:
                return {
                    "type": "topic_based",
                    "found": False,
                    "message": "Không tìm thấy khóa học phù hợp. Vui lòng chia sẻ thêm thông tin để tư vấn chi tiết."
                }
            
            # Step 4: AI-powered matching score calculation
            scored_courses = self._calculate_ai_matching_scores(all_courses, user_input, user_profile)
            
            # Step 5: Format recommendations
            recommendations = self._format_topic_recommendations(scored_courses[:5], user_input, user_profile)
            
            return {
                "type": "topic_based",
                "found": True,
                "interested_topics": interested_topics,
                "recommendations": recommendations,
                "total_courses_found": len(all_courses)
            }
            
        except Exception as e:
            print(f"Error in topic-based recommendations: {e}")
            return {
                "type": "topic_based",
                "found": False,
                "message": "Có lỗi xảy ra khi tìm kiếm khóa học. Vui lòng thử lại."
            }
    
    def _has_sufficient_profile_info(self, user_profile: UserProfile) -> bool:
        """Kiểm tra xem có đủ thông tin user profile không"""
        # Cần ít nhất 2/3 thông tin chính: work_field, goal, current_skills
        info_count = 0
        
        if user_profile.work_field and user_profile.work_field.strip():
            info_count += 1
        if user_profile.goal and user_profile.goal.strip():
            info_count += 1
        if user_profile.current_skills and len(user_profile.current_skills) > 0:
            info_count += 1
            
        return info_count >= 2  # Cần ít nhất 2/3 thông tin
    
    def _get_qualification_questions(self) -> str:
        """Trả về câu hỏi qualification chuẩn"""
        return """🎯 **Để tư vấn khóa học phù hợp, bạn vui lòng chia sẻ:**

**1. Lĩnh vực làm việc hiện tại:**
   • Developer, IT Support, System Admin, Student, Business Analyst...

**2. Kỹ năng và kinh nghiệm:**
   • Những công nghệ/tools đã biết (VD: Python, AWS, Linux...)
   • Số năm kinh nghiệm trong IT

**3. Mục tiêu sau khóa học:**
   • Chuyển đổi nghề nghiệp, thăng tiến, lấy chứng chỉ, nâng cao kỹ năng...

💡 **Với thông tin này, mình sẽ tư vấn khóa học cụ thể và phù hợp nhất!**"""
    
    def _detect_topics_from_input(self, user_input: str) -> List[str]:
        """Detect topics from user input using keyword matching"""
        
        topic_keywords = {
            "cloud": ["cloud", "aws", "azure", "gcp", "docker", "kubernetes", "devops", "openstack"],
            "virtualization": ["vmware", "ảo hóa", "virtualization", "vsphere", "hyper-v", "esxi"],
            "bigdata": ["bigdata", "big data", "data engineer", "hadoop", "spark", "data science", "analytics"],
            "mobile": ["mobile", "di động", "app", "react native", "android", "ios", "flutter"]
        }
        
        user_lower = user_input.lower()
        detected_topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                detected_topics.append(topic)
        
        # Default to cloud if no specific topic detected
        if not detected_topics:
            detected_topics = ["cloud"]
        
        return detected_topics
    
    def _calculate_ai_matching_scores(self, courses: List[CourseInfo], user_input: str, user_profile: UserProfile = None) -> List[CourseInfo]:
        """Use LLM to calculate intelligent matching scores"""
        
        try:
            # Prepare user context
            user_context = self._prepare_user_context(user_input, user_profile)
            
            # Create scoring prompt
            scoring_prompt = f"""
Bạn là chuyên gia tư vấn khóa học IT. Hãy tính điểm phù hợp (0-100) cho mỗi khóa học dựa trên thông tin user.

USER CONTEXT:
{user_context}

COURSES TO SCORE:
"""
            
            for i, course in enumerate(courses):
                scoring_prompt += f"""
Course {i+1}: {course.name}
Topic: {course.topic}
Description: {course.description[:200]}...
---
"""
            
            scoring_prompt += """
Hãy trả về JSON format:
{
    "scores": [
        {"course_index": 0, "score": 85, "reason": "lý do phù hợp"},
        {"course_index": 1, "score": 70, "reason": "lý do phù hợp"},
        ...
    ]
}

CHỈ TRẢ VỀ JSON, KHÔNG GIẢI THÍCH THÊM.
"""
            
            # Get LLM response
            response = self.llm.invoke(scoring_prompt)
            response_text = response.content.strip()
            
            # Parse JSON response
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            scoring_result = json.loads(response_text)
            
            # Apply scores to courses
            for score_info in scoring_result.get("scores", []):
                course_idx = score_info.get("course_index", 0)
                if 0 <= course_idx < len(courses):
                    courses[course_idx].score = float(score_info.get("score", 0)) / 100.0  # Normalize to 0-1
            
            # Sort by AI score
            courses.sort(key=lambda x: x.score, reverse=True)
            
            return courses
            
        except Exception as e:
            print(f"Error in AI scoring: {e}")
            # Fallback: use VectorDB similarity scores
            return sorted(courses, key=lambda x: x.score, reverse=True)
    
    def _prepare_user_context(self, user_input: str, user_profile: UserProfile = None) -> str:
        """Prepare user context for LLM analysis"""
        
        context = f"User Query: {user_input}\n"
        
        if user_profile:
            context += f"""
User Profile:
- Work Field: {user_profile.work_field or 'Not specified'}
- Skills: {', '.join(user_profile.current_skills) if user_profile.current_skills else 'Not specified'}
- Goal: {user_profile.goal or 'Not specified'}
- Experience Level: {user_profile.experience_level or 'Not specified'}
"""
        else:
            context += "User Profile: Not provided\n"
        
        return context
    
    def _format_course_info_with_llm(self, course_name: str, results: List[Dict], user_profile: UserProfile = None) -> str:
        """Format course information using LLM"""
        
        try:
            format_prompt = f"""
Bạn là tư vấn viên khóa học chuyên nghiệp. Hãy tạo thông tin chi tiết về khóa học dựa trên dữ liệu provided.

COURSE NAME: {course_name}

COURSE DATA:
"""
            
            for i, result in enumerate(results):
                format_prompt += f"""
Source {i+1}: {result.get('file_name', 'Unknown')}
Content: {result['content']}
Score: {result['score']:.3f}
---
"""
            
            if user_profile and (user_profile.work_field or user_profile.goal):
                format_prompt += f"""
USER CONTEXT:
- Background: {user_profile.work_field or 'Not specified'}
- Goal: {user_profile.goal or 'Not specified'}
"""
            
            format_prompt += """
Hãy tạo thông tin khóa học theo format:

📚 **[Tên khóa học]**

🎯 **Mô tả khóa học:**
[Mô tả chi tiết]

👥 **Đối tượng tham gia:**
[Ai nên học khóa này]

📋 **Nội dung chính:**
• [Điểm 1]
• [Điểm 2]
• [Điểm 3]

🎓 **Sau khóa học bạn sẽ:**
• [Kỹ năng 1]
• [Kỹ năng 2]

⏱️ **Thời lượng:** [nếu có]

📞 **Bước tiếp theo:**
Để được tư vấn chi tiết lịch khai giảng và ưu đãi, bạn vui lòng để lại thông tin liên hệ nhé!

Trả lời bằng tiếng Việt, chuyên nghiệp và thân thiện.
"""
            
            response = self.llm.invoke(format_prompt)
            return response.content.strip()
            
        except Exception as e:
            print(f"Error formatting course info: {e}")
            return f"📚 **{course_name}**\n\nThông tin chi tiết về khóa học này đang được cập nhật. Vui lòng liên hệ để được tư vấn chi tiết."
    
    def _format_topic_recommendations(self, courses: List[CourseInfo], user_input: str, user_profile: UserProfile = None) -> str:
        """Format topic-based recommendations using LLM"""
        
        try:
            format_prompt = f"""
Bạn là tư vấn viên khóa học chuyên nghiệp. Hãy tạo phản hồi tư vấn dựa trên các khóa học phù hợp đã tìm được.

USER QUERY: {user_input}

MATCHED COURSES:
"""
            
            for i, course in enumerate(courses):
                format_prompt += f"""
{i+1}. {course.name} (Topic: {course.topic})
   Score: {course.score:.3f}
   Description: {course.description[:150]}...
---
"""
            
            if user_profile and (user_profile.work_field or user_profile.goal):
                format_prompt += f"""
USER PROFILE:
- Background: {user_profile.work_field or 'Not specified'}
- Goal: {user_profile.goal or 'Not specified'}
- Skills: {', '.join(user_profile.current_skills) if user_profile.current_skills else 'Not specified'}
"""
            
            format_prompt += """
Hãy tạo phản hồi theo format:

🎯 **Dựa trên yêu cầu của bạn, đây là các khóa học phù hợp:**

**1. [Tên khóa học 1]** (⭐ [Điểm phù hợp])
   • [Tóm tắt ngắn gọn]
   • [Tại sao phù hợp]

**2. [Tên khóa học 2]** (⭐ [Điểm phù hợp])
   • [Tóm tắt ngắn gọn]
   • [Tại sao phù hợp]

**3. [Tên khóa học 3]** (⭐ [Điểm phù hợp])
   • [Tóm tắt ngắn gọn]
   • [Tại sao phù hợp]

💡 **Lời khuyên:**
[Gợi ý lộ trình hoặc khóa học nên ưu tiên]

📞 **Bước tiếp theo:**
Để được tư vấn chi tiết về lịch khai giảng và ưu đãi, bạn vui lòng để lại thông tin liên hệ!

❓ **Bạn có quan tâm đến lĩnh vực liên quan nào khác không?** (VD: DevOps, Data Analytics, Mobile Development...)

Viết bằng tiếng Việt, tự nhiên và chuyên nghiệp.
"""
            
            response = self.llm.invoke(format_prompt)
            return response.content.strip()
            
        except Exception as e:
            print(f"Error formatting recommendations: {e}")
            return "Đã tìm thấy một số khóa học phù hợp. Vui lòng liên hệ để được tư vấn chi tiết."

# Singleton instance
smart_analyzer = SmartCourseAnalyzer()
