import { NextRequest, NextResponse } from "next/server";

import { API_URL, clearSession, forwardHeaders, readRefreshToken, sessionResponse } from "@/lib/server/session";

/**
 * Swap the refresh-token cookie for a new access token (and a rotated cookie).
 * Called on page load (silent login) and whenever the API answers 401.
 */
export async function POST(req: NextRequest) {
  const refreshToken = readRefreshToken(req);
  if (!refreshToken) {
    return NextResponse.json({ detail: "Not logged in" }, { status: 401 });
  }

  const upstream = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "content-type": "application/json", ...forwardHeaders(req) },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!upstream.ok) {
    // Expired, revoked or reused: the cookie is worthless, so remove it.
    return clearSession(NextResponse.json({ detail: "Session expired" }, { status: 401 }));
  }
  return sessionResponse(await upstream.json());
}
