"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

import { ArrowLeftIcon, CheckIcon, LockIcon, PinIcon, XIcon } from "@/components/icons";
import { Button, Card, EmptyState, ErrorBanner, Skeleton, buttonClass } from "@/components/ui";
import type { Order, OrderStatus } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";
import { formatDateTime, formatRupees } from "@/lib/format";

import { OrderStatusBadge, statusLabel } from "./OrderStatusBadge";

// Customers may cancel until the order leaves the store (the API enforces the same rule).
const CANCELLABLE = new Set<Order["status"]>(["placed", "confirmed"]);
const FLOW: OrderStatus[] = ["placed", "confirmed", "dispatched", "delivered"];

export function OrderDetail({ id }: { id: string }) {
  const { status, api } = useAuth();
  const queryClient = useQueryClient();
  const order = useQuery({
    queryKey: ["orders", id],
    queryFn: () => api.get<Order>(`/orders/${encodeURIComponent(id)}`),
    enabled: status === "authenticated",
  });
  const cancel = useMutation({
    mutationFn: () => api.post<Order>(`/orders/${encodeURIComponent(id)}/cancel`),
    onSuccess: (updated) => {
      queryClient.setQueryData(["orders", id], updated);
      queryClient.invalidateQueries({ queryKey: ["orders"], exact: true });
    },
  });

  if (status === "anonymous") {
    return (
      <EmptyState icon={<LockIcon />} title="Log in to see this order">
        <Link href={`/login?next=/orders/${encodeURIComponent(id)}`} className={buttonClass("primary", "md", "mt-2")}>
          Log in
        </Link>
      </EmptyState>
    );
  }
  if (order.isError) return <ErrorBanner message={order.error.message} />;
  if (!order.data) {
    return (
      <div className="space-y-3" aria-label="Loading order">
        <Skeleton className="h-24 w-full rounded-2xl" />
        <Skeleton className="h-40 w-full rounded-2xl" />
      </div>
    );
  }

  const o = order.data;
  return (
    <div className="space-y-4">
      <Link href="/orders" className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-700 hover:text-brand-800">
        <ArrowLeftIcon className="h-4 w-4" /> All orders
      </Link>

      <div className="grid items-start gap-4 lg:grid-cols-[1fr_20rem]">
        <Card className="p-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <p className="flex items-center gap-1.5 text-sm text-slate-500">
              <PinIcon className="h-4 w-4 text-brand-600" />
              Placed {formatDateTime(o.created_at)} · pincode {o.pincode}
            </p>
            <OrderStatusBadge status={o.status} />
          </div>
          <ul className="divide-y divide-slate-100 text-sm">
            {o.items.map((item) => (
              <li key={item.medicine_id} className="flex justify-between gap-4 py-2.5">
                <span className="text-slate-700">
                  {item.quantity} × {item.name} <span className="text-slate-400">({item.pack_size})</span>
                </span>
                <span className="font-medium tabular-nums">{formatRupees(item.line_total)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2 flex justify-between border-t border-slate-200 pt-3 text-base font-bold">
            <span>Total</span>
            <span data-testid="order-total" className="tabular-nums">
              {formatRupees(o.total)}
            </span>
          </p>
        </Card>

        <Card className="p-5">
          <h2 className="mb-4 text-base font-bold text-slate-900">Progress</h2>
          <Timeline order={o} />
          {cancel.isError && (
            <div className="mt-4">
              <ErrorBanner message={cancel.error.message} />
            </div>
          )}
          {CANCELLABLE.has(o.status) && (
            <Button
              variant="danger"
              onClick={() => cancel.mutate()}
              disabled={cancel.isPending}
              className="mt-5 w-full"
            >
              {cancel.isPending ? "Cancelling…" : "Cancel order"}
            </Button>
          )}
        </Card>
      </div>
    </div>
  );
}

/** Done steps come from the order history; for live orders the remaining steps show greyed out. */
function Timeline({ order }: { order: Order }) {
  const done = order.history;
  const reached = new Set(done.map((s) => s.status));
  const upcoming = order.status === "cancelled" ? [] : FLOW.filter((s) => !reached.has(s));

  return (
    <ol className="relative">
      {done.map((step, index) => {
        const cancelled = step.status === "cancelled";
        const last = index === done.length - 1 && upcoming.length === 0;
        return (
          <li key={`${step.status}-${index}`} data-step={step.status} className="relative flex gap-3 pb-5 last:pb-0">
            {!last && <span aria-hidden="true" className="absolute top-6 left-[11px] h-full w-0.5 bg-brand-200" />}
            <span
              className={`relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-white ${
                cancelled ? "bg-rose-500" : "bg-brand-600"
              }`}
            >
              {cancelled ? <XIcon className="h-3.5 w-3.5" /> : <CheckIcon className="h-3.5 w-3.5" />}
            </span>
            <span className="text-sm">
              <span className={`block font-semibold ${cancelled ? "text-rose-700" : "text-slate-900"}`}>
                {statusLabel(step.status)}
              </span>
              <span className="text-xs text-slate-500">{formatDateTime(step.at)}</span>
            </span>
          </li>
        );
      })}
      {upcoming.map((s, index) => (
        <li key={s} className="relative flex gap-3 pb-5 last:pb-0">
          {index < upcoming.length - 1 && (
            <span aria-hidden="true" className="absolute top-6 left-[11px] h-full w-0.5 bg-slate-200" />
          )}
          <span className="relative z-10 h-6 w-6 shrink-0 rounded-full border-2 border-slate-200 bg-white" />
          <span className="text-sm font-medium text-slate-400">{statusLabel(s)}</span>
        </li>
      ))}
    </ol>
  );
}
