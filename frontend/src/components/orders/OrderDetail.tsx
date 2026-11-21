"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";

import { Button, ErrorBanner } from "@/components/ui";
import type { Order } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";
import { formatDateTime, formatRupees } from "@/lib/format";

import { OrderStatusBadge, statusLabel } from "./OrderStatusBadge";

// Customers may cancel until the order leaves the store (the API enforces the same rule).
const CANCELLABLE = new Set<Order["status"]>(["placed", "confirmed"]);

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
      <p>
        Please{" "}
        <Link href={`/login?next=/orders/${encodeURIComponent(id)}`} className="text-emerald-700 hover:underline">
          log in
        </Link>{" "}
        to see this order.
      </p>
    );
  }
  if (order.isError) return <ErrorBanner message={order.error.message} />;
  if (!order.data) return <p className="text-slate-500">Loading order…</p>;

  const o = order.data;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          Placed {formatDateTime(o.created_at)} · pincode {o.pincode}
        </p>
        <OrderStatusBadge status={o.status} />
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <ul className="space-y-1 text-sm">
          {o.items.map((item) => (
            <li key={item.medicine_id} className="flex justify-between">
              <span>
                {item.quantity} × {item.name} ({item.pack_size})
              </span>
              <span>{formatRupees(item.line_total)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 flex justify-between border-t border-slate-100 pt-2 font-semibold">
          <span>Total</span>
          <span data-testid="order-total">{formatRupees(o.total)}</span>
        </p>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="mb-2 font-medium">Progress</h2>
        <ol className="space-y-2 border-l-2 border-emerald-200 pl-4">
          {o.history.map((step, index) => (
            <li key={`${step.status}-${index}`} data-step={step.status} className="text-sm">
              <span className="font-medium">{statusLabel(step.status)}</span>{" "}
              <span className="text-slate-500">· {formatDateTime(step.at)}</span>
            </li>
          ))}
        </ol>
      </section>

      {cancel.isError && <ErrorBanner message={cancel.error.message} />}
      {CANCELLABLE.has(o.status) && (
        <Button
          onClick={() => cancel.mutate()}
          disabled={cancel.isPending}
          className="bg-rose-600 hover:bg-rose-700"
        >
          {cancel.isPending ? "Cancelling…" : "Cancel order"}
        </Button>
      )}
    </div>
  );
}
