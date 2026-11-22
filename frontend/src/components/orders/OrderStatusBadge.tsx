import type { OrderStatus } from "@/lib/api/types";

const STYLES: Record<OrderStatus, { pill: string; dot: string }> = {
  placed: { pill: "bg-sky-50 text-sky-800 ring-sky-200", dot: "bg-sky-500" },
  confirmed: { pill: "bg-indigo-50 text-indigo-800 ring-indigo-200", dot: "bg-indigo-500" },
  dispatched: { pill: "bg-amber-50 text-amber-800 ring-amber-200", dot: "bg-amber-500" },
  delivered: { pill: "bg-brand-50 text-brand-800 ring-brand-200", dot: "bg-brand-500" },
  cancelled: { pill: "bg-slate-100 text-slate-600 ring-slate-200", dot: "bg-slate-400" },
};

export function statusLabel(status: OrderStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const style = STYLES[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${style.pill}`}
    >
      <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      <span>{statusLabel(status)}</span>
    </span>
  );
}
