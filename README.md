# Quant Invest

Web tra cứu tài sản đầu tư: tìm kiếm, xem biểu đồ nến và thông tin cơ bản.

**Giai đoạn 1** gồm 2 danh mục:

| Danh mục | Phạm vi | Nguồn dữ liệu |
|---|---|---|
| CK Việt Nam | Cổ phiếu niêm yết HOSE, HNX, UPCoM | VNDirect (API công khai) |
| Crypto | Các cặp spot `/USDT` trên Binance | Binance (API công khai) |

Tính năng:
- Tìm kiếm nhanh cả hai danh mục (Ctrl K / ⌘K, gõ không dấu được).
- Tab danh mục, danh sách mã có giá và % thay đổi, lọc theo sàn.
- Biểu đồ nến kèm khối lượng. Khung thời gian CK VN: 1m, 5m, 15m, 1H, 1D, 1W. Crypto có thêm 4H.
- Thông tin cơ bản. Cổ phiếu: giá tham chiếu, trần, sàn, KL khớp, đỉnh/đáy 52 tuần, ngày niêm yết… Crypto: cao/thấp 24h, khối lượng, giá trị giao dịch…
- Tự làm mới dữ liệu mỗi 15–60 giây.

> Dữ liệu chỉ mang tính tham khảo, có thể chậm so với bảng giá chính thức.
> API của VNDirect và Binance là API công khai miễn phí, không có cam kết dịch vụ.

## Cấu trúc

```
backend/            Python + FastAPI
  app/main.py         các API /api/... và phục vụ giao diện đã build
  app/providers/      mỗi nguồn dữ liệu một file: vndirect.py, binance.py, demo.py
frontend/           React + TypeScript + Vite + Tailwind + shadcn/ui + Lightweight Charts
  src/features/       search, asset-list, chart, asset-detail
tests/              test backend (dùng dữ liệu mẫu, không cần mạng)
scripts/            check_sources.py: kiểm tra kết nối tới nguồn dữ liệu thật
```

## Cài đặt (lần đầu)

Cần cài sẵn **Python 3.11+** và **Node.js 20+**.

```bash
# 1. Thư viện Python
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Build giao diện
cd frontend
npm install
npm run build
cd ..
```

## Chạy

```bash
python -m uvicorn backend.app.main:app --port 8000
```

Mở trình duyệt tại **http://localhost:8000**.

Chạy với dữ liệu giả lập (không cần mạng):

```bash
# macOS / Linux
DEMO_MODE=1 python -m uvicorn backend.app.main:app --port 8000
# Windows (PowerShell)
$env:DEMO_MODE=1; python -m uvicorn backend.app.main:app --port 8000
```

## Kiểm tra nguồn dữ liệu thật

```bash
python -m scripts.check_sources
```

Lệnh này gọi Binance và VNDirect rồi in OK / LỖI cho từng bước. Nếu Binance báo lỗi 451 hoặc 403 (chặn theo khu vực), app tự thử domain dự phòng `data-api.binance.vision`.

## Phát triển giao diện

Chạy backend và giao diện ở hai cửa sổ terminal. Sửa code giao diện thì trình duyệt tự cập nhật:

```bash
python -m uvicorn backend.app.main:app --port 8000 --reload   # cửa sổ 1
cd frontend && npm run dev                                     # cửa sổ 2, mở http://localhost:5173
```

## Test

```bash
python -m pytest            # backend
cd frontend && npm run typecheck
```

## API

| Đường dẫn | Mô tả |
|---|---|
| `GET /api/categories` | Danh mục và khung thời gian hỗ trợ |
| `GET /api/assets/{vn\|crypto}` | Danh sách mã kèm giá |
| `GET /api/search?q=...` | Tìm kiếm cả hai danh mục |
| `GET /api/assets/{cat}/{symbol}/candles?tf=1d` | Dữ liệu nến |
| `GET /api/assets/{cat}/{symbol}/info` | Thông tin cơ bản |

## Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `DEMO_MODE` | tắt | `1` = dùng dữ liệu giả lập |
| `BINANCE_BASE_URLS` | `https://api.binance.com,https://data-api.binance.vision` | Các domain Binance, thử lần lượt |
| `VNDIRECT_FINFO_URL` | `https://finfo-api.vndirect.com.vn/v4` | API danh sách mã và giá |
| `VNDIRECT_CHART_URL` | `https://dchart-api.vndirect.com.vn/dchart/history` | API nến |
