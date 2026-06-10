import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from clean import clean_text
from classifier import predict_feedback

# Load biến môi trường từ file .env ở thư mục gốc (xanh_iu)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Thiếu cấu hình SUPABASE_URL hoặc SUPABASE_SERVICE_ROLE_KEY trong file .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def ingest_demo_data(json_path: str):
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return {"success": False, "error": "File not found"}
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    inserted_count = 0
    
    # Lấy 1 user_id bất kỳ trong bảng profiles để làm mock_user_id (vì bảng feedback yêu cầu user_id NOT NULL)
    profiles_res = supabase.table("profiles").select("id").limit(1).execute()
    mock_user_id = None
    if profiles_res.data:
        mock_user_id = profiles_res.data[0]["id"]
    else:
        print("Lỗi: Không tìm thấy bất kỳ tài khoản nào trong hệ thống. Hãy đăng ký 1 tài khoản trên Frontend trước!")
        return {"success": False, "error": "No user found"}
    
    records_to_process = data[:150]
    
    for row in records_to_process:
        try:
            raw_text = row.get("text", "")
            if not raw_text:
                continue
                
            cleaned_text = clean_text(raw_text)
            prediction = predict_feedback(cleaned_text)
            
            # Map dữ liệu khớp chuẩn schema của bảng public.feedback
            payload = {
                "user_id": mock_user_id,
                "text": cleaned_text,
                "topic": prediction["topic"],
                "sentiment": prediction["sentiment"],
                "severity": f"P{prediction['severity']}",
                "confidence": prediction["confidence"],
                "area": row.get("area", "Unknown"),
                "source": row.get("source", "app_store"),
                "channel": "app"
            }
            
            supabase.table("feedback").insert(payload).execute()
            inserted_count += 1
            
        except Exception as e:
            print(f"Error inserting row: {e}")
            
    print(f"Successfully processed and inserted {inserted_count} records into Supabase!")
    return {"success": True, "inserted": inserted_count}

if __name__ == "__main__":
    demo_file = os.path.join(os.path.dirname(__file__), "..", "..", "AI223_crawled_reviews_5000", "enriched", "seed_demo_150_enriched_locations.json")
    ingest_demo_data(demo_file)
