import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Cấu hình API key của Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    # Nếu chưa có key thì dùng Mock
    pass

def analyze_spike(area: str, feedback_texts: list[str]) -> dict:
    """
    Gửi danh sách các phản hồi tiêu cực của một khu vực cho LLM (Groq API) để phân tích nguyên nhân gốc rễ.
    """
    # 1. Chuẩn bị dữ liệu đầu vào cho Prompt
    reviews_text = "\n".join([f"- {text}" for text in feedback_texts])
    
    # --- MOCK DATA: Nếu chưa có Groq Key, trả về dữ liệu giả lập để Demo ---
    if not GROQ_API_KEY or GROQ_API_KEY.strip() == "":
        print(f"[{area}] Chưa có GROQ_API_KEY. Đang dùng chế độ giả lập (Mock AI)...")
        time.sleep(1) # Giả lập thời gian AI xử lý
        return {
            "title": f"Bùng nổ phàn nàn tại {area}",
            "description": f"Tổng hợp {len(feedback_texts)} review: Khách hàng phản ánh gay gắt về thái độ phục vụ của nhân viên và chất lượng sản phẩm giảm sút trong giờ cao điểm.",
            "action": "Yêu cầu Quản lý khu vực xuống trực tiếp chi nhánh kiểm tra camera và chấn chỉnh đội ngũ ngay lập tức.",
            "assigned_team": "Vận hành & Đào tạo"
        }
    # -----------------------------------------------------------------------------------

    prompt = f"""
Bạn là một chuyên gia phân tích dữ liệu khách hàng (Customer Insights Analyst).
Hệ thống vừa phát hiện một lượng lớn phản hồi tiêu cực (Spike) tại khu vực: {area}.

Dưới đây là danh sách các phản hồi (reviews) thu thập được:
{reviews_text}

Nhiệm vụ của bạn:
1. Đọc kỹ các phản hồi trên và tìm ra nguyên nhân gốc rễ chung nhất (Root Cause).
2. Viết một tiêu đề (title) ngắn gọn, súc tích (dưới 10 từ) mô tả sự cố.
3. Đề xuất một hành động (action) cần thực hiện ngay lập tức để khắc phục.
4. Xác định phòng ban nào (assigned_team) cần chịu trách nhiệm xử lý (VD: Vận hành, Cửa hàng, IT, Giao hàng...).

YÊU CẦU BẮT BUỘC: Bạn CHỈ ĐƯỢC PHÉP trả về kết quả dưới dạng JSON theo đúng định dạng sau, không thêm bất kỳ văn bản giải thích nào khác ngoài JSON:
{{
  "title": "Tên sự cố ngắn gọn",
  "description": "Mô tả nguyên nhân gốc rễ một cách chuyên nghiệp",
  "action": "Đề xuất hành động khắc phục",
  "assigned_team": "Tên phòng ban xử lý"
}}
"""

    try:
        # Khởi tạo client Groq
        client = Groq(api_key=GROQ_API_KEY)
        model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
        
        # Ngủ 2 giây để tránh vượt giới hạn tốc độ miễn phí của Groq
        print(f"[{area}] Đang gọi AI ({model_name}) phân tích...")
        time.sleep(2)
        
        # Gọi mô hình của Groq
        response = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model=model_name,
            temperature=0.3,
            response_format={"type": "json_object"} # Ép trả về chuẩn JSON
        )
        
        # 3. Lấy nội dung trả về
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"Error calling LLM or parsing JSON: {e}")
        # Trả về JSON mặc định nếu có lỗi
        return {
            "title": f"Cảnh báo sự cố tại {area}",
            "description": f"Phát hiện {len(feedback_texts)} phản hồi tiêu cực. Không thể tự động phân tích chi tiết do lỗi LLM: {str(e)[:50]}...",
            "action": "Cần nhân viên CSKH kiểm tra thủ công ngay lập tức.",
            "assigned_team": "CSKH"
        }
