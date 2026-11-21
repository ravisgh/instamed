import { CartView } from "@/components/cart/CartView";

export default function CartPage() {
  return (
    <>
      <h1 className="mb-4 text-2xl font-semibold">Your cart</h1>
      <CartView />
    </>
  );
}
