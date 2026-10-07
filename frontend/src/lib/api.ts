// Kiểu dữ liệu và hàm gọi API backend.

export type CategoryId = "vn" | "crypto";

export interface Category {
  id: CategoryId;
  label: string;
  timeframes: string[];
}

export interface AssetSummary {
  category: CategoryId;
  symbol: string;
  display: string;
  name: string;
  exchange: string;
  price: number | null;
  change_pct: number | null;
  volume: number | null;
}

export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface InfoField {
  label: string;
  value: string | number | null;
  kind: "number" | "price" | "percent" | "text" | "date" | "volume";
}

export interface AssetInfo {
  category: CategoryId;
  symbol: string;
  display: string;
  name: string;
  exchange: string;
  currency: string;
  price: number | null;
  change: number | null;
  change_pct: number | null;
  fields: InfoField[];
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

async function get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const qs = params ? "?" + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])) : "";
  const res = await fetch(`/api${path}${qs}`);
  if (!res.ok) {
    let msg = `Lỗi ${res.status}`;
    try {
      msg = (await res.json()).detail ?? msg;
    } catch {
      /* phản hồi không phải JSON */
    }
    throw new ApiError(msg, res.status);
  }
  return res.json() as Promise<T>;
}

export const api = {
  categories: () => get<{ demo: boolean; categories: Category[] }>("/categories"),
  assets: (category: CategoryId) =>
    get<{ items: AssetSummary[] }>(`/assets/${category}`).then((r) => r.items),
  search: (q: string) => get<{ items: AssetSummary[] }>("/search", { q, limit: 20 }).then((r) => r.items),
  candles: (category: CategoryId, symbol: string, tf: string) =>
    get<{ candles: Candle[] }>(`/assets/${category}/${encodeURIComponent(symbol)}/candles`, { tf, limit: 500 }).then(
      (r) => r.candles,
    ),
  info: (category: CategoryId, symbol: string) =>
    get<AssetInfo>(`/assets/${category}/${encodeURIComponent(symbol)}/info`),
};
