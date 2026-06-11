# Hướng dẫn chạy Docker trên Windows và macOS

Tài liệu này dành cho người nhận source từ GitHub và muốn chạy toàn bộ hệ thống bằng Docker trên máy cá nhân.

Hệ thống gồm ba container:

- `backend`: FastAPI, Supabase, AI agent, live stream và ticket workflow.
- `ui`: giao diện TanStack Start.
- `gateway`: Nginx nối UI với backend trên cùng một URL.

## 1. Thông tin cần chuẩn bị

Người chạy cần có:

- Tài khoản GitHub để clone repo nếu repo là private.
- Docker Desktop.
- Git.
- Một project Supabase đã có schema phù hợp.
- Supabase URL, publishable key và service-role key.
- Ít nhất một AI key: OpenRouter, OpenAI, Gemini hoặc Groq.

Không cần cài Python, Node.js hoặc database local khi chạy bằng Docker.

## 2. Cài Docker trên Windows

### Yêu cầu

- Windows 10/11 64-bit.
- WSL 2 được bật.
- Virtualization được bật trong BIOS/UEFI.

### Cài đặt

1. Tải Docker Desktop từ `https://www.docker.com/products/docker-desktop/`.
2. Chạy installer và chọn backend WSL 2 khi được hỏi.
3. Restart Windows nếu installer yêu cầu.
4. Mở Docker Desktop và chờ trạng thái Docker Engine chuyển sang running.
5. Mở PowerShell và kiểm tra:

```powershell
docker --version
docker compose version
```

Nếu lệnh không tồn tại, đóng PowerShell, mở lại sau khi Docker Desktop đã chạy.

## 3. Cài Docker trên macOS

### Xác định loại CPU

Mở Terminal:

```bash
uname -m
```

- `arm64`: Apple Silicon, ví dụ M1/M2/M3/M4.
- `x86_64`: Mac Intel.

### Cài đặt

1. Tải đúng bản Docker Desktop cho Apple Silicon hoặc Intel từ `https://www.docker.com/products/docker-desktop/`.
2. Kéo Docker vào Applications và mở Docker Desktop.
3. Chờ Docker Engine chạy xong.
4. Kiểm tra:

```bash
docker --version
docker compose version
```

## 4. Clone repo

### Windows PowerShell

```powershell
git clone https://github.com/Kez-DE/xanh_iu.git
Set-Location xanh_iu
```

### macOS Terminal

```bash
git clone https://github.com/Kez-DE/xanh_iu.git
cd xanh_iu
```

Tất cả lệnh tiếp theo phải chạy trong thư mục chứa `compose.yaml`.

## 5. Tạo file `.env`

File `.env` không có trên GitHub vì chứa secret. Mỗi người phải tạo từ `.env.example`.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
notepad .env
```

### macOS Terminal

```bash
cp .env.example .env
open -e .env
```

Có thể dùng VS Code:

```bash
code .env
```

## 6. Điền cấu hình `.env`

Các giá trị tối thiểu cần thay:

```env
SUPABASE_PROJECT_ID=your_project_id
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_publishable_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

VITE_SUPABASE_PROJECT_ID=your_project_id
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your_publishable_key
```

Chọn ít nhất một AI provider. Ví dụ OpenRouter:

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL_NAME=openrouter/owl-alpha
```

Hoặc để tự chọn provider có key:

```env
LLM_PROVIDER=auto
```

Port Docker mặc định:

```env
BACKEND_PORT=8000
UI_PORT=5174
DOCKER_PUBLIC_BACKEND_URL=
```

Nên để `DOCKER_PUBLIC_BACKEND_URL` trống. Gateway sẽ tự chuyển request `/api` vào backend.

Không gửi `.env` lên GitHub, email công khai hoặc nhóm chat. Mỗi người nên sử dụng key riêng.

## 7. Build và chạy lần đầu

Lệnh giống nhau trên PowerShell và Terminal:

```bash
docker compose up --build -d
```

Lần đầu có thể mất vài phút vì Docker phải tải base image và dependencies.

Kiểm tra trạng thái:

```bash
docker compose ps
```

Kết quả đúng là `backend`, `ui` và `gateway` đều có trạng thái `healthy` hoặc `Up`.

Xem log trong lúc khởi động:

```bash
docker compose logs -f
```

Nhấn `Ctrl+C` để thoát màn hình log. Container vẫn tiếp tục chạy vì lệnh khởi động có `-d`.

## 8. Mở hệ thống

Với port mặc định:

```text
UI              http://localhost:5174
Live Feedback   http://localhost:5174/feedback
Ticket Triage   http://localhost:5174/alerts
AI Chat         http://localhost:5174/chat
Swagger API     http://localhost:5174/docs
Backend direct  http://localhost:8000
```

Đăng ký hoặc đăng nhập ít nhất một tài khoản trên UI. Backend cần một profile hợp lệ để gắn `user_id` khi ingest dataset và tạo ticket.

## 9. Bật live stream

Có hai cách.

### Tự bật khi Docker khởi động

Đặt trong `.env`:

```env
LIVE_STREAM_ENABLED=true
LIVE_STREAM_BATCH_SIZE=150
LIVE_STREAM_INTERVAL_SECONDS=1
LIVE_STREAM_LOOP=true
AUTO_TICKET_ENABLED=true
AUTO_TICKET_EVERY_BATCHES=10
```

