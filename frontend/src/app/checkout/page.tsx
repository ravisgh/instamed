import type { Metadata } from "next";

import { Checkout } from "@/components/checkout/Checkout";
import { Page } from "@/components/ui";

export const metadata: Metadata = { title: "Checkout" };

export default function CheckoutPage() {
  return (
    <Page title="Checkout" subtitle="Review your items and place the order.">
      <Checkout />
    </Page>
  );
}
