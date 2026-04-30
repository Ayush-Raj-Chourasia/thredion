import { NextResponse } from "next/server";

import {
  buildHealthMessage,
  buildTwiml,
  forwardToTarget,
  getRouterConfig,
  isStatusCallback,
  parseTwilioRequest,
  verifyTwilioSignature,
} from "@/lib/twilio-router";

export const runtime = "nodejs";

export async function GET() {
  const config = getRouterConfig();
  return NextResponse.json({
    status: "ok",
    service: "twilio-router",
    routes: [
      config.defaultTarget ? config.defaultTarget.name : null,
      ...config.targets.map((target) => target.name),
    ].filter(Boolean),
    message: buildHealthMessage(),
  });
}

export async function POST(request: Request) {
  try {
    const fields = await parseTwilioRequest(request);

    if (Object.keys(fields).length === 0) {
      return new NextResponse(buildTwiml("Twilio router expects form-encoded webhook payloads."), {
        status: 400,
        headers: { "content-type": "application/xml" },
      });
    }

    if (!verifyTwilioSignature(request, fields)) {
      return new NextResponse(buildTwiml("Invalid Twilio signature."), {
        status: 403,
        headers: { "content-type": "application/xml" },
      });
    }

    if (isStatusCallback(fields)) {
      return new NextResponse(null, { status: 204 });
    }

    const body = String(fields.Body || "");

    if (!body.trim()) {
      return new NextResponse(buildTwiml("Send a message body or configure a default route."), {
        status: 200,
        headers: { "content-type": "application/xml" },
      });
    }

    return forwardToTarget(request, fields);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown router failure";
    return new NextResponse(buildTwiml(`Router error: ${message}`), {
      status: 500,
      headers: { "content-type": "application/xml" },
    });
  }
}