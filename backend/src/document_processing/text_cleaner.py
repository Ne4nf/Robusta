"""
Text Cleaner Module
Handles text preprocessing and cleaning for course documents
"""

import re
import logging

logger = logging.getLogger(__name__)

class TextCleaner:
    """Clean và normalize text với logic chuẩn cho course documents"""
    
    def __init__(self):
        # Patterns để loại bỏ thông tin nhiễu công ty - ENHANCED
        self.company_noise_patterns = [
            # Company headers và footers
            r'Trụ sở chính.*?(?=\n[A-ZÀÁẢÃẠ]|\n\n|$)',
            r'Chi nhánh.*?(?=\n[A-ZÀÁẢÃẠ]|\n\n|$)',
            r'Head Office.*?(?=\n[A-ZÀÁẢÃẠ]|\n\n|$)',
            r'Hanoi Office.*?(?=\n[A-ZÀÁẢÃẠ]|\n\n|$)',
            
            # Address patterns
            r'Lầu \d+.*?(?=\n[A-ZÀÁẢÃẠ]|\n\n|$)',
            r'Tầng \d+.*?(?=\n[A-ZÀÁẢÃẠ]|\n\n|$)',
            r'\d+-\d+-\d+\s+.*?Quận.*?(?=\n|$)',
            r'Quận \d+.*?Tp\.?\s*Hồ Chí Minh.*?(?=\n|$)',
            r'P\.\s*.*?Q\.\s*.*?Hà Nội.*?(?=\n|$)',
            r'Dist\.\s*\d+.*?HCM.*?(?=\n|$)',
            r'Dong Da Dist.*?Hanoi.*?(?=\n|$)',
            
            # Contact info
            r'Website:.*?(?=\n|$)',
            r'Email:.*?(?=\n|$)',
            r'Hotline:.*?(?=\n|$)',
            r'Tel:.*?(?=\n|$)',
            r'Phone:.*?(?=\n|$)',
            r'\|\s*Hotline:.*?(?=\n|$)',
            r'\+84.*?\d{3}.*?\d{3}.*?(?=\n|$)',
            r'www\.Robusta\.vn.*?(?=\n|$)',
            r'Learn@Robusta\.vn.*?(?=\n|$)',
            
            # Page numbers và metadata
            r'Page \d+ of \d+.*?(?=\n|$)',
            r'www\.Robusta\.vn\s+Page.*?(?=\n|$)',
            r'Trang \d+.*?(?=\n|$)',
            r'©.*?(?=\n|$)',
            
            # Multi-line company blocks
            r'Trụ sở chính.*?www\.Robusta\.vn',
            r'Chi nhánh.*?Learn@Robusta\.vn',
            
            # Company name mentions
            r'ROBUSTA.*?(?=\n|$)',
            r'Robusta.*?Technology.*?(?=\n|$)',
        ]
    
    def fix_vietnamese_encoding(self, text: str) -> str:
        """Fix common Vietnamese encoding issues in PDF extraction - ENHANCED"""
        if not text:
            return ""
        
        # Fix spaced Vietnamese diacritics - More comprehensive
        fixes = {
            # Common spaced words
            'h ọc': 'học', 'gi ảng': 'giảng', 'vi ện': 'viện',
            'cơ b ản': 'cơ bản', 'đào t ạo': 'đào tạo', 'hệ th ống': 'hệ thống',
            'công ngh ệ': 'công nghệ', 'ki ến th ức': 'kiến thức', 'ứng d ụng': 'ứng dụng',
            'quản tr ị': 'quản trị', 'th ực hiện': 'thực hiện', 'phát tri ển': 'phát triển',
            
            # Additional problematic patterns
            'ngư ời': 'người', 'd ự án': 'dự án', 'đ ể': 'để', 'c ần': 'cần',
            'gi ờ': 'giờ', 'đ ề': 'đề', 'c ấp': 'cấp', 'c ách': 'cách',
            'c ó th ể': 'có thể', 'c ung c ấp': 'cung cấp', 'ph ương pháp': 'phương pháp',
            'c ông c ụ': 'công cụ', 'ph ân tích': 'phân tích', 'd ữ liệu': 'dữ liệu',
            'b ằng c ách': 'bằng cách', 'gi ải quy ết': 'giải quyết', 'yêu c ầu': 'yêu cầu',
            'liên quan đ ến': 'liên quan đến', 'ki nh doanh': 'kinh doanh',
            'nh ững': 'những', 'căn b ản': 'căn bản', 'g ồm': 'gồm',
            'đư ợc': 'được', 'c ách th ức': 'cách thức', 'áp d ụng': 'áp dụng',
            'th ực t ế': 'thực tế', 'môi trư ờng': 'môi trường', 'k ỹ thu ật': 'kỹ thuật',
            'cu ối': 'cuối', 'v ới': 'với', 'gi ải quy ết': 'giải quyết',
            'ch ứng ch ỉ': 'chứng chỉ', 'c ài đ ặt': 'cài đặt', 'tri ển khai': 'triển khai',
            'c ấu hình': 'cấu hình', 'ph ục v ụ': 'phục vụ', 'ph át tri ển': 'phát triển',
        }
        
        fixed_text = text
        for wrong, correct in fixes.items():
            fixed_text = fixed_text.replace(wrong, correct)
        
        # Generic fix for spaced Vietnamese characters - More patterns
        patterns = [
            (r'([a-zA-ZÀ-ỹ])\s+([ọệấởảắằẳẵặ])', r'\1\2'),
            (r'([a-zA-ZÀ-ỹ])\s+([ụũúùűùử])', r'\1\2'),
            (r'([a-zA-ZÀ-ỹ])\s+([ịĩíìỉ])', r'\1\2'),
            (r'([a-zA-ZÀ-ỹ])\s+([ỗốồổộ])', r'\1\2'),
            (r'([a-zA-ZÀ-ỹ])\s+([ỹýỳỷỵ])', r'\1\2'),
        ]
        
        for pattern, replacement in patterns:
            fixed_text = re.sub(pattern, replacement, fixed_text)
        
        return fixed_text
    
    def remove_company_noise(self, text: str) -> str:
        """Remove company information but preserve course content - SMART MODE"""
        cleaned = text
        
        # FIRST: Identify and preserve course content sections
        course_content_patterns = [
            r'I\.\s*Giới thiệu.*?(?=Trụ sở|Chi nhánh|$)',
            r'II\.\s*Thời lượng.*?(?=Trụ sở|Chi nhánh|$)',
            r'III\.\s*Mục tiêu.*?(?=Trụ sở|Chi nhánh|$)',
            r'IV\.\s*Đối tượng.*?(?=Trụ sở|Chi nhánh|$)',
            r'V\.\s*Yêu cầu.*?(?=Trụ sở|Chi nhánh|$)',
            r'VI\.\s*Nội dung.*?(?=Trụ sở|Chi nhánh|$)',
            r'Khóa học.*?(?=Trụ sở|Chi nhánh|$)',
            r'(?:Module|Chương)\s*\d+.*?(?=Trụ sở|Chi nhánh|$)',
        ]
        
        preserved_content = []
        for pattern in course_content_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            preserved_content.extend(matches)
        
        # SECOND: Remove company blocks (aggressive on company info only)
        company_blocks = [
            r'Ho Chi Minh.*?City Head Office.*?www\.Robusta\.vn',
            r'Trụ sở chính.*?www\.Robusta\.vn',
            r'Chi nhánh.*?Learn@Robusta\.vn',
            r'Hanoi\s+Office.*?www\.Robusta\.vn',
        ]
        
        for pattern in company_blocks:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # THIRD: Remove individual company patterns but preserve course keywords
        for pattern in self.company_noise_patterns:
            # Only remove if the line doesn't contain course keywords
            def replace_if_not_course(match):
                matched_text = match.group(0)
                course_keywords = [
                    'khóa học', 'course', 'mục tiêu', 'objectives', 'giới thiệu',
                    'nội dung', 'content', 'học viên', 'students', 'yêu cầu',
                    'VMware', 'NSX', 'BigData', 'Cloud', 'thời lượng', 'duration'
                ]
                
                # If contains course keywords, keep it
                for keyword in course_keywords:
                    if keyword.lower() in matched_text.lower():
                        return matched_text
                
                # Otherwise remove
                return ''
            
            cleaned = re.sub(pattern, replace_if_not_course, cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # FOURTH: Line-by-line filtering with course content protection
        lines = cleaned.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Always preserve lines with course structure indicators
            course_structure_keywords = [
                r'I\.\s*Giới thiệu', r'II\.\s*Thời lượng', r'III\.\s*Mục tiêu',
                r'IV\.\s*Đối tượng', r'V\.\s*Yêu cầu', r'VI\.\s*Nội dung',
                r'Khóa học', r'Course', r'Module\s*\d+', r'Chương\s*\d+',
                r'VMware', r'NSX', r'BigData', r'Cloud', r'OpenStack'
            ]
            
            has_course_content = any(re.search(pattern, line, re.IGNORECASE) 
                                   for pattern in course_structure_keywords)
            
            if has_course_content:
                clean_lines.append(line)
                continue
                
            # Check against isolated company patterns only if no course content
            isolated_patterns = [
                r'^.*?(?:Head Office|Chi nhánh|Trụ sở).*?$',
                r'^.*?(?:\+84|\(\+84\)).*?$',
                r'^.*?(?:Tel:|Phone:|Hotline:).*?$',
                r'^.*?(?:Website:|Email:).*?$',
                r'^.*?(?:www\.Robusta|Learn@Robusta).*?$',
                r'^.*?(?:97-99-101|Lane 167|Tây Sơn).*?$',
                r'^.*?(?:Dist\.|Quận|HCM City|Hà Nội).*?$',
            ]
            
            skip_line = False
            for pattern in isolated_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    skip_line = True
                    break
            
            if not skip_line:
                clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize spacing and line breaks"""
        # Multiple spaces -> single space
        text = re.sub(r'\s+', ' ', text)
        # Multiple newlines -> double newline max
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        # Remove spaces after newlines
        text = re.sub(r'\n\s+', '\n', text)
        return text
    
    def standardize_formatting(self, text: str) -> str:
        """Standardize bullet points and numbering"""
        # Standardize bullet points
        text = re.sub(r'•\s*', '• ', text)
        # Standardize numbering
        text = re.sub(r'(\d+)\.\s*', r'\1. ', text)
        return text
    
    def remove_incomplete_lines(self, text: str) -> str:
        """Remove lines that appear to be incomplete or cut off"""
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip very short lines that don't end properly
            if len(line) < 10:
                continue
                
            # Skip lines ending with incomplete words (no punctuation)
            if len(line) > 20 and not re.search(r'[\.!?\)\:]$', line) and line.endswith('...'):
                continue
                
            clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def clean_text(self, text: str) -> str:
        """Main cleaning function - applies all cleaning steps"""
        if not text:
            return ""
        
        # Step 1: Fix encoding issues
        text = self.fix_vietnamese_encoding(text)
        
        # Step 2: Remove company noise
        text = self.remove_company_noise(text)
        
        # Step 3: Remove non-text characters (keep Vietnamese)
        text = re.sub(r'[^\w\sÀ-ỹ\n\.\,\!\?\-\•\:\(\)]', ' ', text, flags=re.UNICODE)
        
        # Step 4: Normalize whitespace
        text = self.normalize_whitespace(text)
        
        # Step 5: Standardize formatting
        text = self.standardize_formatting(text)
        
        # Step 6: Remove incomplete lines
        text = self.remove_incomplete_lines(text)
        
        return text.strip()
