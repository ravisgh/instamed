import { Suspense } from "react";

import { OrderRoute } from "./OrderRoute";

export default function OrderPage() {
  // The order id comes from the URL at request time, so it renders inside Suspense.
  return (
    <>
      <h1 className="mb-4 text-2xl font-semibold">Order details</h1>
      <Suspense>
        <OrderRoute />
      </Suspense>
    </>
  );
}
