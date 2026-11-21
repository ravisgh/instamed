import { OrdersList } from "@/components/orders/OrdersList";

export default function OrdersPage() {
  return (
    <>
      <h1 className="mb-4 text-2xl font-semibold">My orders</h1>
      <OrdersList />
    </>
  );
}
