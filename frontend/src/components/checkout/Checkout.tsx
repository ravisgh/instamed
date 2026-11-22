"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { OrderSummary } from "@/components/cart/CartView";
import { CartIcon, LockIcon, PinIcon, ShieldIcon } from "@/components/icons";
import { Button, Card, EmptyState, ErrorBanner, Spinner, buttonClass } from "@/components/ui";
import type { Order, OrderCreate } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";
import { useCart } from "@/lib/cart/CartProvider";
import { formatRupees } from "@/lib/format";

import { PrescriptionPicker } from "./PrescriptionPicker";

export function Checkout() {
  const { status, api } = useAuth();
  const { cart, count, total, needsPrescription, clear } = useCart();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [prescriptionId, setPrescriptionId] = useState<string | null>(null);

  const placeOrder = useMutation({
    mutationFn: () => {
      const body: OrderCreate = {
        pincode: cart.pincode ?? "",
        items: cart.lines.map((l) => ({ medicine_id: l.medicine_id, quantity: l.quantity })),
      };
      if (needsPrescription && prescriptionId) body.prescription_id = prescriptionId;
      return api.post<Order>("/orders", body);
    },
    onSuccess: (order) => {
      clear();
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      router.push(`/orders/${order.id}`);
    },
  });

  if (cart.lines.length === 0) {
    return (
      <EmptyState icon={<CartIcon />} title="Nothing to check out">
        <p>Your cart is empty.</p>
        <Link href="/" className={buttonClass("primary", "md", "mt-4")}>
          Search medicines
        </Link>
      </EmptyState>
    );
  }
  if (status === "loading") return <Spinner />;
  if (status === "anonymous") {
    return (
      <EmptyState icon={<LockIcon />} title="Log in to place your order">
        <p>Your cart is saved. Log in or create an account to continue.</p>
        <Link href="/login?next=/checkout" className={buttonClass("primary", "md", "mt-4")}>
          Log in
        </Link>
      </EmptyState>
    );
  }

  const blocked = needsPrescription && !prescriptionId;

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[1fr_20rem]">
      <div className="space-y-4">
        <Card className="p-5">
          <h2 className="mb-3 flex items-center gap-2 text-base font-bold text-slate-900">
            <PinIcon className="h-4 w-4 text-brand-600" /> Delivering to {cart.pincode}
          </h2>
          <ul className="divide-y divide-slate-100 text-sm">
            {cart.lines.map((l) => (
              <li key={l.medicine_id} className="flex justify-between gap-4 py-2.5">
                <span className="text-slate-700">
                  {l.quantity} × {l.name} <span className="text-slate-400">({l.pack_size})</span>
                </span>
                <span className="font-medium tabular-nums">
                  {formatRupees(Math.round(l.price * 100 * l.quantity) / 100)}
                </span>
              </li>
            ))}
          </ul>
        </Card>

        {needsPrescription && <PrescriptionPicker value={prescriptionId} onChange={setPrescriptionId} />}
      </div>

      <OrderSummary count={count} total={formatRupees(total)}>
        {placeOrder.isError && <ErrorBanner message={placeOrder.error.message} />}
        <Button
          size="lg"
          onClick={() => placeOrder.mutate()}
          disabled={blocked || placeOrder.isPending}
          className="w-full"
        >
          {placeOrder.isPending ? "Placing order…" : "Place order"}
        </Button>
        {blocked && <p className="text-center text-xs text-slate-500">Choose an approved prescription first.</p>}
        <p className="flex items-center justify-center gap-1.5 text-xs text-slate-400">
          <ShieldIcon className="h-3.5 w-3.5" /> You can cancel any time before dispatch
        </p>
      </OrderSummary>
    </div>
  );
}
