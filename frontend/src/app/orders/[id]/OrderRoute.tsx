"use client";

import { useParams } from "next/navigation";

import { OrderDetail } from "@/components/orders/OrderDetail";

export function OrderRoute() {
  const { id } = useParams<{ id: string }>();
  return <OrderDetail id={id} />;
}
