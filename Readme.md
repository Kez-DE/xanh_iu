# Hướng dẫn sử dụng và vận hành hệ thống

Tài liệu này hướng dẫn cài đặt, cấu hình, chạy và theo dõi toàn bộ repo **AI Quality Intelligence Platform**.

Để đóng gói và chạy bằng container, xem [DOCKER.md](./DOCKER.md). Hướng dẫn chi tiết cho máy người nhận trên Windows và macOS nằm tại [DOCKER_WINDOWS_MAC.md](./DOCKER_WINDOWS_MAC.md).

## 1. Tổng quan hệ thống

Repo gồm ba phần chính:

```text
xanh_iu/
├── UI/                         # React + TanStack Start + Vite
├── backend/pipeline/           # FastAPI, ingest, agent, spike detector
├── data/                       # Dataset thật dùng cho live stream
├── .env                        # Cấu hình dùng chung, không commit
├── .env.example                # Mẫu cấu hình dùng chung
└── .gitignore                  # Quy tắc ignore dùng chung
```

URL và port không cố định giữa các máy. Trong tài liệu này dùng các biến đại diện:

```bash
export BACKEND_HOST=127.0.0.1
export BACKEND_PORT=8000
export UI_HOST=127.0.0.1
export UI_PORT=5174

export BACKEND_URL="http://${BACKEND_HOST}:${BACKEND_PORT}"
export UI_URL="http://${UI_HOST}:${UI_PORT}"
```

Các đường dẫn dịch vụ được suy ra như sau:

| Dịch vụ | Địa chỉ |
|---|---|
| UI | `${UI_URL}` |
| Backend API | `${BACKEND_URL}` |
| Swagger API | `${BACKEND_URL}/docs` |
| Live Feedback | `${UI_URL}/feedback` |
| Ticket Triage | `${UI_URL}/alerts` |
| AI Chat | `${UI_URL}/chat` |

`127.0.0.1:8000` và `127.0.0.1:5174` chỉ là ví dụ local, không phải cấu hình bắt buộc của repo. Mỗi người phải thay host, port hoặc domain theo môi trường của mình.

## 2. Yêu cầu môi trường

- Python 3.10 trở lên.
- Node.js 20 trở lên và npm.
- Một project Supabase có các bảng `profiles`, `feedback`, `alerts` và cấu hình Auth.
- Ít nhất một API key model nếu muốn dùng AI thật: OpenRouter, OpenAI, Gemini hoặc Groq.

## 3. Cài đặt lần đầu

Chạy từ thư mục gốc của repo.

### Backend

```bash
python3 -m venv backend/pipeline/.venv
backend/pipeline/.venv/bin/pip install -r backend/pipeline/requirements.txt
```

### UI

```bash
cd UI
npm install
cd ..
```

### Cấu hình môi trường

```bash
cp .env.example .env
```

Chỉ sử dụng một file `.env` tại thư mục gốc. Không tạo `.env` riêng trong `UI/` hoặc `backend/`.

Các biến Supabase bắt buộc:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your_publishable_key
```

`SUPABASE_SERVICE_ROLE_KEY` chỉ được dùng ở backend. Không đặt service-role key vào biến bắt đầu bằng `VITE_` vì các biến này có thể xuất hiện trong bundle trình duyệt.

Khai báo URL backend mà UI có thể truy cập:

```env
# Thay bằng URL mà backend thực tế đang phục vụ.
BACKEND_API_URL=http://YOUR_BACKEND_HOST:YOUR_BACKEND_PORT
VITE_BACKEND_API_URL=http://YOUR_BACKEND_HOST:YOUR_BACKEND_PORT
```

Khi deploy, dùng URL public thật, ví dụ:

```env
BACKEND_API_URL=https://api.example.com
VITE_BACKEND_API_URL=https://api.example.com
OPENROUTER_SITE_URL=https://app.example.com
```

Không dùng `127.0.0.1` hoặc `localhost` trong cấu hình frontend production vì trình duyệt người dùng sẽ hiểu đó là máy của chính họ.

## 4. Cấu hình AI Agent

Hệ thống tự chọn provider đầu tiên có key theo thứ tự:

```text
OpenRouter -> OpenAI -> Gemini -> Groq -> mock
```

Cấu hình tự động:

```env
LLM_PROVIDER=auto

