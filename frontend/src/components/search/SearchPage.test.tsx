import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { useCart } from "@/lib/cart/CartProvider";
import { fakeHit, fakeMedicine, renderWithProviders } from "@/test/render";
import { server } from "@/test/server";

import { SearchPage } from "./SearchPage";

function CartCount() {
  const { count } = useCart();
  return <p data-testid="cart-count">{count}</p>;
}

function renderSearch() {
  return renderWithProviders(
    <>
      <SearchPage />
      <CartCount />
    </>,
  );
}

function mockApi(stock: () => Response = () =>
  HttpResponse.json({ pincode: "201014", store_id: "s1", results: [fakeHit] })) {
  let searchedFor = "";
  server.use(
    http.get("*/backend/medicines/search", ({ request }) => {
      searchedFor = new URL(request.url).searchParams.get("q") ?? "";
      return HttpResponse.json({ engine: "elasticsearch", results: [fakeMedicine] });
    }),
    http.get("*/backend/search", stock),
  );
  return { searchedFor: () => searchedFor };
}

describe("SearchPage", () => {
  it("finds a medicine despite a typo, shows stock at the pincode and adds it to the cart", async () => {
    const api = mockApi();
    const user = userEvent.setup();
    renderSearch();

    await user.type(screen.getByLabelText(/pincode/i), "201014");
    await user.type(screen.getByLabelText(/search medicines/i), "paracetmol");

    await user.click(await screen.findByRole("button", { name: /Paracetamol 500 Tablet/ }));
    expect(api.searchedFor()).toBe("paracetmol");

    expect(await screen.findByText("₹28.10")).toBeInTheDocument();
    expect(screen.getByText("3 in stock")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /add to cart/i }));

    await waitFor(() => expect(screen.getByTestId("cart-count")).toHaveTextContent("1"));
  });

  it("remembers the pincode", async () => {
    mockApi();
    const user = userEvent.setup();
    renderSearch();

    await user.type(screen.getByLabelText(/pincode/i), "201014");

    expect(window.localStorage.getItem("instamed.pincode")).toBe("201014");
  });

  it("asks for a valid pincode before checking stock", async () => {
    mockApi();
    const user = userEvent.setup();
    renderSearch();

    await user.type(screen.getByLabelText(/pincode/i), "0123");
    await user.type(screen.getByLabelText(/search medicines/i), "paracetamol");
    await user.click(await screen.findByRole("button", { name: /Paracetamol 500 Tablet/ }));

    expect(screen.getByText(/enter a valid 6-digit pincode/i)).toBeInTheDocument();
  });

  it("explains when the pincode is not serviceable", async () => {
    mockApi(() => HttpResponse.json({ detail: "Pincode not serviceable" }, { status: 404 }));
    const user = userEvent.setup();
    renderSearch();

    await user.type(screen.getByLabelText(/pincode/i), "110001");
    await user.type(screen.getByLabelText(/search medicines/i), "paracetamol");
    await user.click(await screen.findByRole("button", { name: /Paracetamol 500 Tablet/ }));

    expect(await screen.findByText("Pincode not serviceable")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add to cart/i })).not.toBeInTheDocument();
  });
});
