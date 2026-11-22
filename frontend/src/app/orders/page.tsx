import type { Metadata } from "next";

import { OrdersList } from "@/components/orders/OrdersList";
import { Page } from "@/components/ui";

export const metadata: Metadata = { title: "My orders" };

export default function OrdersPage() {
  return (
    <Page title="My orders" subtitle="Track, view and cancel your orders.">
      <OrdersList />
    </Page>
  );
}
