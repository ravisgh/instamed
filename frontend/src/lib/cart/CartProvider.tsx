"use client";

import { createContext, useContext, useEffect, useReducer, useRef } from "react";

import type { StockHit } from "@/lib/api/types";

import { type CartState, cartReducer, cartTotal, EMPTY_CART, itemCount, needsPrescription } from "./cart";

const STORAGE_KEY = "instamed.cart.v1";

interface CartContextValue {
  cart: CartState;
  count: number;
  total: number;
  needsPrescription: boolean;
  add(hit: StockHit, storeId: string, pincode: string): void;
  setQuantity(medicineId: string, quantity: number): void;
  clear(): void;
}

const CartContext = createContext<CartContextValue | null>(null);

function loadCart(): CartState {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    return saved ? (JSON.parse(saved) as CartState) : EMPTY_CART;
  } catch {
    return EMPTY_CART; // storage blocked or corrupted: start empty
  }
}

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [cart, dispatch] = useReducer(cartReducer, EMPTY_CART);
  const firstRender = useRef(true);

  // Read storage after mount so server and first client render match.
  useEffect(() => {
    dispatch({ type: "load", state: loadCart() });
  }, []);

  useEffect(() => {
    // Skip the initial empty cart, or it would overwrite the saved one before loading.
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
    } catch {
      // ignore: the cart still works for this page view
    }
  }, [cart]);

  const value: CartContextValue = {
    cart,
    count: itemCount(cart),
    total: cartTotal(cart),
    needsPrescription: needsPrescription(cart),
    add: (hit, storeId, pincode) => dispatch({ type: "add", hit, storeId, pincode }),
    setQuantity: (medicineId, quantity) => dispatch({ type: "setQuantity", medicineId, quantity }),
    clear: () => dispatch({ type: "clear" }),
  };
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used inside <CartProvider>");
  return ctx;
}
