// Biểu đồ nến + khối lượng bằng TradingView Lightweight Charts.
import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import type { Candle, CategoryId } from "@/lib/api";
import { cryptoDecimals, formatPrice } from "@/lib/format";

const UP = "#22c55e";
const DOWN = "#f43f5e";

/** Lightweight Charts hiển thị giờ theo UTC, nên dịch thời gian sang múi giờ cần hiển thị:
 *  cổ phiếu VN luôn theo giờ Việt Nam (UTC+7), crypto theo giờ máy người dùng. */
function tzShift(category: CategoryId): number {
  return category === "vn" ? 7 * 3600 : -new Date().getTimezoneOffset() * 60;
}

export function CandleChart({
  candles,
  category,
  intraday,
}: {
  candles: Candle[];
  category: CategoryId;
  intraday: boolean;
}) {
  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const candleSeries = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeries = useRef<ISeriesApi<"Histogram"> | null>(null);
  const lastKey = useRef("");

  // Tạo biểu đồ một lần.
  useEffect(() => {
    if (!container.current) return;
    const c = createChart(container.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#7d8799",
        fontFamily: "JetBrains Mono, ui-monospace, monospace",
        fontSize: 11,
        attributionLogo: true,
      },
      grid: { vertLines: { color: "#141b27" }, horzLines: { color: "#141b27" } },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#1f2633" },
      timeScale: { borderColor: "#1f2633", rightOffset: 4 },
      localization: { locale: "vi-VN" },
    });
    candleSeries.current = c.addSeries(CandlestickSeries, {
      upColor: UP,
      downColor: DOWN,
      borderVisible: false,
      wickUpColor: UP,
      wickDownColor: DOWN,
    });
    volumeSeries.current = c.addSeries(HistogramSeries, {
      priceScaleId: "volume",
      priceFormat: { type: "volume" },
      lastValueVisible: false,
      priceLineVisible: false,
    });
    c.priceScale("volume").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    candleSeries.current.priceScale().applyOptions({ scaleMargins: { top: 0.08, bottom: 0.25 } });
    chart.current = c;
    return () => {
      c.remove();
      chart.current = null;
    };
  }, []);

  // Cập nhật dữ liệu.
  useEffect(() => {
    if (!chart.current || !candleSeries.current || !volumeSeries.current) return;
    const shift = tzShift(category);
    const last = candles[candles.length - 1]?.close ?? 1;
    const precision = category === "vn" ? 0 : cryptoDecimals(last);
    candleSeries.current.applyOptions({
      priceFormat: { type: "price", precision, minMove: 1 / 10 ** precision },
    });
    chart.current.applyOptions({
      timeScale: { timeVisible: intraday, secondsVisible: false },
      localization: { locale: "vi-VN", priceFormatter: (p: number) => formatPrice(p, category) },
    });

    candleSeries.current.setData(
      candles.map((c) => ({ time: (c.time + shift) as UTCTimestamp, open: c.open, high: c.high, low: c.low, close: c.close })),
    );
    volumeSeries.current.setData(
      candles.map((c) => ({
        time: (c.time + shift) as UTCTimestamp,
        value: c.volume,
        color: c.close >= c.open ? "rgba(34,197,94,0.35)" : "rgba(244,63,94,0.35)",
      })),
    );

    // Chỉ căn lại khung nhìn khi đổi mã hoặc khung thời gian, không phải mỗi lần tự làm mới.
    const key = `${category}:${intraday}:${candles[0]?.time}`;
    if (key !== lastKey.current) {
      chart.current.timeScale().fitContent();
      lastKey.current = key;
    }
  }, [candles, category, intraday]);

  return <div ref={container} className="h-full w-full" />;
}