OPENROUTER_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
```

Để ép dùng một provider cụ thể:

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL_NAME=openrouter/owl-alpha
```

Các giá trị hợp lệ của `LLM_PROVIDER` là `auto`, `openrouter`, `openai`, `gemini`, `groq`, `mock`.

Kiểm tra provider đang được sử dụng:

```bash
curl "${BACKEND_URL}/api/agent/status"
```

Xem log agent gần nhất:

```bash
curl "${BACKEND_URL}/api/agent/logs?limit=50"
```

Log được ghi tại `backend/pipeline/logs/agent.log` và đã được `.gitignore` loại khỏi Git.

## 5. Chạy hệ thống

Mở hai terminal tại thư mục gốc. Trước tiên chọn host và port phù hợp với máy:

```bash
export BACKEND_HOST=127.0.0.1
export BACKEND_PORT=8000
export UI_HOST=127.0.0.1
export UI_PORT=5174
export BACKEND_URL="http://${BACKEND_HOST}:${BACKEND_PORT}"
export UI_URL="http://${UI_HOST}:${UI_PORT}"
```

Có thể đổi `8000` hoặc `5174` sang port trống khác. Các giá trị trên chỉ là một cấu hình mẫu.

Biến được `export` chỉ tồn tại trong terminal hiện tại. Hãy khai báo lại các biến cần dùng trong mỗi terminal, hoặc thay trực tiếp `$BACKEND_HOST`, `$BACKEND_PORT`, `$UI_HOST`, `$UI_PORT` bằng giá trị đã chọn.

Đồng thời cập nhật URL backend trong `.env` trước khi chạy UI:

```env
BACKEND_API_URL=http://YOUR_BACKEND_HOST:YOUR_BACKEND_PORT
VITE_BACKEND_API_URL=http://YOUR_BACKEND_HOST:YOUR_BACKEND_PORT
```

Ví dụ, nếu backend của một thành viên chạy tại `10.0.0.25:9100`, cả hai biến trên phải trỏ tới `http://10.0.0.25:9100`.

### Terminal 1: Backend

```bash
cd backend/pipeline
.venv/bin/uvicorn main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
```

Kiểm tra backend:

```bash
curl "${BACKEND_URL}/health"
```

Kết quả mong đợi:

```json
{"status":"ok","message":"Backend service is running"}
```

### Terminal 2: UI

```bash
cd UI
npm run dev -- --host "$UI_HOST" --port "$UI_PORT"
```

Mở URL được in trong terminal hoặc `${UI_URL}`, sau đó đăng ký hoặc đăng nhập tài khoản Supabase trước khi sử dụng các trang được bảo vệ.

### Truy cập từ máy khác trong cùng mạng LAN

Backend và UI cần bind trên mọi interface:

```bash
export BACKEND_HOST=0.0.0.0
export BACKEND_PORT=8000
export UI_HOST=0.0.0.0
export UI_PORT=5174
```

Trong `.env`, đặt URL backend bằng IP LAN của máy chạy server, không dùng `0.0.0.0` làm URL truy cập:

```env
BACKEND_API_URL=http://192.168.1.20:8000
VITE_BACKEND_API_URL=http://192.168.1.20:8000
```

Người dùng khác sẽ mở `http://192.168.1.20:5174`. Thay `192.168.1.20` bằng IP thật của máy chủ và mở firewall cho các port đã chọn nếu cần.

## 6. Luồng xử lý dữ liệu

```text
Dataset thật trong /data
        |
        v
ingest.py đọc từng batch
        |
        v
Làm sạch nội dung và dùng nhãn có sẵn
hoặc classifier nếu bản ghi chưa có nhãn
        |
        v
Ghi feedback vào Supabase bằng service-role key
        |
        v
UI polling backend và hiển thị review mới với hiệu ứng lướt
        |
        v
Sau mỗi N batch, spike_detector quét P2-P5 theo khu vực
        |
        v
AI Agent phân tích nguyên nhân, hành động, phòng ban
        |
        v
Tạo ticket trong bảng alerts
        |
        v
open -> in_progress -> resolved
```

Dataset mặc định:

```text
data/processed/seed_real_clean (1).json
```

Có thể đổi file bằng biến:

```env
REAL_DATA_FILE=/absolute/path/to/dataset.json
```

