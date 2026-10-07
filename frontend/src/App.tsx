import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { AssetDetail } from "@/features/asset-detail/AssetDetail";
import { AssetList } from "@/features/asset-list/AssetList";
import { SearchDialog } from "@/features/search/SearchDialog";
import { api, type AssetSummary, type CategoryId } from "@/lib/api";
import { useViewState } from "@/lib/urlState";
import { cn } from "@/lib/utils";

const FALLBACK_TF: Record<CategoryId, string[]> = {
  vn: ["1m", "5m", "15m", "1h", "1d", "1w"],
  crypto: ["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
};

export default function App() {
  const [view, update] = useViewState();
  const [searchOpen, setSearchOpen] = useState(false);

  const meta = useQuery({ queryKey: ["categories"], queryFn: api.categories, staleTime: Infinity });
  const categories = meta.data?.categories ?? [
    { id: "vn" as const, label: "CK Việt Nam", timeframes: FALLBACK_TF.vn },
    { id: "crypto" as const, label: "Crypto", timeframes: FALLBACK_TF.crypto },
  ];
  const timeframes = categories.find((c) => c.id === view.category)?.timeframes ?? FALLBACK_TF[view.category];
  const timeframe = timeframes.includes(view.timeframe) ? view.timeframe : "1d";

  // Chưa chọn mã nào: tự chọn mã đầu danh sách (giao dịch nhiều nhất).
  const list = useQuery({ queryKey: ["assets", view.category], queryFn: () => api.assets(view.category) });
  useEffect(() => {
    if (!view.symbol && list.data?.length) update({ symbol: list.data[0].symbol });
  }, [view.symbol, list.data, update]);

  // Phím tắt Ctrl+K / ⌘K hoặc "/" để mở ô tìm kiếm.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;
      if ((e.key.toLowerCase() === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing)) {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const select = (a: AssetSummary) => update({ category: a.category, symbol: a.symbol });
  const isMac = navigator.platform.toLowerCase().includes("mac");

  return (
    <div className="flex h-full flex-col">
      <header className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-2.5">
        <span className="text-[15px] font-bold tracking-tight text-white">
          quant<span className="text-primary">·</span>invest
        </span>
        <button
          onClick={() => setSearchOpen(true)}
          className="order-last flex h-9 w-full items-center gap-2 rounded-lg border border-input bg-muted px-3 text-sm text-muted-foreground transition-colors hover:border-muted-foreground/40 sm:order-none sm:w-80"
        >
          <Search className="h-4 w-4" />
          <span className="flex-1 text-left">Tìm cổ phiếu, coin…</span>
          <kbd className="rounded border border-input px-1.5 font-mono text-[10px]">{isMac ? "⌘K" : "Ctrl K"}</kbd>
        </button>
        <nav className="ml-auto flex gap-0.5 rounded-lg bg-muted p-0.5" aria-label="Danh mục">
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => c.id !== view.category && update({ category: c.id, symbol: null })}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm transition-colors",
                c.id === view.category ? "bg-accent text-white" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {c.label}
            </button>
          ))}
        </nav>
        {meta.data?.demo && (
          <span className="rounded-full bg-flat/15 px-2 py-0.5 text-[11px] text-flat" title="Đang chạy DEMO_MODE">
            Dữ liệu giả lập
          </span>
        )}
      </header>

      <main className="grid min-h-0 flex-1 grid-rows-[minmax(0,38vh)_auto] md:grid-cols-[320px_minmax(0,1fr)] md:grid-rows-1">
        <aside className="flex min-h-0 flex-col border-b border-border md:border-b-0 md:border-r">
          <AssetList category={view.category} selected={view.symbol} onSelect={select} />
        </aside>
        <div className="min-h-0 overflow-y-auto">
          {view.symbol ? (
            <AssetDetail
              key={`${view.category}:${view.symbol}`}
              category={view.category}
              symbol={view.symbol}
              timeframes={timeframes}
              timeframe={timeframe}
              onTimeframe={(tf) => update({ timeframe: tf })}
            />
          ) : (
            <p className="p-6 text-sm text-muted-foreground">Chọn một mã ở danh sách bên trái hoặc nhấn Ctrl K để tìm.</p>
          )}
          <p className="px-4 pb-4 text-[11px] text-muted-foreground">
            Nguồn: {view.category === "vn" ? "VNDirect" : "Binance"}. Dữ liệu chỉ mang tính tham khảo, có thể chậm so với bảng giá
            chính thức.
          </p>
        </div>
      </main>

      <SearchDialog open={searchOpen} onOpenChange={setSearchOpen} onSelect={select} />
    </div>
  );
}
