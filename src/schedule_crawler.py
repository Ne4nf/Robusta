"""
Web Crawler cho lịch khai giảng Robusta
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from typing import List, Dict

def crawl_robusta_schedule() -> str:
    """
    Crawl lịch khai giảng từ website robusta.vn
    Returns: String chứa thông tin lịch khai giảng
    """
    try:
        # URL của trang lịch khai giảng Robusta
        url = "https://robusta.vn/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tìm các element chứa thông tin lịch khai giảng
        schedule_info = []
        
        # Tìm các khóa học và ngày khai giảng
        # (Cần inspect website để tìm đúng selector)
        
        # Fallback: Tìm text có chứa từ khóa lịch khai giảng
        text_content = soup.get_text()
        
        # Tìm pattern ngày tháng (dd/mm/yyyy hoặc dd/mm)
        date_patterns = re.findall(r'\d{1,2}/\d{1,2}(?:/\d{4})?', text_content)
        
        if date_patterns:
            schedule_text = f"Lịch khai giảng gần nhất: {', '.join(date_patterns[:3])}"
        else:
            schedule_text = "Vui lòng liên hệ để biết lịch khai giảng chi tiết."
            
        return schedule_text
        
    except Exception as e:
        print(f"Error crawling schedule: {e}")
        return "Không thể lấy lịch khai giảng từ website. Vui lòng liên hệ Robusta để biết thông tin mới nhất."

def get_schedule_info(course_name: str = None) -> str:
    """
    Lấy thông tin lịch khai giảng cho khóa học cụ thể hoặc tổng quát
    """
    base_schedule = crawl_robusta_schedule()
    
    if course_name:
        return f"Lịch khai giảng khóa {course_name}: {base_schedule}"
    else:
        return f"Lịch khai giảng các khóa học: {base_schedule}"

# Test function
if __name__ == "__main__":
    schedule = crawl_robusta_schedule()
    print("Schedule:", schedule)
