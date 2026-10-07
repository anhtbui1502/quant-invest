import { Button } from "@/components/ui/button";
import { TIMEFRAME_LABELS } from "@/lib/format";

const SHORT: Record<string, string> = { "1m": "1m", "5m": "5m", "15m": "15m", "1h": "1H", "4h": "4H", "1d": "1D", "1w": "1W" };

export function TimeframeBar({
  timeframes,
  value,
  onChange,
}: {
  timeframes: string[];
  value: string;
  onChange: (tf: string) => void;
}) {
  return (
    <div className="flex gap-0.5 rounded-lg bg-muted p-0.5" role="group" aria-label="Khung thời gian">
      {timeframes.map((tf) => (
        <Button
          key={tf}
          size="sm"
          variant={tf === value ? "active" : "ghost"}
          title={TIMEFRAME_LABELS[tf]}
          aria-pressed={tf === value}
          onClick={() => onChange(tf)}
          className="font-mono"
        >
          {SHORT[tf] ?? tf}
        </Button>
      ))}
    </div>
  );
}
