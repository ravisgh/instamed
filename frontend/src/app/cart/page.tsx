import type { Metadata } from "next";

import { CartView } from "@/components/cart/CartView";
import { Page } from "@/components/ui";

export const metadata: Metadata = { title: "Cart" };

export default function CartPage() {
  return (
    <Page title="Your cart">
      <CartView />
    </Page>
  );
}
