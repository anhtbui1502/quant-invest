#!/usr/bin/env bash
# Cài đặt và chạy Quant Invest bằng một lệnh.
#
#   ./run.sh           cài đặt (nếu cần), kiểm tra nguồn dữ liệu, chạy web ở cổng 8000
#   ./run.sh --demo    chạy với dữ liệu giả lập (không cần mạng)
#   ./run.sh --check   chỉ kiểm tra kết nối tới nguồn dữ liệu thật
#
# Biến môi trường: PORT (mặc định 8000).
set -euo pipefail

cd "$(dirname "$0")"
PORT="${PORT:-8000}"
MODE="${1:-}"

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }

command -v python3 >/dev/null || { echo "Chưa cài Python 3. Cài tại https://www.python.org/downloads/"; exit 1; }
command -v npm >/dev/null || { echo "Chưa cài Node.js. Cài tại https://nodejs.org/"; exit 1; }

step "Cài thư viện Python"
python3 -m pip install --quiet --disable-pip-version-check -r requirements.txt

step "Cài thư viện giao diện"
(cd frontend && npm install --no-fund --no-audit --loglevel=error)

step "Build giao diện"
(cd frontend && npm run build --silent)

if [[ "$MODE" == "--demo" ]]; then
  export DEMO_MODE=1
  echo "Chế độ DEMO: dùng dữ liệu giả lập."
else
  step "Kiểm tra nguồn dữ liệu thật"
  python3 -m scripts.check_sources || true
  [[ "$MODE" == "--check" ]] && exit 0
fi

step "Chạy web tại http://localhost:${PORT}  (Ctrl+C để dừng)"
echo "Trên Codespaces: bấm 'Open in Browser' ở thông báo góc phải dưới, hoặc mở tab PORTS."
exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT"
