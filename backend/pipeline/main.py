from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

from ingest import ingest_demo_data

# Hàm chạy định kỳ giả lập Real-time
def scheduled_data_fetch():
    print("[APScheduler] Simulating fetch of new feedback data...")
    # Tương lai có thể cắm logic quét từ AppStore/PlayStore vào đây
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi chạy Scheduler khi startup
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_data_fetch, 'interval', minutes=5)
    scheduler.start()
    print("APScheduler started successfully. Running every 5 minutes.")
    yield
    # Tắt Scheduler khi shutdown
    scheduler.shutdown()

app = FastAPI(
    title="AI Quality Intelligence Platform API",
    description="Backend API for Smart Mobility Feedback Analytics",
    version="1.0.0",
    lifespan=lifespan
)

# CORS config to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Quality Intelligence API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend service is running"}

@app.post("/api/trigger-demo-batch")
def trigger_demo_batch():
    """
    Endpoint dùng cho Demo Day: Bắn toàn bộ 150 dữ liệu đánh giá vào Database ngay lập tức
    để mô phỏng một Spike (bùng nổ feedback) ở Cầu Giấy.
    """
    demo_file = os.path.join(os.path.dirname(__file__), "..", "..", "AI223_crawled_reviews_5000", "enriched", "seed_demo_150_enriched_locations.json")
    result = ingest_demo_data(demo_file)
    if result["success"]:
        return {"status": "success", "message": f"Đã chèn thành công {result['inserted']} bản ghi."}
    else:
        return {"status": "error", "message": result["error"]}

@app.post("/api/trigger-spike-detect")
def trigger_spike_detect():
    """
    Endpoint để kích hoạt thủ công tiến trình Spike Detection
    """
    from spike_detector import detect_spikes
    result = detect_spikes()
    return {"status": "success", "data": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
