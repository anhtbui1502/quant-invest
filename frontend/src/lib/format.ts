// Định dạng số theo kiểu Việt Nam (dấu chấm phân cách nghìn, dấu phẩy thập phân).
import type { CategoryId } from "./api";

const vi = (opts: Intl.NumberFormatOptions) => new Intl.NumberFormat("vi-VN", opts);

/** Số chữ số thập phân hợp lý cho một mức giá crypto. */
export function cryptoDecimals(price: number): number {
  const p = Math.abs(price);
  if (p >= 1000) return 2;
  if (p >= 1) return 4;
  if (p === 0) return 2;
  // Giá rất nhỏ (VD PEPE 0,00000912): giữ 4 chữ số có nghĩa.
  return Math.min(10, Math.ceil(-Math.log10(p)) + 3);
}

export function formatPrice(value: number | null | undefined, category: CategoryId): string {
  if (value == null || Number.isNaN(value)) return "—";
  if (category === "vn") return vi({ maximumFractionDigits: 0 }).format(value);
  const d = cryptoDecimals(value);
  return vi({ minimumFractionDigits: Math.min(d, 2), maximumFractionDigits: d }).format(value);
}

export function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const s = vi({ minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
  return (value > 0 ? "+" : "") + s + "%";
}

/** Số lớn rút gọn: 1,2 tỷ / 345,6 tr / 12,3 N. */
export function formatCompact(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const a = Math.abs(value);
  const f = vi({ maximumFractionDigits: 1 });
  if (a >= 1e9) return f.format(value / 1e9) + " tỷ";
  if (a >= 1e6) return f.format(value / 1e6) + " tr";
  if (a >= 1e3) return f.format(value / 1e3) + " N";
  return f.format(value);
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return vi({ maximumFractionDigits: 2 }).format(value);
}

export function formatDate(value: string | number | null | undefined): string {
  if (!value) return "—";
  const d = new Date(String(value).slice(0, 10) + "T00:00:00");
  return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleDateString("vi-VN");
}

/** Màu theo hướng thay đổi giá. */
export function trendClass(value: number | null | undefined): string {
  if (value == null || value === 0) return "text-flat";
  return value > 0 ? "text-up" : "text-down";
}

export const TIMEFRAME_LABELS: Record<string, string> = {
  "1m": "1 phút",
  "5m": "5 phút",
  "15m": "15 phút",
  "1h": "1 giờ",
  "4h": "4 giờ",
  "1d": "1 ngày",
  "1w": "1 tuần",
};
