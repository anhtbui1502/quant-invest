// Bảng lệnh tìm kiếm (Command palette) theo mẫu shadcn/ui, dựa trên cmdk + Radix Dialog.
import * as React from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { Command as Cmdk } from "cmdk";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

export function CommandDialog({
  open,
  onOpenChange,
  title,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content
          aria-describedby={undefined}
          className="fixed left-1/2 top-[12vh] z-50 w-[calc(100%-2rem)] max-w-xl -translate-x-1/2 overflow-hidden rounded-xl border border-border bg-card shadow-2xl"
        >
          <Dialog.Title className="sr-only">{title}</Dialog.Title>
          <Cmdk shouldFilter={false} className="flex flex-col">
            {children}
          </Cmdk>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export function CommandInput(props: React.ComponentProps<typeof Cmdk.Input>) {
  return (
    <div className="flex items-center gap-2 border-b border-border px-4">
      <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
      <Cmdk.Input
        {...props}
        className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
      />
    </div>
  );
}

export function CommandList({ className, ...props }: React.ComponentProps<typeof Cmdk.List>) {
  return <Cmdk.List className={cn("max-h-[60vh] overflow-y-auto p-2", className)} {...props} />;
}

export function CommandGroup({ className, ...props }: React.ComponentProps<typeof Cmdk.Group>) {
  return (
    <Cmdk.Group
      className={cn(
        "[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
}

export function CommandItem({ className, ...props }: React.ComponentProps<typeof Cmdk.Item>) {
  return (
    <Cmdk.Item
      className={cn(
        "flex cursor-pointer items-center gap-3 rounded-lg px-2 py-2 text-sm data-[selected=true]:bg-accent",
        className,
      )}
      {...props}
    />
  );
}

export const CommandEmpty = Cmdk.Empty;
export const CommandLoading = Cmdk.Loading;
