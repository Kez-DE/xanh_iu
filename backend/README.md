# 🧠 Backend — AI Quality Intelligence Platform

Đây là tài liệu kỹ thuật dành cho các thành viên trong nhóm **AI20K-223** phụ trách phần Backend của dự án **xanhSM AI Quality Intelligence Platform**.

> **Dự án:** Hệ thống phân tích phản hồi khách hàng thời gian thực cho Hãng gọi xe công nghệ.  
> **Phiên bản:** 1.1 · Cập nhật: 06/2025

---

## 📁 Cấu trúc thư mục

```
backend/
├── pipeline/
│   ├── main.py              # 🚀 Server FastAPI chính — điểm vào của hệ thống
│   ├── clean.py             # 🧹 Làm sạch & bảo vệ thông tin riêng tư (PII)
│   ├── classifier.py        # 🤖 Phân loại AI (ML model) + Rule-based Safety
│   ├── ingest.py            # 💾 Đẩy dữ liệu đã xử lý vào Supabase
│   ├── spike_detector.py    # 🔥 Phát hiện bùng nổ phản hồi tiêu cực (Spike)
│   ├── llm_agent.py         # 💬 Gọi Groq AI (Llama 3.3) phân tích & sinh Alert
│   ├── requirements.txt     # 📦 Danh sách thư viện Python
│   └── ml/
│       ├── topic_model.joblib       # Model phân loại Chủ đề (Topic)
│       ├── sentiment_model.joblib   # Model phân tích Cảm xúc (Sentiment)
│       └── taxonomy/
│           └── safety_keywords.json # Từ khóa Rule-based Safety
├── data/
│   ├── raw/                 # Dữ liệu thô từ nguồn
│   ├── processed/           # Dữ liệu đã xử lý, sẵn sàng đưa vào model
│   └── train/               # Tập dữ liệu train/test đã label
└── .env                     # 🔑 API Keys (KHÔNG commit file này lên Git!)
```

---

## ⚙️ Cài đặt & Chạy Local

### Bước 1: Cài đặt Python & các thư viện

Yêu cầu: **Python 3.10+**

```bash
# Di chuyển vào thư mục pipeline
cd backend/pipeline

# Cài đặt tất cả thư viện cần thiết
pip install -r requirements.txt
```

### Bước 2: Cấu hình file `.env`

Tạo file `.env` trong thư mục `backend/` (copy từ `.env.example` nếu có):

```env
# === SUPABASE ===
VITE_SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>   # Key có quyền ghi/xóa dữ liệu

# === GROQ AI (Model Llama 3.3) ===
GROQ_API_KEY=gsk_...                            # Lấy tại console.groq.com
GROQ_MODEL_NAME=llama-3.3-70b-versatile        # Có thể đổi model khác tại đây
```

> ⚠️ **Quan trọng:** Không bao giờ commit file `.env` lên GitHub. File này đã được thêm vào `.gitignore`.

### Bước 3: Chạy server

```bash
cd backend/pipeline
python main.py
```

Server sẽ chạy tại: **http://localhost:8000**

Swagger UI (giao diện test API): **http://localhost:8000/docs**

---

## 🔄 Luồng dữ liệu (Data Flow)

```
Dữ liệu thô (150 reviews)
        │
        ▼
  [1] clean.py
  → Làm sạch text, xóa ký tự đặc biệt
  → Ẩn SĐT (→ [SĐT]) và Email (→ [EMAIL]) bằng Regex
        │
        ▼
  [2] classifier.py
  → Dự đoán Chủ đề (Topic): Tài xế / Xe / App / Giá / An toàn / Khác
  → Dự đoán Cảm xúc (Sentiment): positive / negative / neutral
  → Rule-based Safety: Nếu có từ khóa "tai nạn", "ngộ độc" → override severity = P5
        │
        ▼
  [3] ingest.py
  → Ghi toàn bộ dữ liệu đã nhãn vào bảng `feedback` trên Supabase
        │
        ▼
  [4] spike_detector.py
  → Group By theo Area (khu vực)
  → Đếm số feedback tiêu cực (P4, P5) trong 1 giờ qua
  → Nếu ≥ 5 case/khu vực → Kích hoạt SPIKE 🚨
        │
        ▼
  [5] llm_agent.py (Groq API — Llama 3.3 70B)
  → Đọc toàn bộ feedback của khu vực bị Spike
  → Phân tích nguyên nhân gốc rễ (Root Cause)
  → Đề xuất hành động khắc phục
  → Gán phòng ban chịu trách nhiệm (Vận Hành / CSKH / Safety / IT)
        │
        ▼
  [6] Lưu Alert vào bảng `alerts` trên Supabase
  → Frontend hiện thị Ticket tự động trên Dashboard
```

---

## 🌐 Danh sách API Endpoints

Server FastAPI chạy tại `http://localhost:8000`. Xem đầy đủ tại `/docs`.

---

### `GET /health`
Kiểm tra server còn sống không.

**Response:**
```json
{
  "status": "ok",
  "message": "Backend service is running"
}
```

---

### `POST /api/trigger-demo-batch`
**🎯 Dùng cho Demo Day!** Bắn 150 review giả lập vào database để kích hoạt Spike.

