import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { StrictMode } from "react";
import { describe, expect, it } from "vitest";

import { server } from "@/test/server";

import { AuthProvider, useAuth } from "./AuthProvider";

const USER = { id: "u1", email: "asha@example.com", full_name: "Asha", role: "customer", is_active: true };

function Probe() {
  const { status, user, login, logout } = useAuth();
  return (
    <div>
      <p data-testid="status">{status}</p>
      <p data-testid="user">{user?.email ?? "-"}</p>
      <button onClick={() => login("asha@example.com", "pw-123456").catch(() => undefined)}>login</button>
      <button onClick={() => logout()}>logout</button>
    </div>
  );
}

function renderAuth() {
  return render(
    <StrictMode>
      <AuthProvider>
        <Probe />
      </AuthProvider>
    </StrictMode>,
  );
}

describe("AuthProvider", () => {
  it("restores the session on load with a single refresh, even under StrictMode", async () => {
    let refreshCalls = 0;
    server.use(
      http.post("*/api/session/refresh", () => {
        refreshCalls += 1;
        return HttpResponse.json({ access_token: "a1", expires_in: 900 });
      }),
      http.get("*/backend/auth/me", ({ request }) =>
        request.headers.get("authorization") === "Bearer a1"
          ? HttpResponse.json(USER)
          : HttpResponse.json({ detail: "no" }, { status: 401 }),
      ),
    );

    renderAuth();

    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("authenticated"));
    expect(screen.getByTestId("user")).toHaveTextContent("asha@example.com");
    expect(refreshCalls).toBe(1);
  });

  it("is anonymous when there is no session cookie", async () => {
    server.use(http.post("*/api/session/refresh", () => HttpResponse.json({ detail: "x" }, { status: 401 })));

    renderAuth();

    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("anonymous"));
  });

  it("logs in and out", async () => {
    server.use(
      http.post("*/api/session/refresh", () => HttpResponse.json({ detail: "x" }, { status: 401 })),
      http.post("*/api/session", () => HttpResponse.json({ access_token: "a2", expires_in: 900 })),
      http.get("*/backend/auth/me", () => HttpResponse.json(USER)),
      http.delete("*/api/session", () => new HttpResponse(null, { status: 204 })),
    );
    renderAuth();
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("anonymous"));

    await userEvent.click(screen.getByText("login"));
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("asha@example.com"));

    await userEvent.click(screen.getByText("logout"));
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("anonymous"));
    expect(screen.getByTestId("user")).toHaveTextContent("-");
  });
});
