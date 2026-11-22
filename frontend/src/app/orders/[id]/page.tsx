import type { Metadata } from "next";
import { Suspense } from "react";

import { Page } from "@/components/ui";

import { OrderRoute } from "./OrderRoute";

export const metadata: Metadata = { title: "Order details" };

export default function OrderPage() {
  // The order id comes from the URL at request time, so it renders inside Suspense.
  return (
    <Page title="Order details">
      <Suspense>
        <OrderRoute />
      </Suspense>
    </Page>
  );
}