Sau khi sửa `.env`:

```bash
docker compose up -d --force-recreate backend
```

### Bật bằng API trên Windows PowerShell

PowerShell có alias riêng cho `curl`, vì vậy nên dùng `Invoke-RestMethod`:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:5174/api/live-stream/start?batch_size=150&interval_seconds=1&loop=true&reset=true&auto_ticket=true&ticket_every_batches=10&ticket_max_spikes=1"
```

### Bật bằng API trên macOS

```bash
curl -X POST "http://localhost:5174/api/live-stream/start?batch_size=150&interval_seconds=1&loop=true&reset=true&auto_ticket=true&ticket_every_batches=10&ticket_max_spikes=1"
```

Kiểm tra stream trên Windows:

```powershell
Invoke-RestMethod -Uri "http://localhost:5174/api/live-stream/status"
```

Kiểm tra stream trên macOS:

```bash
curl "http://localhost:5174/api/live-stream/status"
```

## 10. Dừng và chạy lại

### Dừng và xóa container/network

```bash
docker compose down
```

Lệnh này không xóa image đã build, source code hoặc `.env`.

Chạy lại mà không build:

```bash
docker compose up -d
```

### Chỉ tạm dừng

```bash
docker compose stop
```

Chạy lại container đã dừng:

```bash
docker compose start
```

### Restart

```bash
docker compose restart
```

## 11. Cập nhật code mới từ GitHub

```bash
git pull origin main
docker compose up --build -d
```

Phải dùng `--build` nếu source, dependency, Dockerfile hoặc biến `VITE_*` thay đổi.

## 12. Đổi port khi bị trùng

Nếu báo port đã được sử dụng, sửa `.env`:

```env
BACKEND_PORT=8100
UI_PORT=5274
```

Sau đó chạy lại:

```bash
docker compose down
docker compose up -d
```

URL mới sẽ là:

```text
http://localhost:5274
```

### Kiểm tra port trên Windows

```powershell
Get-NetTCPConnection -LocalPort 5174 -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

### Kiểm tra port trên macOS

```bash
lsof -nP -iTCP:5174 -sTCP:LISTEN
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

## 13. Truy cập từ máy khác trong cùng mạng

1. Tìm IP LAN của máy chạy Docker.
2. Cho phép firewall nhận kết nối vào `UI_PORT`.
3. Máy khác mở `http://<IP-LAN>:<UI_PORT>`.

### Tìm IP trên Windows

```powershell
ipconfig
```

Tìm dòng `IPv4 Address` của Wi-Fi hoặc Ethernet.

### Tìm IP trên macOS

```bash
ipconfig getifaddr en0
```

Nếu dùng Ethernet, interface có thể khác `en0`.

Chỉ cần public `UI_PORT` vì gateway đã chuyển `/api` vào backend. Không nên mở service-role key hoặc file `.env` cho người truy cập.

## 14. Xử lý lỗi thường gặp

### Docker daemon chưa chạy

Lỗi thường có nội dung `Cannot connect to the Docker daemon`.

Giải pháp: mở Docker Desktop và chờ Docker Engine chạy xong.

### Container không healthy

```bash
docker compose ps
docker compose logs backend
docker compose logs ui
docker compose logs gateway
```

### Không thấy live feedback

Kiểm tra:

```text
http://localhost:<UI_PORT>/api/live-stream/status
```

Các trường cần xem: `running`, `last_result`, `last_error`, `ticket_running` và `last_ticket_error`.

### Không tạo ticket

- Dataset phải có ít nhất 5 feedback `P2-P5` cùng khu vực.
- `AUTO_TICKET_ENABLED` phải là `true`.
- Cần chờ đủ số batch trong `AUTO_TICKET_EVERY_BATCHES`.
- AI provider phải có key hợp lệ.

### Chỉ thấy ticket chờ xử lý

Workflow mặc định:

- Chờ xử lý khoảng 10 giây.
- Đang xử lý khoảng 45 giây.
- Sau đó chuyển sang đã xong.

Kiểm tra:

```text
http://localhost:<UI_PORT>/api/alerts/workflow-status
```

### Thay Supabase hoặc biến `VITE_*`

Các biến `VITE_*` được đưa vào UI trong lúc build. Sau khi thay chúng phải chạy:

```bash
docker compose up --build -d
```

## 15. Khác biệt kiến trúc CPU

Nếu clone source và chạy `docker compose up --build`, Docker tự build image đúng kiến trúc máy hiện tại.

Nếu nhận file image `.tar`:

- Image build trên Apple Silicon thường là `linux/arm64`.
- Máy Windows Intel/AMD và Mac Intel thường cần `linux/amd64`.
- Image sai kiến trúc có thể chạy qua giả lập nhưng chậm, hoặc không chạy.

Cách ít lỗi nhất là gửi source/GitHub để người nhận tự build. Nếu cần gửi image, hãy tạo image đa kiến trúc hoặc xuất đúng image cho loại CPU của máy nhận.

## 16. Xóa dữ liệu Docker khi cần làm sạch

Xóa container và network của repo:

```bash
docker compose down
```

Xóa thêm image do Compose build:

```bash
docker compose down --rmi local
```

Không dùng `docker system prune -a` nếu không hiểu rõ tác động vì lệnh đó có thể xóa image/cache của các dự án Docker khác.
