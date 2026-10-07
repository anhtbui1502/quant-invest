// Lưu lựa chọn (danh mục, mã, khung) trên URL để tải lại trang / chia sẻ link vẫn giữ nguyên.
import { useCallback, useEffect, useState } from "react";
import type { CategoryId } from "./api";

export interface ViewState {
  category: CategoryId;
  symbol: string | null;
  timeframe: string;
}

function read(): ViewState {
  const p = new URLSearchParams(window.location.search);
  const c = p.get("c");
  return {
    category: c === "crypto" ? "crypto" : "vn",
    symbol: p.get("s"),
    timeframe: p.get("tf") ?? "1d",
  };
}

export function useViewState() {
  const [state, setState] = useState<ViewState>(read);

  useEffect(() => {
    const p = new URLSearchParams();
    p.set("c", state.category);
    if (state.symbol) p.set("s", state.symbol);
    p.set("tf", state.timeframe);
    window.history.replaceState(null, "", `?${p}`);
  }, [state]);

  const update = useCallback((patch: Partial<ViewState>) => setState((s) => ({ ...s, ...patch })), []);
  return [state, update] as const;
}
