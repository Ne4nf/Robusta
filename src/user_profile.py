"""
User Profile Data Structures
"""

from typing import List
from dataclasses import dataclass

@dataclass
class UserProfile:
    """User profile for course matching"""
    work_field: str = ""  # Lĩnh vực làm việc
    current_skills: List[str] = None  # Kỹ năng hiện có
    goal: str = ""  # Mục tiêu sau khóa học
    experience_level: str = ""  # Beginner, Intermediate, Advanced
    time_availability: str = ""  # Part-time, Full-time
    budget: str = ""  # Budget range
    
    def __post_init__(self):
        if self.current_skills is None:
            self.current_skills = []
