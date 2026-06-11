# Chạy và phân phối hệ thống bằng Docker

Người nhận chạy trên Windows hoặc macOS xem hướng dẫn từng bước tại [DOCKER_WINDOWS_MAC.md](./DOCKER_WINDOWS_MAC.md).

Docker Compose đóng gói hệ thống thành ba service:

| Service | Vai trò |
|---|---|
| `backend` | FastAPI, ingest dataset, AI agent, live stream và ticket workflow |
| `ui` | TanStack Start production server |
| `gateway` | Nginx public gateway, chuyển `/api` vào backend và các route còn lại vào UI |

Gateway giúp cùng một image UI chạy trên nhiều máy/IP/domain mà không phải đóng cứng URL backend vào bundle.

## 1. Yêu cầu

- Docker Engine hoặc Docker Desktop.
- Docker Compose v2 trở lên.
- File `.env` ở thư mục gốc.
- Supabase đã có các bảng và ít nhất một tài khoản/profile.

Kiểm tra Docker:

```bash
docker --version
docker compose version
```

## 2. Cấu hình

```bash
cp .env.example .env
```

Điền Supabase và ít nhất một model key vào `.env`.

Các biến Docker quan trọng:

```env
# Port được mở trên máy host, có thể đổi tùy máy.
BACKEND_PORT=8000
UI_PORT=5174

# Để trống khi dùng gateway cùng origin.
DOCKER_PUBLIC_BACKEND_URL=

# Tên image local hoặc image trên registry.
BACKEND_IMAGE=ai-quality-backend:local
UI_IMAGE=ai-quality-ui:local
```

Khi `DOCKER_PUBLIC_BACKEND_URL` để trống, trình duyệt gọi `${UI_URL}/api/...`; Nginx tự chuyển request vào backend. Đây là cấu hình nên dùng khi gửi container cho người khác.

Không đưa `.env` chứa key thật vào image, Git hoặc file tar. Người nhận phải tự tạo `.env` của họ.

## 3. Build và chạy

Từ thư mục gốc:

```bash
docker compose up --build -d
```

Kiểm tra container:

```bash
docker compose ps
docker compose logs -f
```

URL phụ thuộc host và port của từng máy:

```text
UI              http://<HOST>:<UI_PORT>
Live Feedback   http://<HOST>:<UI_PORT>/feedback
Ticket Triage   http://<HOST>:<UI_PORT>/alerts
AI Chat         http://<HOST>:<UI_PORT>/chat
Swagger         http://<HOST>:<UI_PORT>/docs
Backend direct  http://<HOST>:<BACKEND_PORT>
```

Ví dụ nếu máy chạy Docker có IP `192.168.1.20` và `UI_PORT=5174`, người khác trong LAN truy cập `http://192.168.1.20:5174`.

## 4. Lệnh vận hành

Xem log từng service:

```bash
docker compose logs -f backend
docker compose logs -f ui
docker compose logs -f gateway
```

Restart:

```bash
docker compose restart
```

Tắt nhưng giữ image:

```bash
docker compose down
```

Build lại sau khi sửa code hoặc đổi biến `VITE_*`:

```bash
docker compose up --build -d
```

Bật live stream:

```bash
curl -X POST "http://<HOST>:<UI_PORT>/api/live-stream/start?batch_size=150&interval_seconds=1&loop=true&reset=true&auto_ticket=true&ticket_every_batches=10&ticket_max_spikes=1"
```

Hoặc đặt `LIVE_STREAM_ENABLED=true` trong `.env` để backend tự bật stream khi container khởi động.

## 5. Gửi cho người khác bằng file image tar

Máy build:

```bash
docker compose build
docker pull nginx:1.27-alpine
docker save \
  ai-quality-backend:local \
  ai-quality-ui:local \
  nginx:1.27-alpine \
  -o ai-quality-intelligence-images.tar
```

Gửi cho người nhận các file:

```text
ai-quality-intelligence-images.tar
compose.yaml
docker/nginx.conf
.env.example
```

Máy nhận:

```bash
docker load -i ai-quality-intelligence-images.tar
cp .env.example .env
# Điền key và chọn port trong .env
docker compose up --no-build -d
```

Dataset mặc định đã nằm trong backend image. Nếu thay dataset hoặc code, cần build và xuất lại image backend.

## 6. Push lên Docker Hub hoặc GHCR

Ví dụ với Docker Hub account `yourname`:

```bash
export BACKEND_IMAGE=yourname/ai-quality-backend:1.0.0
export UI_IMAGE=yourname/ai-quality-ui:1.0.0

docker compose build
docker login
docker push "$BACKEND_IMAGE"
docker push "$UI_IMAGE"
```

Người nhận đặt cùng tên image trong `.env`:

```env
BACKEND_IMAGE=yourname/ai-quality-backend:1.0.0
UI_IMAGE=yourname/ai-quality-ui:1.0.0
```

Sau đó chạy:

```bash
docker compose pull
docker compose up --no-build -d
```

Với GitHub Container Registry, tên image thường có dạng:

```text
ghcr.io/<github-user-or-org>/ai-quality-backend:1.0.0
ghcr.io/<github-user-or-org>/ai-quality-ui:1.0.0
```

## 7. Deploy lên VPS

1. Cài Docker trên VPS.
2. Copy `compose.yaml`, `docker/nginx.conf` và `.env` lên VPS.
3. Dùng image registry hoặc build trực tiếp từ source.
4. Mở firewall cho `UI_PORT`; chỉ mở `BACKEND_PORT` nếu cần truy cập backend trực tiếp.
5. Với domain và HTTPS, đặt thêm reverse proxy như Caddy, Traefik hoặc Nginx phía trước gateway.

Trong production nên chỉ public gateway. Có thể xóa phần `ports` của service `backend` trong `compose.yaml` để backend chỉ hoạt động trong Docker network.

## 8. Kiểm tra lỗi

Xem trạng thái và healthcheck:

```bash
docker compose ps
docker inspect --format='{{json .State.Health}}' ai-quality-intelligence-backend-1
```

Backend không healthy:

```bash
docker compose logs backend
```

UI không gọi được API:

```bash
curl "http://<HOST>:<UI_PORT>/health"
curl "http://<HOST>:<UI_PORT>/api/live-stream/status"
```

Không kết nối Supabase:

- Kiểm tra `SUPABASE_URL` và `SUPABASE_SERVICE_ROLE_KEY`.
- Kiểm tra `VITE_SUPABASE_URL` và `VITE_SUPABASE_PUBLISHABLE_KEY`.
- Không dùng service-role key cho biến `VITE_*`.

Đổi `VITE_SUPABASE_*` hoặc `DOCKER_PUBLIC_BACKEND_URL` cần rebuild image UI vì đây là biến build-time của Vite.