**Cách gọi (curl):**
```bash
curl -X POST http://localhost:8000/api/trigger-demo-batch
```

**Cách gọi (Python):**
```python
import requests
res = requests.post("http://localhost:8000/api/trigger-demo-batch")
print(res.json())
```

**Response thành công:**
```json
{
  "status": "success",
  "message": "Đã chèn thành công 150 bản ghi."
}
```

**Kết quả:** 150 bản ghi xuất hiện trong bảng `feedback` trên Supabase, tập trung dày đặc ở khu vực `HN-Cau-Giay` để tạo Spike.

---

### `POST /api/trigger-spike-detect`
**🎯 Dùng cho Demo Day!** Ép hệ thống quét Spike ngay lập tức (thay vì chờ định kỳ).

**Cách gọi (curl):**
```bash
curl -X POST http://localhost:8000/api/trigger-spike-detect
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "spikes_detected": 13
  }
}
```

**Kết quả:** AI (Llama 3.3) tự động phân tích 13 khu vực bị Spike → Sinh 13 Alert đỏ xuất hiện trên Dashboard của Frontend.

---

## 🧪 Chạy thủ công từng bước (Debug)

Nếu cần test từng module riêng lẻ:

```bash
cd backend/pipeline

# Test kết nối Supabase
python test_db.py

# Chỉ chạy bước phát hiện Spike + gọi AI (không cần chạy cả server)
python spike_detector.py
```

---

## 📊 Cấu trúc Database (Supabase)

Hệ thống sử dụng 4 bảng chính trên Supabase (PostgreSQL):

| Bảng | Mô tả | File tương tác |
|------|-------|---------------|
| `feedback` | Lưu toàn bộ phản hồi đã phân loại | `ingest.py` |
| `alerts` | Lưu các Ticket/Alert AI sinh ra | `spike_detector.py` |
| `profiles` | Thông tin tài khoản người dùng | Auth |
| `chat_messages` | Lịch sử chat với AI Assistant | Frontend |

### Schema bảng `feedback`
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `id` | uuid | ID tự động |
| `text` | text | Nội dung phản hồi (đã mask PII) |
| `area` | text | Khu vực (VD: `HN-Cau-Giay`) |
| `topic` | text | Chủ đề AI phân loại (VD: `Tài xế`) |
| `sentiment` | text | Cảm xúc: `positive/negative/neutral` |
| `severity` | text | Mức độ: `P1` (nhẹ) → `P5` (nguy hiểm) |
| `channel` | text | Nguồn: `app/hotline/survey` |
| `created_at` | timestamp | Thời điểm ghi nhận |

### Schema bảng `alerts`
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `id` | uuid | ID tự động |
| `title` | text | Tiêu đề Ticket (AI sinh) |
| `description` | text | Nguyên nhân gốc rễ + Hành động + Phòng ban |
| `severity` | text | Luôn là `P1` (Spike = Khẩn cấp) |
| `area` | text | Khu vực bị Spike |
| `status` | text | `open → in_progress → resolved` |
| `created_at` | timestamp | Thời điểm phát hiện |

---

## 🤖 Cấu hình AI (Groq — Llama 3.3)

Hệ thống dùng **Groq API** (siêu nhanh, miễn phí) thay vì Claude/OpenAI để tối ưu chi phí.

- **Model:** `llama-3.3-70b-versatile` (Meta Llama 3.3, 70 tỷ tham số)
- **Tốc độ:** ~200 token/giây (cực nhanh)
- **Giới hạn miễn phí:** 14,400 requests/ngày
- **Thay đổi model:** Chỉ cần sửa `GROQ_MODEL_NAME` trong file `.env`, không cần sửa code

**Lấy API Key miễn phí:** [console.groq.com](https://console.groq.com)

---

## 🔄 APScheduler — Tự động hóa

Server FastAPI tích hợp sẵn **APScheduler** để giả lập hệ thống chạy Real-time.

Hiện tại scheduler chạy mỗi 5 phút để kiểm tra dữ liệu mới. Để kích hoạt Spike Detection tự động định kỳ, thêm vào `main.py`:

```python
from spike_detector import detect_spikes
scheduler.add_job(detect_spikes, 'interval', minutes=10)
```

---

## 🚨 Kịch bản Demo Day (5 phút)

1. **Bật server:** `python main.py`
2. **Mở Swagger UI:** `http://localhost:8000/docs`
3. **Gọi `/api/trigger-demo-batch`** → 150 reviews đổ vào DB
4. **Gọi `/api/trigger-spike-detect`** → AI phân tích, sinh 13 Ticket 🔴
5. **Mở Frontend** → Dashboard đỏ rực, Ticket Triage hiện đầy đủ theo phòng ban
6. **Demo Human-in-the-loop** → Sửa 1 nhãn sai của AI trên trang Phản hồi

---

## 👥 Phân công & Liên hệ

| Module | Phụ trách |
|--------|-----------|
| `clean.py`, `classifier.py` | Data/NLP Team |
| `ingest.py`, `main.py` | Backend Team |
| `spike_detector.py`, `llm_agent.py` | AI Agent Team |
| Database schema, Supabase | Backend Team |

---

*Tài liệu này được sinh tự động và cập nhật theo tiến độ dự án. Mọi thắc mắc, liên hệ team Backend.*
