import os
import sys

# Thêm đường dẫn để có thể import các module
sys.path.append(os.path.dirname(__file__))

from ingest import ingest_demo_data
from spike_detector import detect_spikes

def run_demo():
    print("=== BẮT ĐẦU DEMO TUẦN 3: SPIKE DETECTION & LLM AGENT ===\n")
    
    # Bước 1: Bắn dữ liệu mô phỏng (tương đương với việc có 1 lượng lớn review dồn về)
    print("1. Bắn 150 review vào hệ thống (giả lập lưu lượng giờ cao điểm)...")
    demo_file = os.path.join(os.path.dirname(__file__), "..", "..", "AI223_crawled_reviews_5000", "enriched", "seed_demo_150_enriched_locations.json")
    ingest_result = ingest_demo_data(demo_file)
    print(f"-> Kết quả Ingest: {ingest_result}\n")
    
    # Bước 2: Kích hoạt Spike Detector
    print("2. Chạy Spike Detector để tìm kiếm điểm nóng (Spike)...")
    spike_result = detect_spikes()
    print(f"-> Kết quả Spike Detector: {spike_result}\n")
    
    print("=== HOÀN TẤT DEMO ===")
    print("Hãy vào kiểm tra bảng `alerts` trên Supabase để xem kết quả do AI (OpenRouter) sinh ra!")

if __name__ == "__main__":
    run_demo()