## 7. Live Feedback Stream

### Bật thủ công

```bash
curl -X POST "${BACKEND_URL}/api/live-stream/start?batch_size=150&interval_seconds=1&loop=true&reset=true&auto_ticket=true&ticket_every_batches=10&ticket_max_spikes=1"
```

Ý nghĩa tham số:

| Tham số | Ý nghĩa |
|---|---|
| `batch_size=150` | Tối đa 150 review mỗi batch |
| `interval_seconds=1` | Chạy một batch mỗi giây |
| `loop=true` | Đọc lại từ đầu khi hết dataset |
| `reset=true` | Đưa offset và bộ đếm batch về 0 |
| `auto_ticket=true` | Bật phát hiện spike và sinh ticket |
| `ticket_every_batches=10` | Quét spike sau mỗi 10 batch |
| `ticket_max_spikes=1` | Tạo tối đa một ticket trong mỗi lần quét |

Kiểm tra trạng thái:

```bash
curl "${BACKEND_URL}/api/live-stream/status"
```

Các trường quan trọng:

- `running`: stream còn chạy hay không.
- `offset`: vị trí hiện tại trong dataset.
- `batches_ingested`: tổng số batch đã nạp.
- `last_result`: tốc độ và kết quả batch gần nhất.
- `ticket_running`: agent đang phân tích ticket hay không.
- `last_ticket_result`: số spike và ticket tạo gần nhất.
- `last_ticket_error`: lỗi auto-ticket gần nhất.

Dừng stream:

```bash
curl -X POST "${BACKEND_URL}/api/live-stream/stop"
```

### Tự chạy khi backend khởi động

Đặt trong `.env`:

```env
LIVE_STREAM_ENABLED=true
LIVE_STREAM_BATCH_SIZE=150
LIVE_STREAM_INTERVAL_SECONDS=1
LIVE_STREAM_LOOP=true
LIVE_STREAM_RESET_ON_START=false

AUTO_TICKET_ENABLED=true
AUTO_TICKET_EVERY_BATCHES=10
AUTO_TICKET_MAX_FEEDBACK=1000
AUTO_TICKET_MAX_SPIKES=1
```

Không nên đặt `LIVE_STREAM_RESET_ON_START=true` trên môi trường vận hành lâu dài nếu không muốn backend đọc lại dataset từ đầu sau mỗi lần restart.

## 8. Auto Ticket và vòng đời xử lý

Spike detector đọc các feedback mức `P2-P5` trong khoảng thời gian gần nhất, nhóm theo khu vực và kích hoạt khi một khu vực đạt ngưỡng spike. Ticket nhận mức severity cao nhất trong nhóm; `P5` là nghiêm trọng nhất.

Ticket mới được tạo với trạng thái:

```text
open (Chờ xử lý)
  -> in_progress (Đang xử lý)
  -> resolved (Đã xong)
```

Workflow tự động mặc định:

```env
AUTO_TICKET_WORKFLOW_ENABLED=true
AUTO_TICKET_IN_PROGRESS_AFTER_SECONDS=10
AUTO_TICKET_RESOLVED_AFTER_SECONDS=55
```

- Sau 10 giây, ticket chuyển từ `open` sang `in_progress`.
- Ticket ở trạng thái `in_progress` khoảng 45 giây, rồi chuyển sang `resolved` khi tổng thời gian kể từ lúc tạo đạt 55 giây.
- Scheduler kiểm tra workflow mỗi 5 giây.
- Người dùng vẫn có thể bấm xử lý thủ công trên trang Ticket Triage.

Kiểm tra workflow:

```bash
curl "${BACKEND_URL}/api/alerts/workflow-status"
```

Ép quét spike thủ công:

```bash
curl -X POST "${BACKEND_URL}/api/trigger-spike-detect?max_feedback=1000&max_spikes=1"
```

## 9. AI Chat trong UI

Trang `/chat` gửi hội thoại đến `POST /api/agent/chat`.

Backend tự bổ sung context gồm:

- 300 feedback gần nhất.
- 20 alerts gần nhất.
- Thống kê severity, sentiment, topic và khu vực.
- Trạng thái live stream hiện tại.

