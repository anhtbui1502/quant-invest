// Ô tìm kiếm toàn cục (Ctrl+K / ⌘K): tìm cả cổ phiếu VN và crypto.
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandLoading,
} from "@/components/ui/command";
import { api, type AssetSummary, type CategoryId } from "@/lib/api";
import { formatPct, formatPrice, trendClass } from "@/lib/format";
import { useDebounced } from "@/lib/useDebounced";
import { cn } from "@/lib/utils";

const GROUP_LABEL: Record<CategoryId, string> = { vn: "Cổ phiếu Việt Nam", crypto: "Crypto" };

export function SearchDialog({
  open,
  onOpenChange,
  onSelect,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (asset: AssetSummary) => void;
}) {
  const [query, setQuery] = useState("");
  const q = useDebounced(query.trim(), 150);

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  const { data = [], isFetching, error } = useQuery({
    queryKey: ["search", q],
    queryFn: () => api.search(q),
    enabled: q.length > 0,
    staleTime: 30_000,
  });

  const groups = (["vn", "crypto"] as CategoryId[])
    .map((c) => ({ id: c, items: data.filter((a) => a.category === c) }))
    .filter((g) => g.items.length);

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange} title="Tìm kiếm tài sản">
      <CommandInput
        value={query}
        onValueChange={setQuery}
        placeholder="Nhập mã hoặc tên: FPT, Hòa Phát, BTC, SOL…"
      />
      <CommandList>
        {!q && (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            Tìm theo mã hoặc tên công ty. Gõ không dấu cũng được.
          </p>
        )}
        {q && isFetching && !data.length && <CommandLoading>
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">Đang tìm…</p>
        </CommandLoading>}
        {q && error && (
          <p className="px-2 py-6 text-center text-sm text-down">{(error as Error).message}</p>
        )}
        {q && !isFetching && !error && (
          <CommandEmpty className="px-2 py-6 text-center text-sm text-muted-foreground">
            Không tìm thấy "{q}".
          </CommandEmpty>
        )}
        {groups.map((g) => (
          <CommandGroup key={g.id} heading={GROUP_LABEL[g.id]}>
            {g.items.map((a) => (
              <CommandItem
                key={`${a.category}:${a.symbol}`}
                value={`${a.category}:${a.symbol}`}
                onSelect={() => {
                  onSelect(a);
                  onOpenChange(false);
                }}
              >
                <span className="w-24 shrink-0 font-semibold">{a.display}</span>
                <span className="min-w-0 flex-1 truncate text-muted-foreground">{a.name}</span>
                <span className="hidden text-xs text-muted-foreground sm:inline">{a.exchange}</span>
                <span className="w-24 text-right tabular">{formatPrice(a.price, a.category)}</span>
                <span className={cn("w-16 text-right text-xs tabular", trendClass(a.change_pct))}>
                  {formatPct(a.change_pct)}
                </span>
              </CommandItem>
            ))}
          </CommandGroup>
        ))}
      </CommandList>
    </CommandDialog>
  );
}
