// @vitest-environment node
import { http, HttpResponse } from "msw";
import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { REFRESH_COOKIE } from "@/lib/server/session";
import { server } from "@/test/server";

import { POST as refresh } from "./refresh/route";
import { DELETE as logout, POST as login } from "./route";

const API = "http://127.0.0.1:8000";
const TOKENS = { access_token: "access-1", refresh_token: "refresh-1", token_type: "bearer", expires_in: 900 };

function request(method: string, path: string, init: { body?: unknown; cookie?: string; ip?: string } = {}) {
  const headers = new Headers({ "content-type": "application/json" });
  if (init.cookie) headers.set("cookie", `${REFRESH_COOKIE}=${init.cookie}`);
  if (init.ip) headers.set("x-forwarded-for", init.ip);
  return new NextRequest(`http://localhost:3000${path}`, {
    method,
    headers,
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
  });
}

describe("POST /api/session (login)", () => {
  it("returns only the access token and keeps the refresh token in an httpOnly cookie", async () => {
    let sent: { form: string; forwardedFor: string | null } | undefined;
    server.use(
      http.post(`${API}/auth/login`, async ({ request: req }) => {
        sent = { form: await req.text(), forwardedFor: req.headers.get("x-forwarded-for") };
        return HttpResponse.json(TOKENS);
      }),
    );

    const res = await login(
      request("POST", "/api/session", { body: { email: "a@example.com", password: "pw-123456" }, ip: "203.0.113.9" }),
    );

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ access_token: "access-1", expires_in: 900 });
    const cookie = res.headers.get("set-cookie") ?? "";
    expect(cookie).toContain(`${REFRESH_COOKIE}=refresh-1`);
    expect(cookie).toMatch(/HttpOnly/i);
    expect(cookie).toMatch(/SameSite=strict/i);
    expect(cookie).toContain("Path=/api/session");
    expect(sent?.form).toBe("username=a%40example.com&password=pw-123456");
    expect(sent?.forwardedFor).toBe("203.0.113.9");
  });

  it("passes through login failures and rate limits without setting a cookie", async () => {
    server.use(
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json({ detail: "Too many attempts, try again later" }, { status: 429, headers: { "Retry-After": "42" } }),
      ),
    );

    const res = await login(request("POST", "/api/session", { body: { email: "a@example.com", password: "x" } }));

    expect(res.status).toBe(429);
    expect(res.headers.get("retry-after")).toBe("42");
    expect(await res.json()).toEqual({ detail: "Too many attempts, try again later" });
    expect(res.headers.get("set-cookie")).toBeNull();
  });

  it("rejects a malformed body", async () => {
    const res = await login(request("POST", "/api/session", { body: { email: 5 } }));

    expect(res.status).toBe(400);
  });
});

describe("POST /api/session/refresh", () => {
  it("is 401 without a cookie", async () => {
    const res = await refresh(request("POST", "/api/session/refresh"));

    expect(res.status).toBe(401);
  });

  it("rotates the cookie and returns a new access token", async () => {
    let sentToken: unknown;
    server.use(
      http.post(`${API}/auth/refresh`, async ({ request: req }) => {
        sentToken = ((await req.json()) as { refresh_token: string }).refresh_token;
        return HttpResponse.json({ ...TOKENS, access_token: "access-2", refresh_token: "refresh-2" });
      }),
    );

    const res = await refresh(request("POST", "/api/session/refresh", { cookie: "refresh-1" }));

    expect(sentToken).toBe("refresh-1");
    expect(await res.json()).toEqual({ access_token: "access-2", expires_in: 900 });
    expect(res.headers.get("set-cookie")).toContain(`${REFRESH_COOKIE}=refresh-2`);
  });

  it("clears the cookie when the backend rejects the refresh token", async () => {
    server.use(http.post(`${API}/auth/refresh`, () => HttpResponse.json({ detail: "nope" }, { status: 401 })));

    const res = await refresh(request("POST", "/api/session/refresh", { cookie: "stolen" }));

    expect(res.status).toBe(401);
    expect(res.headers.get("set-cookie")).toMatch(new RegExp(`${REFRESH_COOKIE}=;`));
  });
});

describe("DELETE /api/session (logout)", () => {
  it("revokes the session on the backend and clears the cookie", async () => {
    let revoked: unknown;
    server.use(
      http.post(`${API}/auth/logout`, async ({ request: req }) => {
        revoked = ((await req.json()) as { refresh_token: string }).refresh_token;
        return new HttpResponse(null, { status: 204 });
      }),
    );

    const res = await logout(request("DELETE", "/api/session", { cookie: "refresh-1" }));

    expect(res.status).toBe(204);
    expect(revoked).toBe("refresh-1");
    expect(res.headers.get("set-cookie")).toMatch(new RegExp(`${REFRESH_COOKIE}=;`));
  });

  it("is a no-op without a cookie", async () => {
    expect((await logout(request("DELETE", "/api/session"))).status).toBe(204);
  });
});
