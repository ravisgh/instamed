import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "./server";

// Every network call in tests goes through MSW; an unhandled request fails the test.
beforeAll(() => server.listen({ onUnhandledFrame: "error" }));
afterEach(() => {
  server.resetHandlers();
  // Route-handler tests run in the "node" environment, which has no DOM.
  if (typeof window !== "undefined") {
    cleanup();
    window.localStorage.clear();
  }
});
afterAll(() => server.close());
