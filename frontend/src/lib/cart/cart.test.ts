import { describe, expect, it } from "vitest";

import { type CartState, cartReducer, cartTotal, EMPTY_CART, itemCount, needsPrescription } from "./cart";

const otc = {
  medicine_id: "m1",
  name: "Paracetamol 500 Tablet",
  pack_size: "15 Tablet",
  mrp: 30.5,
  price: 28.1,
  quantity_available: 3,
  prescription_required: false,
};
const rx = { ...otc, medicine_id: "m2", name: "Amoxicillin 500", price: 95.55, prescription_required: true };

function add(state: CartState, hit = otc, storeId = "s1") {
  return cartReducer(state, { type: "add", hit, storeId, pincode: "201014" });
}

describe("cartReducer", () => {
  it("adds a line and increments quantity on repeat adds", () => {
    const state = add(add(EMPTY_CART));

    expect(state.storeId).toBe("s1");
    expect(state.pincode).toBe("201014");
    expect(state.lines).toHaveLength(1);
    expect(state.lines[0].quantity).toBe(2);
  });

  it("never exceeds the stock available", () => {
    let state = EMPTY_CART;
    for (let i = 0; i < 5; i++) state = add(state);

    expect(state.lines[0].quantity).toBe(3);
    expect(cartReducer(state, { type: "setQuantity", medicineId: "m1", quantity: 99 }).lines[0].quantity).toBe(3);
  });

  it("removes a line when its quantity drops to zero", () => {
    const state = cartReducer(add(EMPTY_CART), { type: "setQuantity", medicineId: "m1", quantity: 0 });

    expect(state.lines).toEqual([]);
  });

  it("starts a new cart when adding from a different store", () => {
    const state = add(add(EMPTY_CART), rx, "s2");

    expect(state.storeId).toBe("s2");
    expect(state.lines.map((l) => l.medicine_id)).toEqual(["m2"]);
  });

  it("clears", () => {
    expect(cartReducer(add(EMPTY_CART), { type: "clear" })).toEqual(EMPTY_CART);
  });
});

describe("loading a saved cart", () => {
  it("restores valid lines and drops broken ones", () => {
    const saved = {
      storeId: "s1",
      pincode: "201014",
      lines: [{ ...otc, quantity: 9 }, { junk: true }, { ...rx, quantity: 0 }],
    } as unknown as CartState;

    const state = cartReducer(EMPTY_CART, { type: "load", state: saved });

    expect(state.lines.map((l) => [l.medicine_id, l.quantity])).toEqual([["m1", 3]]);
  });

  it("falls back to an empty cart for garbage", () => {
    const garbage = { lines: "nope" } as unknown as CartState;

    expect(cartReducer(EMPTY_CART, { type: "load", state: garbage })).toEqual(EMPTY_CART);
  });
});

describe("cart selectors", () => {
  it("totals in paise so floats never drift", () => {
    let state = add(add(add(EMPTY_CART))); // 3 x 28.10
    state = add(state, rx); // 1 x 95.55

    expect(cartTotal(state)).toBe(179.85);
    expect(itemCount(state)).toBe(4);
  });

  it("knows when a prescription is needed", () => {
    expect(needsPrescription(add(EMPTY_CART))).toBe(false);
    expect(needsPrescription(add(add(EMPTY_CART), rx))).toBe(true);
  });
});
