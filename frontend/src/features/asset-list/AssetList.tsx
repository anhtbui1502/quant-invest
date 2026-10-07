// Danh sách tài sản của một danh mục, có lọc theo sàn và lọc nhanh theo chữ.
import { useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type AssetSummary, type CategoryId } from "@/lib/api";
import { formatCompact, formatPct, formatPrice, trendClass } from "@/lib/format";
import { fold } from "@/lib/text";
import { cn } from "@/lib/utils";

const VN_FLOORS = ["Tất cả", "HOSE", "HNX", "UPCOM"] as const;

export function AssetList({
  category,
  selected,
  onSelect,
}: {
  category: CategoryId;
  selected: string | null;
  onSelect: (asset: AssetSummary) => void;
}) {
  const [floor, setFloor] = useState<(typeof VN_FLOORS)[number]>("Tất cả");
  const [filter, setFilter] = useState("");

  const { data = [], isLoading, error, refetch } = useQuery({
    queryKey: ["assets", category],
    queryFn: () => api.assets(category),
    refetchInterval: 30_000,
  });

  const items = useMemo(() => {
    const f = fold(filter.trim());
    return data.filter(
      (a) =>
        (category !== "vn" || floor === "Tất cả" || a.exchange === floor) &&
        (!f || fold(a.symbol).includes(f) || fold(a.name).includes(f)),
    );
  }, [data, category, floor, filter]);

  const parentRef = useRef<HTMLDivElement>(null);
  const rows = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 52,
    overscan: 10,
  });

  return (
    <div className="flex min-h-0 flex-col">
      <div className="flex flex-col gap-2 border-b border-border p-3">
        <input
          id="asset-filter"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder={category === "vn" ? "Lọc mã, tên công ty…" : "Lọc coin…"}
          className="h-8 rounded-md border border-input bg-muted px-3 text-sm outline-none placeholder:text-muted-foreground focus:border-primary/60"
        />
        {category === "vn" && (
          <div className="flex gap-1">
            {VN_FLOORS.map((f) => (
              <Button key={f} size="sm" variant={floor === f ? "active" : "ghost"} onClick={() => setFloor(f)}>
                {f}
              </Button>
            ))}
          </div>
        )}
        <div className="flex justify-between px-1 text-[11px] uppercase tracking-wider text-muted-foreground">
          <span>{items.length.toLocaleString("vi-VN")} mã</span>
          <span>{category === "vn" ? "Giá (đ) · %" : "Giá (USDT) · % 24h"}</span>
        </div>
      </div>

      {isLoading && (
        <div className="flex flex-col gap-2 p-3">
          {Array.from({ length: 10 }, (_, i) => <Skeleton key={i} className="h-10" />)}
        </div>
      )}
      {error && (
        <div className="flex flex-col items-start gap-2 p-4 text-sm">
          <p className="text-down">Không tải được danh sách: {(error as Error).message}</p>
          <Button size="sm" variant="outline" onClick={() => refetch()}>Thử lại</Button>
        </div>
      )}

      <div ref={parentRef} className="min-h-0 flex-1 overflow-y-auto">
        <div style={{ height: rows.getTotalSize(), position: "relative" }}>
          {rows.getVirtualItems().map((v) => {
            const a = items[v.index];
            const active = a.symbol === selected;
            return (
              <button
                key={a.symbol}
                onClick={() => onSelect(a)}
                style={{ position: "absolute", top: 0, left: 0, width: "100%", height: v.size, transform: `translateY(${v.start}px)` }}
                className="px-2 py-0.5 text-left"
              >
                <div
                  className={cn(
                    "grid h-full grid-cols-[1fr_auto] items-center gap-x-3 rounded-lg px-2 transition-colors hover:bg-accent/60",
                    active && "bg-accent",
                  )}
                >
                  <div className="min-w-0">
                    <div className="flex items-baseline gap-2">
                      <span className="font-semibold text-white">{a.display}</span>
                      {category === "vn" && <span className="text-[10px] text-muted-foreground">{a.exchange}</span>}
                    </div>
                    <div className="truncate text-[11px] text-muted-foreground">
                      {category === "vn" ? a.name : `GT 24h ${formatCompact(a.volume)}`}
                    </div>
                  </div>
                  <div className="text-right tabular">
                    <div className="text-sm">{formatPrice(a.price, category)}</div>
                    <div className={cn("text-[11px]", trendClass(a.change_pct))}>{formatPct(a.change_pct)}</div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
        {!isLoading && !error && items.length === 0 && (
          <p className="p-4 text-sm text-muted-foreground">Không có mã nào khớp bộ lọc.</p>
        )}
      </div>
    </div>
  );
}