Agent có thể trả lời về spike, chất lượng vận hành, ticket triage và hành động ưu tiên. Nếu không có key AI, provider `mock` chỉ phù hợp kiểm tra kết nối, không dùng cho phân tích thật.

## 10. Chạy pipeline một lần

Nạp một batch dữ liệu thật:

```bash
curl -X POST "${BACKEND_URL}/api/ingest-real-dataset?limit=150&batch_size=150&offset=0"
```

Chạy ingest và spike detection trong cùng một request:

```bash
curl -X POST "${BACKEND_URL}/api/run-real-pipeline?limit=150&batch_size=150&max_feedback=1000&max_spikes=1"
```

Luồng một lần phù hợp cho kiểm thử. Live stream phù hợp cho màn hình vận hành liên tục.

## 11. Kiểm tra trước khi deploy

### Backend

```bash
backend/pipeline/.venv/bin/python -m py_compile \
  backend/pipeline/main.py \
  backend/pipeline/ingest.py \
  backend/pipeline/spike_detector.py \
  backend/pipeline/agent/model_router.py
```

### UI

```bash
cd UI
npm run build
```

Build thành công sẽ tạo output trong `UI/dist/`. Thư mục này không được commit.

## 12. Dừng hệ thống

Nhấn `Ctrl+C` trong hai terminal đang chạy backend và UI.

Nếu cần dừng theo port trên macOS/Linux:

```bash
kill $(lsof -tiTCP:"$BACKEND_PORT" -sTCP:LISTEN)
kill $(lsof -tiTCP:"$UI_PORT" -sTCP:LISTEN)
```

## 13. Xử lý lỗi thường gặp

### UI không kết nối backend

Kiểm tra:

```env
VITE_BACKEND_API_URL=https://your-backend-domain.example.com
```

Sau khi đổi `.env`, restart UI.

### Không thấy live feedback

1. Kiểm tra `/health`.
2. Kiểm tra `/api/live-stream/status` có `running=true`.
3. Kiểm tra `last_error` và `last_result`.
4. Kiểm tra `SUPABASE_SERVICE_ROLE_KEY`.
5. Mở `/feedback` và chờ polling khoảng một giây.

### Không sinh auto-ticket

1. Kiểm tra `auto_ticket=true`.
2. Chờ đủ `ticket_every_batches`.
3. Kiểm tra dataset có ít nhất 5 feedback `P2-P5` theo cùng khu vực.
4. Kiểm tra `/api/agent/status` có provider và key hợp lệ.
5. Kiểm tra `last_ticket_error` trong stream status.

### Chỉ thấy ticket chờ xử lý

Kiểm tra:

```bash
curl "${BACKEND_URL}/api/alerts/workflow-status"
```

Đảm bảo `enabled=true` và `last_error=null`. Chờ ít nhất thời gian được cấu hình trong `AUTO_TICKET_IN_PROGRESS_AFTER_SECONDS` và `AUTO_TICKET_RESOLVED_AFTER_SECONDS`.

### Backend báo thiếu user

Dataset ingest cần một `user_id` hợp lệ vì bảng `feedback` tham chiếu người dùng. Hãy đăng ký ít nhất một tài khoản trên UI để bảng `profiles` có bản ghi.

### Lỗi quyền Supabase hoặc RLS

- Backend phải dùng `SUPABASE_SERVICE_ROLE_KEY`.
- UI chỉ dùng publishable key.
- Không đưa service-role key vào source code hoặc Git.

## 14. Quy trình vận hành đề xuất

1. Khởi động backend và kiểm tra `/health`.
2. Kiểm tra `/api/agent/status` để xác nhận model provider.
3. Khởi động UI và đăng nhập.
4. Bật live stream hoặc dùng `LIVE_STREAM_ENABLED=true`.
5. Theo dõi review tại `/feedback`.
6. Theo dõi auto-ticket tại `/alerts`.
7. Kiểm tra `last_error` khi tốc độ ingest giảm hoặc ticket không sinh.
8. Dừng stream trước khi bảo trì hoặc thay dataset.

Với cấu hình mặc định, hệ thống ingest tối đa 150 review mỗi giây. Tốc độ thực tế phụ thuộc mạng và giới hạn ghi của Supabase. Không nên tăng batch hoặc tần suất gọi agent trước khi theo dõi ổn định latency, lỗi ghi và quota của model provider.
