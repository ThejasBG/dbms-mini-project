import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const base = (process.env.STEAMISH_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
  const url = new URL(`${base}/api/${path.map(encodeURIComponent).join("/")}`);
  url.search = request.nextUrl.search;

  const headers = new Headers();
  const cookie = request.headers.get("cookie");
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");
  if (cookie) headers.set("cookie", cookie);
  if (contentType) headers.set("content-type", contentType);
  if (accept) headers.set("accept", accept);

  const options: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
    redirect: "manual",
  };
  if (!["GET", "HEAD"].includes(request.method)) {
    options.body = await request.arrayBuffer();
  }

  let upstream: Response;
  try {
    upstream = await fetch(url, options);
  } catch {
    return Response.json(
      { detail: "Python API is unavailable. Start it with: python -m uvicorn backend.http_api:app --host 127.0.0.1 --port 8000 --reload" },
      { status: 503 },
    );
  }

  const outHeaders = new Headers();
  const outType = upstream.headers.get("content-type");
  const setCookie = upstream.headers.get("set-cookie");
  if (outType) outHeaders.set("content-type", outType);
  if (setCookie) outHeaders.set("set-cookie", setCookie);
  return new Response(upstream.status === 204 ? null : await upstream.arrayBuffer(), {
    status: upstream.status,
    headers: outHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
export const PATCH = proxy;
