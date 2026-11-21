import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { server } from "@/test/server";

import { ApiError, createApiClient } from "./client";

function tokens(initial: string | null, refreshed: string | null = null) {
  let current = initial;
  return {
    getAccessToken: () => current,
    refreshAccessToken: vi.fn(async () => {
      current = refreshed;
      return refreshed;
    }),
  };
}

describe("createApiClient", () => {
  it("sends the bearer token to /backend", async () => {
    let auth: string | null = null;
    server.use(
      http.get("*/backend/auth/me", ({ request }) => {
        auth = request.headers.get("authorization");
        return HttpResponse.json({ id: "u1" });
      }),
    );

    const body = await createApiClient(tokens("t-1")).get<{ id: string }>("/auth/me");

    expect(body).toEqual({ id: "u1" });
    expect(auth).toBe("Bearer t-1");
  });

  it("refreshes once on 401 and retries with the new token", async () => {
    const seen: (string | null)[] = [];
    server.use(
      http.get("*/backend/orders", ({ request }) => {
        seen.push(request.headers.get("authorization"));
        return seen.length === 1
          ? HttpResponse.json({ detail: "expired" }, { status: 401 })
          : HttpResponse.json([]);
      }),
    );
    const source = tokens("old", "new");

    await createApiClient(source).get("/orders");

    expect(seen).toEqual(["Bearer old", "Bearer new"]);
    expect(source.refreshAccessToken).toHaveBeenCalledTimes(1);
  });

  it("gives up after one refresh", async () => {
    server.use(http.get("*/backend/orders", () => HttpResponse.json({ detail: "no" }, { status: 401 })));
    const source = tokens("old", "still-bad");

    await expect(createApiClient(source).get("/orders")).rejects.toMatchObject({ status: 401 });
    expect(source.refreshAccessToken).toHaveBeenCalledTimes(1);
  });

  it("turns error responses into ApiError with detail, request id and retry-after", async () => {
    server.use(
      http.post("*/backend/orders", () =>
        HttpResponse.json(
          { detail: "Insufficient stock for Dolo 650" },
          { status: 409, headers: { "X-Request-ID": "req-9", "Retry-After": "5" } },
        ),
      ),
    );

    const error = await createApiClient(tokens("t")).post("/orders", {}).catch((e) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 409,
      message: "Insufficient stock for Dolo 650",
      requestId: "req-9",
      retryAfter: 5,
    });
  });

  it("flattens FastAPI validation errors into one readable message", async () => {
    server.use(
      http.post("*/backend/auth/register", () =>
        HttpResponse.json(
          {
            detail: [
              { loc: ["body", "password"], msg: "String should have at least 8 characters" },
              { loc: ["body", "email"], msg: "value is not a valid email address" },
            ],
          },
          { status: 422 },
        ),
      ),
    );

    const error = (await createApiClient(tokens(null)).post("/auth/register", {}).catch((e) => e)) as ApiError;

    expect(error.message).toBe(
      "password: String should have at least 8 characters; email: value is not a valid email address",
    );
  });

  it("returns undefined for 204 responses and sends FormData untouched", async () => {
    let contentType: string | null = "";
    server.use(
      http.post("*/backend/prescriptions", ({ request }) => {
        contentType = request.headers.get("content-type");
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const form = new FormData();
    form.append("file", new Blob(["%PDF-1.4"], { type: "application/pdf" }), "rx.pdf");

    expect(await createApiClient(tokens("t")).post("/prescriptions", form)).toBeUndefined();
    expect(contentType).toMatch(/^multipart\/form-data; boundary=/);
  });
});
