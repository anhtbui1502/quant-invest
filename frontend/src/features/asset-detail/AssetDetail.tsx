// Trang chi tiết: tiêu đề + giá, biểu đồ nến theo khung thời gian, thông tin cơ bản.
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CandleChart } from "@/features/chart/CandleChart";
import { TimeframeBar } from "@/features/chart/TimeframeBar";
import { InfoGrid } from "./InfoGrid";
import { api, type CategoryId } from "@/lib/api";
import { formatPct, formatPrice, trendClass } from "@/lib/format";
import { cn } from "@/lib/utils";

const INTRADAY = new Set(["1m", "5m", "15m", "1h", "4h"]);

export function AssetDetail({
  category,
  symbol,
  timeframes,
  timeframe,
  onTimeframe,
}: {
  category: CategoryId;
  symbol: string;
  timeframes: string[];
  timeframe: string;
  onTimeframe: (tf: string) => void;
}) {
  const info = useQuery({
    queryKey: ["info", category, symbol],
    queryFn: () => api.info(category, symbol),
    refetchInterval: 30_000,
  });
  const candles = useQuery({
    queryKey: ["candles", category, symbol, timeframe],
    queryFn: () => api.candles(category, symbol, timeframe),
    refetchInterval: INTRADAY.has(timeframe) ? 15_000 : 60_000,
    placeholderData: (prev, prevQuery) =>
      prevQuery?.queryKey[2] === symbol ? prev : undefined, // giữ nến cũ khi đổi khung, tránh nháy trắng
  });
  const i = info.data;

  return (
    <div className="flex min-h-0 flex-col gap-3 p-3 md:p-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="min-w-0">
          <div className="flex items-baseline gap-2">
            <h1 className="text-xl font-semibold text-white">{i?.display ?? symbol}</h1>
            <span className="text-xs text-muted-foreground">{i?.exchange}</span>
          </div>
          <p className="truncate text-xs text-muted-foreground">{i?.name ?? " "}</p>
        </div>
        {i ? (
          <div className="flex items-baseline gap-2 tabular">
            <span className="text-2xl font-semibold text-white">{formatPrice(i.price, category)}</span>
            <span className="text-xs text-muted-foreground">{i.currency}</span>
            <Badge
              className={cn(
                trendClass(i.change_pct),
                (i.change_pct ?? 0) > 0 ? "bg-up/12" : (i.change_pct ?? 0) < 0 ? "bg-down/12" : "bg-flat/12",
              )}
            >
              {i.change != null && (i.change > 0 ? "+" : "") + formatPrice(i.change, category)} ({formatPct(i.change_pct)})
            </Badge>
          </div>
        ) : info.isLoading ? (
          <Skeleton className="h-8 w-48" />
        ) : null}
        <div className="ml-auto">
          <TimeframeBar timeframes={timeframes} value={timeframe} onChange={onTimeframe} />
        </div>
      </div>

      <div className="relative h-[52vh] min-h-[320px] rounded-lg border border-border bg-card">
        {candles.data && candles.data.length > 0 && (
          <CandleChart candles={candles.data} category={category} intraday={INTRADAY.has(timeframe)} />
        )}
        {candles.isLoading && <Skeleton className="absolute inset-3" />}
        {candles.data?.length === 0 && (
          <p className="absolute inset-0 grid place-items-center text-sm text-muted-foreground">
            Chưa có dữ liệu nến cho khung này.
          </p>
        )}
        {candles.error && !candles.data && (
          <div className="absolute inset-0 grid place-items-center p-4 text-center text-sm">
            <div className="flex flex-col items-center gap-2">
              <p className="text-down">Không tải được biểu đồ: {(candles.error as Error).message}</p>
              <Button size="sm" variant="outline" onClick={() => candles.refetch()}>Thử lại</Button>
            </div>
          </div>
        )}
      </div>

      <section className="flex flex-col gap-2">
        <h2 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Thông tin cơ bản</h2>
        {i && <InfoGrid info={i} />}
        {info.isLoading && <Skeleton className="h-28" />}
        {info.error && <p className="text-sm text-down">Không tải được thông tin: {(info.error as Error).message}</p>}
      </section>
    </div>
  );
}
