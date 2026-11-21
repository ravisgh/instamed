import { NextRequest, NextResponse } from "next/server";

import {
  API_URL,
  clearSession,
  forwardHeaders,
  passThroughError,
  readRefreshToken,
  sessionResponse,
} from "@/lib/server/session";

/** Log in: exchange email + password for a session (refresh token goes into a cookie). */
export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as { email?: unknown; password?: unknown } | null;
  if (typeof body?.email !== "string" || typeof body?.password !== "string") {
    return NextResponse.json({ detail: "email and password are required" }, { status: 400 });
  }

  const upstream = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded", ...forwardHeaders(req) },
    body: new URLSearchParams({ username: body.email, password: body.password }),
  });
  if (!upstream.ok) return passThroughError(upstream);
  return sessionResponse(await upstream.json());
}

/** Log out: revoke the refresh token family on the API and drop the cookie. */
export async function DELETE(req: NextRequest) {
  const refreshToken = readRefreshToken(req);
  if (refreshToken) {
    await fetch(`${API_URL}/auth/logout`, {
      method: "POST",
      headers: { "content-type": "application/json", ...forwardHeaders(req) },
      body: JSON.stringify({ refresh_token: refreshToken }),
    }).catch(() => undefined); // logging out locally must work even if the API is down
  }
  return clearSession(new NextResponse(null, { status: 204 }));
}
