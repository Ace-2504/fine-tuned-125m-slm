/**
 * Server-side proxy to the SFT inference server (sft/sft_server.py), reached through a
 * Cloudflare tunnel. Keeps the tunnel URL (and any secret) server-side and sidesteps CORS.
 *
 * Env (set in Vercel project settings / .env.local):
 *   INFERENCE_URL     tunnel origin, e.g. https://<something>.trycloudflare.com
 *   INFERENCE_SECRET  optional; only if the server sets API_SECRET
 */
import { NextResponse } from "next/server";

const BASE = process.env.INFERENCE_URL ?? "";
const SECRET = process.env.INFERENCE_SECRET;

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  if (!BASE) {
    return NextResponse.json(
      { error: "not_configured", detail: "INFERENCE_URL is not set — the demo backend is offline." },
      { status: 503 }
    );
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "bad_request" }, { status: 400 });
  }

  const question = String(body.question ?? "").trim();
  if (!question) return NextResponse.json({ error: "empty_question" }, { status: 400 });

  const payload = {
    question: question.slice(0, 2000),
    system: String(body.system ?? "You are a precise legal and financial assistant."),
    max_new_tokens: Math.min(256, Number(body.max_new_tokens ?? 120)),
    temperature: Math.max(0, Math.min(1.5, Number(body.temperature ?? 0.7))),
  };

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 120_000);
  try {
    const res = await fetch(`${BASE.replace(/\/$/, "")}/compare`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(SECRET ? { authorization: `Bearer ${SECRET}` } : {}),
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
      cache: "no-store",
    });
    const text = await res.text();
    if (!res.ok) {
      return NextResponse.json(
        { error: "upstream", status: res.status, detail: text.slice(0, 300) },
        { status: 502 }
      );
    }
    return new NextResponse(text, {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  } catch (e) {
    const offline = e instanceof Error && e.name === "AbortError" ? "timeout" : "unreachable";
    return NextResponse.json(
      { error: offline, detail: "The local inference server isn't reachable right now." },
      { status: 503 }
    );
  } finally {
    clearTimeout(timer);
  }
}
