import { createHmac, timingSafeEqual } from "crypto";

export type TwilioRouteTarget = {
  name: string;
  url: string;
  aliases?: string[];
};

export type TwilioRouteDecision = {
  target: TwilioRouteTarget;
  routedBody: string;
  routeName: string;
  reason: string;
};

type RouterConfig = {
  defaultTarget?: TwilioRouteTarget;
  targets: TwilioRouteTarget[];
  validateSignature: boolean;
  authToken: string;
  requestTimeoutMs: number;
  fallbackReply: string;
};

export type TwilioWebhookFields = Record<string, string>;

const ROUTE_PREFIX = /^\[([a-zA-Z0-9_-]+)\]\s*/;

function readBoolean(name: string, fallback = false): boolean {
  const value = process.env[name];
  if (value === undefined) return fallback;
  return ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
}

function readNumber(name: string, fallback: number): number {
  const value = process.env[name];
  if (!value) return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function normalizeUrl(url: string): string {
  return url.trim().replace(/\/+$/, "");
}

function readTarget(name: string, url?: string | null): TwilioRouteTarget | null {
  if (!url) return null;
  const trimmedUrl = normalizeUrl(url);
  if (!trimmedUrl) return null;
  return { name, url: trimmedUrl };
}

function readTargetsFromEnv(rawTargets: string | undefined): TwilioRouteTarget[] {
  if (!rawTargets) return [];

  try {
    const parsed = JSON.parse(rawTargets) as unknown;
    if (!Array.isArray(parsed)) return [];

    const targets: TwilioRouteTarget[] = [];

    for (const entry of parsed) {
      if (!entry || typeof entry !== "object") continue;
      const candidate = entry as Record<string, unknown>;
      const name = typeof candidate.name === "string" && candidate.name.trim() ? candidate.name.trim() : null;
      const url = typeof candidate.url === "string" ? candidate.url : null;
      if (!name || !url) continue;
      const aliases = Array.isArray(candidate.aliases)
        ? candidate.aliases.filter((alias): alias is string => typeof alias === "string" && alias.trim().length > 0)
        : [];
      const target = readTarget(name, url);
      if (target) {
        targets.push({ ...target, aliases });
      }
    }

    return targets;
  } catch {
    return [];
  }
}

export function getRouterConfig(): RouterConfig {
  const targets = readTargetsFromEnv(process.env.TWILIO_ROUTER_TARGETS_JSON);
  const defaultTarget = readTarget(
    process.env.TWILIO_ROUTER_DEFAULT_NAME || "default",
    process.env.TWILIO_ROUTER_DEFAULT_URL
  );

  return {
    defaultTarget: defaultTarget ?? targets[0],
    targets,
    validateSignature: readBoolean("TWILIO_VALIDATE_SIGNATURE", false),
    authToken: process.env.TWILIO_AUTH_TOKEN || process.env.TWILIO_WEBHOOK_AUTH_TOKEN || "",
    requestTimeoutMs: readNumber("TWILIO_ROUTER_TIMEOUT_MS", 12_000),
    fallbackReply:
      process.env.TWILIO_ROUTER_FALLBACK_REPLY ||
      "Sorry, the router could not reach the selected project right now.",
  };
}

export function chooseRoute(fields: TwilioWebhookFields): TwilioRouteDecision {
  const config = getRouterConfig();
  const rawBody = fields.Body || "";
  const explicitRoute = resolveExplicitRoute(fields);
  const match = rawBody.match(ROUTE_PREFIX);
  const requestedRoute = (explicitRoute || match?.[1] || "").trim().toLowerCase();

  const matchedTarget =
    config.targets.find((target) => matchesTarget(target, requestedRoute)) ?? config.defaultTarget;

  if (!matchedTarget) {
    throw new Error("No Twilio route target configured");
  }

  const routedBody = match ? rawBody.slice(match[0].length) : rawBody;

  return {
    target: matchedTarget,
    routedBody,
    routeName: requestedRoute || matchedTarget.name,
    reason: explicitRoute ? "explicit route field" : match ? "body prefix" : "default route",
  };
}

export function buildTwiml(message: string): string {
  return (
    '<?xml version="1.0" encoding="UTF-8"?>' +
    "<Response>" +
    `<Message>${escapeXml(message)}</Message>` +
    "</Response>"
  );
}

export function buildHealthMessage(): string {
  const config = getRouterConfig();
  const routeNames = [config.defaultTarget?.name, ...config.targets.map((target) => target.name)].filter(Boolean);
  return `Twilio router is active. Routes: ${routeNames.join(", ") || "none"}`;
}

export async function parseTwilioRequest(request: Request): Promise<TwilioWebhookFields> {
  const contentType = request.headers.get("content-type") || "";
  if (!contentType.includes("application/x-www-form-urlencoded") && !contentType.includes("multipart/form-data")) {
    return {};
  }

  const form = await request.formData();
  const payload: TwilioWebhookFields = {};

  for (const [key, value] of Array.from(form.entries())) {
    payload[key] = typeof value === "string" ? value : value.name;
  }

  return payload;
}

export function isStatusCallback(fields: TwilioWebhookFields): boolean {
  return Boolean(fields.MessageStatus || fields.SmsStatus || fields.CallStatus);
}

export function verifyTwilioSignature(request: Request, fields: TwilioWebhookFields): boolean {
  const config = getRouterConfig();
  if (!config.validateSignature || !config.authToken) return true;

  const signature = request.headers.get("x-twilio-signature");
  if (!signature) return false;

  const url = new URL(request.url);
  const baseUrl = `${url.origin}${url.pathname}`;
  const sortedKeys = Object.keys(fields).sort();
  const data = sortedKeys.reduce((acc, key) => acc + key + fields[key], baseUrl);
  const expected = createHmac("sha1", config.authToken).update(data).digest("base64");

  const signatureBuffer = Buffer.from(signature);
  const expectedBuffer = Buffer.from(expected);
  if (signatureBuffer.length !== expectedBuffer.length) return false;

  return timingSafeEqual(signatureBuffer, expectedBuffer);
}

export async function forwardToTarget(request: Request, fields: TwilioWebhookFields): Promise<Response> {
  const config = getRouterConfig();

  if (isStatusCallback(fields)) {
    return new Response(null, { status: 204 });
  }

  const decision = chooseRoute(fields);
  const form = new FormData();
  for (const [key, value] of Object.entries(fields)) {
    form.set(key, key === "Body" ? decision.routedBody : value);
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), config.requestTimeoutMs);

  try {
    const outbound = await fetch(decision.target.url, {
      method: "POST",
      headers: {
        Accept: request.headers.get("accept") || "application/xml, text/xml, text/plain, application/json",
        "X-Twilio-Router-Route": decision.routeName,
        "X-Twilio-Router-Reason": decision.reason,
      },
      signal: controller.signal,
      body: form,
    });

    const contentType = outbound.headers.get("content-type") || "";
    const text = await outbound.text();

    if (contentType.includes("xml") || contentType.includes("text/plain")) {
      return new Response(text, {
        status: outbound.status,
        headers: { "content-type": contentType || "application/xml" },
      });
    }

    if (!outbound.ok) {
      return new Response(buildTwiml(config.fallbackReply), {
        status: 200,
        headers: { "content-type": "application/xml" },
      });
    }

    if (contentType.includes("application/json")) {
      try {
        const payload = JSON.parse(text) as Record<string, unknown>;
        const reply =
          typeof payload.reply === "string"
            ? payload.reply
            : typeof payload.message === "string"
              ? payload.message
              : `Routed to ${decision.target.name}`;
        return new Response(buildTwiml(reply), {
          status: outbound.status,
          headers: { "content-type": "application/xml" },
        });
      } catch {
        // Fall through to XML wrapper below.
      }
    }

    return new Response(buildTwiml(`Routed to ${decision.target.name}`), {
      status: outbound.status,
      headers: { "content-type": "application/xml" },
    });
  } catch {
    return new Response(buildTwiml(config.fallbackReply), {
      status: 200,
      headers: { "content-type": "application/xml" },
    });
  } finally {
    clearTimeout(timeout);
  }
}

function resolveExplicitRoute(fields: TwilioWebhookFields): string {
  const candidate = fields.Route || fields.route || fields.Project || fields.project || fields.Target || fields.target;
  return candidate ? candidate.trim() : "";
}

function matchesTarget(target: TwilioRouteTarget, routeName: string): boolean {
  if (!routeName) return false;
  const normalized = routeName.toLowerCase();
  if (target.name.toLowerCase() === normalized) return true;
  return (target.aliases || []).some((alias) => alias.toLowerCase() === normalized);
}

function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}