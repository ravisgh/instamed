import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { push, setSearchParams } from "@/test/navigation";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/server";

import { LoginForm } from "./LoginForm";
import { RegisterForm } from "./RegisterForm";

vi.mock("next/navigation", async () => (await import("@/test/navigation")).navigationMock());

beforeEach(() => {
  push.mockClear();
  setSearchParams("");
});

describe("LoginForm", () => {
  it("logs in and returns to the page that asked for it", async () => {
    setSearchParams("next=/checkout");
    server.use(http.post("*/api/session", () => HttpResponse.json({ access_token: "t", expires_in: 900 })));
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "asha@example.com");
    await user.type(screen.getByLabelText(/password/i), "pw-123456");
    await user.click(screen.getByRole("button", { name: /log in/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/checkout"));
  });

  it("never redirects to another site", async () => {
    setSearchParams("next=https://evil.example/steal");
    server.use(http.post("*/api/session", () => HttpResponse.json({ access_token: "t", expires_in: 900 })));
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "asha@example.com");
    await user.type(screen.getByLabelText(/password/i), "pw-123456");
    await user.click(screen.getByRole("button", { name: /log in/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/"));
  });

  it("shows wrong-password and rate-limit errors", async () => {
    server.use(
      http.post("*/api/session", () =>
        HttpResponse.json({ detail: "Too many attempts, try again later" }, { status: 429, headers: { "Retry-After": "30" } }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<LoginForm />);

    await user.type(screen.getByLabelText(/email/i), "asha@example.com");
    await user.type(screen.getByLabelText(/password/i), "wrong-pass");
    await user.click(screen.getByRole("button", { name: /log in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Too many attempts, try again later (wait 30s)");
    expect(push).not.toHaveBeenCalled();
  });
});

describe("RegisterForm", () => {
  it("creates the account, logs in and goes home", async () => {
    let sent: unknown;
    server.use(
      http.post("*/backend/auth/register", async ({ request }) => {
        sent = await request.json();
        return HttpResponse.json({ id: "u2" }, { status: 201 });
      }),
      http.post("*/api/session", () => HttpResponse.json({ access_token: "t", expires_in: 900 })),
    );
    const user = userEvent.setup();
    renderWithProviders(<RegisterForm />);

    await user.type(screen.getByLabelText(/full name/i), "Asha Verma");
    await user.type(screen.getByLabelText(/email/i), "asha@example.com");
    await user.type(screen.getByLabelText(/password/i), "long-enough-1");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/"));
    expect(sent).toEqual({ full_name: "Asha Verma", email: "asha@example.com", password: "long-enough-1" });
  });

  it("shows server validation messages", async () => {
    server.use(
      http.post("*/backend/auth/register", () => HttpResponse.json({ detail: "User already exists" }, { status: 409 })),
    );
    const user = userEvent.setup();
    renderWithProviders(<RegisterForm />);

    await user.type(screen.getByLabelText(/full name/i), "Asha");
    await user.type(screen.getByLabelText(/email/i), "asha@example.com");
    await user.type(screen.getByLabelText(/password/i), "long-enough-1");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("User already exists");
  });
});
