// Bảng thông tin cơ bản của tài sản.
import type { AssetInfo, InfoField } from "@/lib/api";
import { formatCompact, formatDate, formatNumber, formatPct, formatPrice } from "@/lib/format";

function render(f: InfoField, info: AssetInfo): string {
  if (f.value == null) return "—";
  switch (f.kind) {
    case "price":
      return formatPrice(Number(f.value), info.category);
    case "volume":
      return formatCompact(Number(f.value));
    case "percent":
      return formatPct(Number(f.value));
    case "date":
      return formatDate(f.value);
    case "number":
      return formatNumber(Number(f.value));
    default:
      return String(f.value);
  }
}

export function InfoGrid({ info }: { info: AssetInfo }) {
  return (
    <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-3 xl:grid-cols-4">
      {info.fields.map((f) => (
        <div key={f.label} className="min-w-0 bg-card px-3 py-2.5">
          <dt className="text-[11px] text-muted-foreground">{f.label}</dt>
          <dd className="truncate text-sm font-medium tabular text-white" title={render(f, info)}>
            {render(f, info)}
          </dd>
        </div>
      ))}
    </dl>
  );
}
