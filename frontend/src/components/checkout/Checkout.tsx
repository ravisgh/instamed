"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, ErrorBanner } from "@/components/ui";
import type { Order, OrderCreate } from "@/lib/api/types";
import { useAuth } from "@/lib/auth/AuthProvider";
import { useCart } from "@/lib/cart/CartProvider";
import { formatRupees } from "@/lib/format";

import { PrescriptionPicker } from "./PrescriptionPicker";

export function Checkout() {
  const { status, api } = useAuth();
  const { cart, total, needsPrescription, clear } = useCart();
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
      <p className="text-slate-600">
        Nothing to check out.{" "}
        <Link href="/" className="text-emerald-700 hover:underline">
          Search medicines
        </Link>
      </p>
    );
  }
  if (status === "loading") return <p className="text-slate-500">Loading…</p>;
  if (status === "anonymous") {
    return (
      <p className="text-slate-700">
        Please{" "}
        <Link href="/login?next=/checkout" className="font-medium text-emerald-700 hover:underline">
          log in
        </Link>{" "}
        to place your order.
      </p>
    );
  }

  const blocked = needsPrescription && !prescriptionId;

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="mb-2 font-medium">Order summary · pincode {cart.pincode}</h2>
        <ul className="space-y-1 text-sm">
          {cart.lines.map((l) => (
            <li key={l.medicine_id} className="flex justify-between">
              <span>
                {l.quantity} × {l.name} ({l.pack_size})
              </span>
              <span>{formatRupees(Math.round(l.price * 100 * l.quantity) / 100)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 flex justify-between border-t border-slate-100 pt-2 font-semibold">
          <span>Total</span>
          <span>{formatRupees(total)}</span>
        </p>
      </section>

      {needsPrescription && <PrescriptionPicker value={prescriptionId} onChange={setPrescriptionId} />}
      {placeOrder.isError && <ErrorBanner message={placeOrder.error.message} />}

      <Button
        onClick={() => placeOrder.mutate()}
        disabled={blocked || placeOrder.isPending}
        className="w-full py-2.5 text-base"
      >
        {placeOrder.isPending ? "Placing order…" : "Place order"}
      </Button>
      {blocked && <p className="text-center text-sm text-slate-500">Choose an approved prescription first.</p>}
    </div>
  );
}
