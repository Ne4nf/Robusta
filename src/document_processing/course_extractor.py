"""
Course Information Extractor
Handles structured extraction of course information from cleaned text
"""

import re
import logging
from typing import Dict, List, Optional
from .text_cleaner import TextCleaner

logger = logging.getLogger(__name__)

class CourseInfoExtractor:
    """Extract thông tin khóa học có cấu trúc từ PDF với logic chuẩn"""
    
    def __init__(self):
        self.text_cleaner = TextCleaner()
        
        # Định nghĩa patterns chuẩn cho 6 sections - FIXED OVERLAP ISSUE
        self.section_configs = {
            "overview": {
                "title": "Giới thiệu/Tổng quan khóa học",
                "patterns": [
                    r"i+\.\s*tổng quan",
                    r"i+\.\s*giới thiệu",
                    r"tổng quan\s*$",
                    r"giới thiệu về khóa học"
                ],
                "keywords": ["tổng quan", "giới thiệu khóa học", "mô tả khóa học"],
                "stop_patterns": [r"ii+\.\s*thời lượng", r"thời lượng\s*\d+"]
            },
            "duration": {
                "title": "Thời lượng & Hình thức đào tạo", 
                "patterns": [
                    r"ii+\.\s*thời lượng",
                    r"thời lượng\s*\d+",
                    r"thời lượng.*giờ"
                ],
                "keywords": ["thời lượng", "hình thức đào tạo", "thời gian học"],
                "stop_patterns": [r"iii+\.\s*mục tiêu", r"mục tiêu khóa học"]
            },
            "objectives": {
                "title": "Mục tiêu khóa học",
                "patterns": [
                    r"iii+\.\s*mục tiêu khóa học",
                    r"mục tiêu khóa học",
                    r"mục tiêu\s*$"
                ],
                "keywords": ["mục tiêu khóa học", "mục tiêu", "sau khóa học"],
                "stop_patterns": [r"iv+\.\s*đối tượng", r"đối tượng tham gia"]
            },
            "audience": {
                "title": "Đối tượng tham gia",
                "patterns": [
                    r"iv+\.\s*đối tượng tham gia",
                    r"đối tượng tham gia",
                    r"đối tượng\s*$"
                ],
                "keywords": ["đối tượng tham gia", "đối tượng", "học viên"],
                "stop_patterns": [r"v+\.\s*nội dung", r"nội dung khóa học", r"chương trình"]
            },
            "content": {
                "title": "Nội dung khóa học",
                "patterns": [
                    r"v+\.\s*nội dung khóa học",
                    r"nội dung khóa học",
                    r"chương trình học",
                    r"module\s*\d+"
                ],
                "keywords": ["nội dung khóa học", "chương trình", "module", "nội dung đào tạo"],
                "stop_patterns": []  # Last section, no stop patterns
            }
        }
    
    def find_section_boundaries(self, text: str, section_name: str) -> Optional[tuple]:
        """Find start and end positions for a section with precise boundary detection"""
        config = self.section_configs[section_name]
        text_lower = text.lower()
        
        # Find start position using patterns and keywords
        start_pos = None
        start_method = None
        
        # Try patterns first (more precise)
        for pattern in config["patterns"]:
            match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            if match:
                start_pos = match.start()
                start_method = "pattern"
                break
        
        # Fallback to keywords if patterns don't work
        if start_pos is None:
            for keyword in config["keywords"]:
                pattern = rf'(?:^|\n)\s*[•\-\*]?\s*{re.escape(keyword)}'
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    start_pos = match.start()
                    start_method = "keyword"
                    break
        
        if start_pos is None:
            return None
        
        # Find end position using stop patterns
        end_pos = len(text)
        
        if config["stop_patterns"]:
            for stop_pattern in config["stop_patterns"]:
                # Look for stop pattern after the start position + some offset
                search_text = text[start_pos + 50:]  # Skip 50 chars to avoid matching same section
                stop_match = re.search(stop_pattern, search_text, re.IGNORECASE | re.MULTILINE)
                if stop_match:
                    end_pos = min(end_pos, start_pos + 50 + stop_match.start())
        
        # Also try generic section boundaries (Roman numerals, etc.)
        search_text = text[start_pos + 100:]  # Larger offset for generic patterns
        generic_stops = [
            r'\n\s*[ivx]+\.\s*[a-zA-ZÀ-ỹ]',  # Roman numerals
            r'\n\s*\d+\.\s*[A-ZÀÁẢÃẠ]',      # Numbered sections starting with capital
        ]
        
        for stop_pattern in generic_stops:
            stop_match = re.search(stop_pattern, search_text, re.IGNORECASE)
            if stop_match:
                end_pos = min(end_pos, start_pos + 100 + stop_match.start())
        
        logger.debug(f"Section {section_name}: start={start_pos} ({start_method}), end={end_pos}, length={end_pos-start_pos}")
        
        return (start_pos, end_pos)
    
    def extract_section_content(self, text: str, section_name: str) -> str:
        """Extract content for a specific section"""
        boundaries = self.find_section_boundaries(text, section_name)
        
        if not boundaries:
            return ""
        
        start_pos, end_pos = boundaries
        section_text = text[start_pos:end_pos]
        
        # Clean the extracted section
        cleaned_text = self.text_cleaner.clean_text(section_text)
        
        # Remove section header from content
        config = self.section_configs[section_name]
        header_patterns = [
            rf'{re.escape(config["title"])}:?',
            r'^[ivx]+\.\s*',  # Roman numerals
            r'^\d+\.\s*',     # Numbers
        ]
        
        for pattern in header_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Section-specific post-processing
        cleaned_text = self.post_process_section(cleaned_text, section_name)
        
        return cleaned_text.strip()
    
    def post_process_section(self, content: str, section_type: str) -> str:
        """Post-process section content based on section type"""
        if not content:
            return ""
        
        if section_type == "duration":
            # Ensure time info is properly formatted
            content = re.sub(r'(\d+)\s*(giờ|ngày|tuần|tháng)', r'\1 \2', content, flags=re.IGNORECASE)
        
        elif section_type == "content":
            # Structure module content better
            content = re.sub(r'Module\s*(\d+)', r'\nModule \1', content, flags=re.IGNORECASE)
            content = re.sub(r'Chương\s*(\d+)', r'\nChương \1', content, flags=re.IGNORECASE)
        
        elif section_type == "objectives":
            # Ensure bullet points are properly formatted
            content = re.sub(r'(?:^|\n)([^•\n])', r'\n• \1', content)
        
        # Final cleanup
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        return content.strip()
    
    def _create_fixed_sections(self, raw_sections: Dict[str, str], full_text: str) -> Dict[str, str]:
        """Tạo chính xác 3 sections cố định từ raw sections với boundaries chính xác"""
        fixed_sections = {}
        
        # Clean full text first để đảm bảo không có company noise
        cleaned_full_text = self.text_cleaner.clean_text(full_text)
        
        # SECTION 1: Giới thiệu & Thời lượng
        section1_content = self._extract_precise_section1(cleaned_full_text, raw_sections)
        fixed_sections["section1_intro_duration"] = section1_content
        
        # SECTION 2: Mục tiêu & Đối tượng & Điều kiện  
        section2_content = self._extract_precise_section2(cleaned_full_text, raw_sections)
        fixed_sections["section2_objectives_audience"] = section2_content
        
        # SECTION 3: Nội dung khóa học
        section3_content = self._extract_precise_section3(cleaned_full_text, raw_sections)
        fixed_sections["section3_content"] = section3_content
        
        return fixed_sections
    
    def _extract_precise_section1(self, text: str, raw_sections: Dict[str, str]) -> str:
        """Extract chính xác section 1: Giới thiệu + Thời lượng (LOẠI BỎ Hình thức đào tạo)"""
        parts = []
        
        # 1. Tìm phần giới thiệu
        intro_patterns = [
            r'I\.\s*(?:Giới thiệu|Tổng quan).*?(?=II\.|III\.|Thời lượng|$)',
            r'(?:Giới thiệu|Tổng quan)(?:\s+về)?\s+(?:khóa học|khoá học).*?(?=II\.|Thời lượng|Mục tiêu|$)',
            r'OpenStack là.*?(?=II\.|Thời lượng|$)',
            r'Khóa học.*?cung cấp.*?(?=II\.|Thời lượng|Mục tiêu|$)',
            r'Trong bối cảnh.*?(?=II\.|Thời lượng|Mục tiêu|$)'
        ]
        
        intro_text = ""
        for pattern in intro_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                intro_text = match.group().strip()
                # Clean section header
                intro_text = re.sub(r'^I\.\s*(?:Giới thiệu|Tổng quan).*?:\s*', '', intro_text, flags=re.IGNORECASE)
                intro_text = re.sub(r'^(?:Giới thiệu|Tổng quan).*?:\s*', '', intro_text, flags=re.IGNORECASE)
                break
        
        if intro_text:
            parts.append(f"Tổng quan khóa học:\n{intro_text}")
        
        # 2. Tìm phần thời lượng (BỎ QUA hình thức đào tạo)
        duration_patterns = [
            r'II\.\s*Thời lượng.*?(?=III\.|IV\.|Hình thức|Mục tiêu|$)',
            r'Thời lượng(?:\s+khóa học)?:.*?(?:giờ|ngày|tuần).*?(?=III\.|IV\.|Hình thức|Mục tiêu|Đối tượng|$)'
        ]
        
        duration_text = ""
        for pattern in duration_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                duration_text = match.group().strip()
                # Clean section headers
                duration_text = re.sub(r'^II\.\s*Thời lượng.*?:\s*', '', duration_text, flags=re.IGNORECASE)
                duration_text = re.sub(r'^Thời lượng.*?:\s*', '', duration_text, flags=re.IGNORECASE)
                
                # LOẠI BỎ phần "Hình thức đào tạo" nếu có
                duration_text = re.sub(r'III\.\s*Hình thức.*', '', duration_text, flags=re.DOTALL | re.IGNORECASE)
                duration_text = re.sub(r'Hình thức đào tạo.*', '', duration_text, flags=re.DOTALL | re.IGNORECASE)
                
                break
        
        if duration_text:
            parts.append(f"Thời lượng:\n{duration_text}")
        
        result = "\n\n".join(parts) if parts else ""
        
        # Đảm bảo không trả về generic fallback text
        if not result or len(result.strip()) < 50:
            # Thử tìm bất kỳ text nào có ý nghĩa
            meaningful_patterns = [
                r'(?:khóa học|khoá học).*?(?:cung cấp|giúp|trang bị).*?(?=Mục tiêu|Đối tượng|\d+\.|$)',
                r'[A-Z][a-z]+ là.*?(?=Mục tiêu|Đối tượng|\d+\.|$)',
                r'Trong bối cảnh.*?(?=Mục tiêu|Đối tượng|\d+\.|$)'
            ]
            
            for pattern in meaningful_patterns:
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    result = f"Tổng quan khóa học:\n{match.group().strip()}"
                    break
        
        return result if result else "Thông tin giới thiệu và thời lượng khóa học."
    
    def _extract_precise_section2(self, text: str, raw_sections: Dict[str, str]) -> str:
        """Extract chính xác section 2: Mục tiêu + Đối tượng + Điều kiện - ENHANCED"""
        parts = []
        
        # 1. Tìm mục tiêu khóa học (flexible patterns)
        objectives_patterns = [
            r'IV\.\s*Mục tiêu.*?(?=V\.|VI\.|Đối tượng|$)',
            r'Mục tiêu khóa học.*?(?=V\.|Đối tượng|Điều kiện|$)',
            r'Kết thúc khóa học.*?(?=V\.|Đối tượng|$)',
            # Fallback: tìm bất kỳ text nào nói về mục tiêu
            r'.*?học viên.*?(?:nắm|hiểu|có thể|sẽ).*?(?=Đối tượng|Điều kiện|Nội dung|$)'
        ]
        
        objectives_text = ""
        for pattern in objectives_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                objectives_text = match.group().strip()
                objectives_text = re.sub(r'^IV\.\s*Mục tiêu.*?:\s*', '', objectives_text, flags=re.IGNORECASE)
                objectives_text = re.sub(r'^Mục tiêu.*?:\s*', '', objectives_text, flags=re.IGNORECASE)
                break
        
        if objectives_text:
            parts.append(f"Mục tiêu khóa học:\n{objectives_text}")
        
        # 2. Tìm đối tượng tham gia (enhanced patterns for various formats)
        audience_patterns = [
            r'III\.\s*Đối tượng.*?(?=IV\.|V\.|Yêu cầu|Điều kiện|Nội dung|$)',
            r'V\.\s*Đối tượng.*?(?=VI\.|VII\.|Điều kiện|Nội dung|$)',
            r'Đối tượng(?:\s+tham gia|\s+học)?.*?(?=IV\.|V\.|VI\.|Yêu cầu|Điều kiện|Nội dung|$)',
            # Special pattern for "Đối tượng học"
            r'Đối tượng học\s*:.*?(?=IV\.|V\.|Yêu cầu|Điều kiện|Nội dung|$)'
        ]
        
        audience_text = ""
        for pattern in audience_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                audience_text = match.group().strip()
                audience_text = re.sub(r'^(?:III\.|V\.)\s*Đối tượng.*?:\s*', '', audience_text, flags=re.IGNORECASE)
                audience_text = re.sub(r'^Đối tượng.*?:\s*', '', audience_text, flags=re.IGNORECASE)
                break
        
        if audience_text:
            parts.append(f"Đối tượng tham gia:\n{audience_text}")
        
        # 3. Tìm điều kiện tiên quyết/yêu cầu (enhanced patterns)
        prereq_patterns = [
            r'IV\.\s*(?:Yêu cầu|Điều kiện).*?(?=V\.|VI\.|Nội dung|$)',
            r'VI\.\s*Điều kiện.*?(?=VII\.|VIII\.|Nội dung|$)',
            r'(?:Điều kiện tiên quyết|Yêu cầu trước khóa học).*?(?=V\.|VI\.|VII\.|Nội dung|$)'
        ]
        
        prereq_text = ""
        for pattern in prereq_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                prereq_text = match.group().strip()
                prereq_text = re.sub(r'^(?:IV\.|VI\.)\s*(?:Điều kiện|Yêu cầu).*?:\s*', '', prereq_text, flags=re.IGNORECASE)
                prereq_text = re.sub(r'^(?:Điều kiện|Yêu cầu).*?:\s*', '', prereq_text, flags=re.IGNORECASE)
                break
        
        if prereq_text:
            parts.append(f"Điều kiện tiên quyết:\n{prereq_text}")
        
        result = "\n\n".join(parts) if parts else ""
        
        # Fallback nếu không tìm thấy gì
        if not result or len(result.strip()) < 50:
            # Tìm bất kỳ thông tin nào về đối tượng hoặc yêu cầu
            fallback_patterns = [
                r'.*?(?:Quản trị|Admin|Developer|Kỹ sư|Chuyên viên).*?(?=Nội dung|\d+\.|$)',
                r'.*?(?:kiến thức|kinh nghiệm|yêu cầu).*?(?:Linux|cơ bản|nền tảng).*?(?=Nội dung|\d+\.|$)'
            ]
            
            for pattern in fallback_patterns:
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    result = f"Đối tượng và yêu cầu:\n{match.group().strip()}"
                    break
        
        return result if result else "Thông tin mục tiêu và đối tượng khóa học."
    
    def _extract_precise_section3(self, text: str, raw_sections: Dict[str, str]) -> str:
        """Extract chính xác section 3: Nội dung khóa học - ENHANCED"""
        
        # Tìm nội dung khóa học với flexible patterns
        content_patterns = [
            r'V\.\s*Nội dung.*',  # Most common
            r'VI\.\s*Nội dung.*',  # Alternative numbering
            r'VII\.\s*Nội dung.*',  # If more sections before
            r'Nội dung khóa học.*',
            r'\d+\.\s*(?:Introduction|Tổng quan|Overview).*',  # First module
            r'Module\s*1.*',  # Module-based content
            r'Chương\s*1.*'  # Chapter-based content
        ]
        
        content_text = ""
        for pattern in content_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content_text = match.group().strip()
                # Clean section header
                content_text = re.sub(r'^(?:V\.|VI\.|VII\.)\s*Nội dung.*?:\s*', '', content_text, flags=re.IGNORECASE)
                content_text = re.sub(r'^Nội dung khóa học\s*:\s*', '', content_text, flags=re.IGNORECASE)
                break
        
        # Enhanced fallback - look for structured content
        if not content_text or len(content_text.strip()) < 100:
            # Look for numbered items/modules
            module_patterns = [
                r'1\.\s*.*?(?:\n2\.|$)',  # Look for "1. ..." patterns
                r'Module.*?1.*',
                r'Introduction to.*',
                r'Hadoop.*Installation.*',
                r'HDFS.*Components.*'
            ]
            
            for pattern in module_patterns:
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    # Try to capture more content after the match
                    start_pos = match.start()
                    remaining_text = text[start_pos:]
                    content_text = remaining_text[:1000]  # Take reasonable amount
                    break
        
        if content_text:
            return f"Nội dung khóa học:\n{content_text}"
        else:
            return "Nội dung khóa học: Thông tin chi tiết về chương trình học."
    
    def _extract_fallback_section1(self, text: str) -> str:
        """Fallback extraction cho section 1 (intro + duration)"""
        # Tìm các pattern cơ bản
        intro_patterns = [
            r"(?i)(?:tổng quan|giới thiệu|mô tả).*?(?=(?:thời lượng|mục tiêu|\n\n))",
            r"(?i)trong bối cảnh.*?(?=(?:thời lượng|mục tiêu|\n\n))"
        ]
        
        duration_patterns = [
            r"(?i)thời lượng.*?(?:giờ|ngày|tuần).*?(?=(?:mục tiêu|\n\n))",
            r"(?i)\d+\s*(?:giờ|ngày|tuần)"
        ]
        
        content_parts = []
        
        # Extract intro
        for pattern in intro_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content_parts.append(f"Tổng quan: {match.group().strip()}")
                break
        
        # Extract duration
        for pattern in duration_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content_parts.append(f"Thời lượng: {match.group().strip()}")
                break
        
        return "\n\n".join(content_parts) if content_parts else "Thông tin giới thiệu và thời lượng khóa học."
    
    def _extract_fallback_section2(self, text: str) -> str:
        """Fallback extraction cho section 2 (objectives + audience)"""
        objectives_patterns = [
            r"(?i)mục tiêu.*?(?=(?:đối tượng|nội dung|\n\n))",
            r"(?i)sau khóa học.*?(?=(?:đối tượng|nội dung|\n\n))"
        ]
        
        audience_patterns = [
            r"(?i)đối tượng.*?(?=(?:nội dung|điều kiện|\n\n))",
            r"(?i)học viên.*?(?=(?:nội dung|điều kiện|\n\n))"
        ]
        
        content_parts = []
        
        # Extract objectives
        for pattern in objectives_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content_parts.append(f"Mục tiêu: {match.group().strip()}")
                break
        
        # Extract audience
        for pattern in audience_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content_parts.append(f"Đối tượng: {match.group().strip()}")
                break
        
        return "\n\n".join(content_parts) if content_parts else "Thông tin mục tiêu và đối tượng khóa học."
    
    def _extract_fallback_section3(self, text: str) -> str:
        """Fallback extraction cho section 3 (content)"""
        content_patterns = [
            r"(?i)nội dung.*?(?:module|chương).*",
            r"(?i)chương trình.*",
            r"(?i)module\s*\d+.*"
        ]
        
        for pattern in content_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return f"Nội dung khóa học:\n{match.group().strip()}"
        
        return "Nội dung khóa học: Thông tin chi tiết về chương trình học."
    
    def extract_course_info(self, text: str) -> Dict[str, str]:
        """Extract thông tin khóa học thành chính xác 3 sections cố định"""
        if not text or len(text.strip()) < 100:
            return {}
        
        # Clean text first
        cleaned_text = self.text_cleaner.clean_text(text)
        
        # Extract các sections riêng lẻ trước
        raw_sections = {}
        for section_name in self.section_configs.keys():
            content = self.extract_section_content(cleaned_text, section_name)
            if content and len(content.strip()) > 30:
                raw_sections[section_name] = content
        
        # Tạo 3 sections cố định từ raw sections
        final_sections = self._create_fixed_sections(raw_sections, cleaned_text)
        
        return final_sections
