import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
from llm_agent import analyze_spike

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Thiếu cấu hình SUPABASE_URL hoặc SUPABASE_SERVICE_ROLE_KEY trong file .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SPIKE_THRESHOLD = 5  # Ngưỡng bùng nổ: >= 5 phản hồi tiêu cực cùng một khu vực

def detect_spikes():
    print("[Spike Detector] Đang quét hệ thống để tìm kiếm sự cố bùng nổ...")
    
    # Lấy dữ liệu trong vòng 1 giờ qua (để demo, bạn có thể chỉnh lại khoảng thời gian nếu cần)
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    
    # Lấy các feedback tiêu cực hoặc nguy hiểm (P4, P5)
    response = supabase.table("feedback") \
        .select("id, text, area, severity, topic") \
        .gte("created_at", one_hour_ago) \
        .in_("severity", ["P4", "P5"]) \
        .execute()
        
    data = response.data
    if not data:
        print("[Spike Detector] Không có feedback tiêu cực nào gần đây.")
        return {"spikes_detected": 0}
        
    # Gom nhóm theo khu vực (area)
    area_counts = {}
    area_texts = {}
    
    for row in data:
        area = row.get("area", "Unknown")
        text = row.get("text", "")
        
        if area not in area_counts:
            area_counts[area] = 0
            area_texts[area] = []
            
        area_counts[area] += 1
        area_texts[area].append(text)
        
    spikes_detected = 0
    
    for area, count in area_counts.items():
        if count >= SPIKE_THRESHOLD:
            print(f"🚨 PHÁT HIỆN SPIKE: Khu vực {area} có {count} phàn nàn nghiêm trọng!")
            spikes_detected += 1
            
            # Gửi cho LLM phân tích
            print(f"[{area}] Đang gửi dữ liệu cho AI (OpenRouter) phân tích...")
            alert_data = analyze_spike(area, area_texts[area])
            
            # Lấy 1 user_id bất kỳ làm admin tạo alert
            profiles_res = supabase.table("profiles").select("id").limit(1).execute()
            mock_user_id = profiles_res.data[0]["id"] if profiles_res.data else None
            
            # Lưu vào bảng alerts
            if mock_user_id:
                alert_payload = {
                    "user_id": mock_user_id,
                    "title": alert_data.get("title", f"Spike tại {area}"),
                    "description": alert_data.get("description", "Không có mô tả chi tiết") + f"\n\n**Action Plan:** {alert_data.get('action', '')}\n**Assigned Team:** {alert_data.get('assigned_team', '')}",
                    "severity": "P1", # Spike là sự cố nghiêm trọng
                    "area": area,
                    "status": "open"
                }
                
                try:
                    supabase.table("alerts").insert(alert_payload).execute()
                    print(f"✅ Đã tạo Alert khẩn cấp cho {area} thành công!")
                except Exception as e:
                    print(f"❌ Lỗi khi lưu Alert vào DB: {e}")
            else:
                print("❌ Không có user_id hợp lệ để lưu Alert!")
                
    return {"spikes_detected": spikes_detected}

if __name__ == "__main__":
    detect_spikes()
