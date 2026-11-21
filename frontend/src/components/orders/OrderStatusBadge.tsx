import type { OrderStatus } from "@/lib/api/types";

const STYLES: Record<OrderStatus, string> = {
  placed: "bg-sky-100 text-sky-800",
  confirmed: "bg-indigo-100 text-indigo-800",
  dispatched: "bg-amber-100 text-amber-800",
  delivered: "bg-emerald-100 text-emerald-800",
  cancelled: "bg-slate-200 text-slate-700",
};

export function statusLabel(status: OrderStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}>{statusLabel(status)}</span>;
}
