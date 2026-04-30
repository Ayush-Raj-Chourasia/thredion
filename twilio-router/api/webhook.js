const { Buffer } = require("node:buffer");

function readBoolean(value, fallback = false) {
  if (value === undefined) return fallback;
  return ["1", "true", "yes", "on"].includes(String(value).trim().toLowerCase());
}

function readNumber(value, fallback) {
  if (!value) return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function normalizeUrl(url) {
  return String(url || "").trim().replace(/\/+$/, "");
}

function escapeXml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function buildTwiml(message) {
  return (
    '<?xml version="1.0" encoding="UTF-8"?>' +
    "<Response>" +
    `<Message>${escapeXml(message)}</Message>` +
    "</Response>"
  );
}

function parseJsonTargets(rawTargets) {
  if (!rawTargets) return [];

  try {
    const parsed = JSON.parse(rawTargets);
    if (!Array.isArray(parsed)) return [];

    return parsed
      .map((entry) => {
        if (!entry || typeof entry !== "object") return null;
        const name = typeof entry.name === "string" ? entry.name.trim() : "";
        const url = typeof entry.url === "string" ? normalizeUrl(entry.url) : "";
        if (!name || !url) return null;
        const aliases = Array.isArray(entry.aliases)
          ? entry.aliases.filter((alias) => typeof alias === "string" && alias.trim())
          : [];
        return { name, url, aliases };
      })
      .filter(Boolean);
  } catch {
    return [];
  }
}

function getConfig() {
  const defaultUrl = normalizeUrl(process.env.TWILIO_ROUTER_DEFAULT_URL);
  const defaultName = (process.env.TWILIO_ROUTER_DEFAULT_NAME || "default").trim();
  const targets = parseJsonTargets(process.env.TWILIO_ROUTER_TARGETS_JSON);

  return {
    defaultTarget: defaultUrl ? { name: defaultName, url: defaultUrl } : targets[0],
    targets,
    fallbackReply:
      process.env.TWILIO_ROUTER_FALLBACK_REPLY ||
      "Sorry, the router could not reach the selected project right now.",
    validateSignature: readBoolean(process.env.TWILIO_VALIDATE_SIGNATURE, false),
    authToken: process.env.TWILIO_AUTH_TOKEN || process.env.TWILIO_WEBHOOK_AUTH_TOKEN || "",
    timeoutMs: readNumber(process.env.TWILIO_ROUTER_TIMEOUT_MS, 12000),
  };
}

function findTarget(config, routeName) {
  if (!routeName) return config.defaultTarget;
  const normalized = routeName.trim().toLowerCase();
  const match = config.targets.find((target) => {
    if (target.name.toLowerCase() === normalized) return true;
    return (target.aliases || []).some((alias) => alias.toLowerCase() === normalized);
  });
  return match || config.defaultTarget;
}

function parseBodyText(rawBody) {
  if (!rawBody) return {};
  const params = new URLSearchParams(rawBody);
  const fields = {};
  for (const [key, value] of params.entries()) {
    fields[key] = value;
  }
  return fields;
}

function explicitRoute(fields) {
  return (
    fields.Route ||
    fields.route ||
    fields.Project ||
    fields.project ||
    fields.Target ||
    fields.target ||
    ""
  ).trim();
}

function isStatusCallback(fields) {
  return Boolean(fields.MessageStatus || fields.SmsStatus || fields.CallStatus);
}

function parseRequestBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function verifySignature(req, rawBody, fields) {
  const config = getConfig();
  if (!config.validateSignature || !config.authToken) return true;

  const signature = req.headers["x-twilio-signature"];
  if (!signature) return false;

  const crypto = require("node:crypto");
  const url = `https://${req.headers.host}${req.url}`;
  const sortedKeys = Object.keys(fields).sort();
  const data = sortedKeys.reduce((acc, key) => acc + key + fields[key], url);
  const expected = crypto.createHmac("sha1", config.authToken).update(data).digest("base64");

  const signatureBuffer = Buffer.from(signature);
  const expectedBuffer = Buffer.from(expected);
  if (signatureBuffer.length !== expectedBuffer.length) return false;
  return crypto.timingSafeEqual(signatureBuffer, expectedBuffer);
}

function buildForwardHeaders(req, decision) {
  return {
    Accept: req.headers.accept || "application/xml, text/xml, text/plain, application/json",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Twilio-Router-Route": decision.routeName,
    "X-Twilio-Router-Reason": decision.reason,
  };
}

async function forwardRequest(req, rawBody, fields, decision) {
  const config = getConfig();
  const body = new URLSearchParams();

  for (const [key, value] of Object.entries(fields)) {
    body.set(key, key === "Body" ? decision.routedBody : value);
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), config.timeoutMs);

  try {
    const response = await fetch(decision.target.url, {
      method: "POST",
      headers: buildForwardHeaders(req, decision),
      body: body.toString(),
      signal: controller.signal,
    });

    const contentType = response.headers.get("content-type") || "";
    const text = await response.text();

    if (contentType.includes("xml") || contentType.includes("text/plain")) {
      return { status: response.status, body: text, contentType: contentType || "application/xml" };
    }

    if (!response.ok) {
      return { status: 200, body: buildTwiml(config.fallbackReply), contentType: "application/xml" };
    }

    if (contentType.includes("application/json")) {
      try {
        const parsed = JSON.parse(text);
        const reply =
          typeof parsed.reply === "string"
            ? parsed.reply
            : typeof parsed.message === "string"
              ? parsed.message
              : `Routed to ${decision.target.name}`;
        return { status: response.status, body: buildTwiml(reply), contentType: "application/xml" };
      } catch {
        return { status: response.status, body: buildTwiml(`Routed to ${decision.target.name}`), contentType: "application/xml" };
      }
    }

    return { status: response.status, body: buildTwiml(`Routed to ${decision.target.name}`), contentType: "application/xml" };
  } catch {
    return { status: 200, body: buildTwiml(config.fallbackReply), contentType: "application/xml" };
  } finally {
    clearTimeout(timeout);
  }
}

module.exports = async (req, res) => {
  if (req.method === "GET") {
    const config = getConfig();
    res.status(200).json({
      status: "ok",
      service: "twilio-router",
      routes: [config.defaultTarget?.name, ...config.targets.map((target) => target.name)].filter(Boolean),
      message: "Twilio router is active.",
    });
    return;
  }

  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  try {
    const rawBody = await parseRequestBody(req);
    const fields = parseBodyText(rawBody);

    if (!Object.keys(fields).length) {
      res.status(400).setHeader("Content-Type", "application/xml").send(buildTwiml("Twilio router expects form-encoded webhook payloads."));
      return;
    }

    if (!verifySignature(req, rawBody, fields)) {
      res.status(403).setHeader("Content-Type", "application/xml").send(buildTwiml("Invalid Twilio signature."));
      return;
    }

    if (isStatusCallback(fields)) {
      res.status(204).end();
      return;
    }

    const body = String(fields.Body || "");
    if (!body.trim()) {
      res.status(200).setHeader("Content-Type", "application/xml").send(buildTwiml("Send a message body or configure a default route."));
      return;
    }

    const config = getConfig();
    const routeName = explicitRoute(fields) || (body.match(/^\[([a-zA-Z0-9_-]+)\]/)?.[1] || "").trim();
    const target = findTarget(config, routeName);

    if (!target) {
      res.status(200).setHeader("Content-Type", "application/xml").send(buildTwiml(config.fallbackReply));
      return;
    }

    const routedBody = body.replace(/^\[[a-zA-Z0-9_-]+\]\s*/, "");
    const decision = {
      target,
      routedBody,
      routeName: routeName || target.name,
      reason: routeName ? "explicit route" : "default route",
    };

    const forwarded = await forwardRequest(req, rawBody, fields, decision);
    res.status(forwarded.status).setHeader("Content-Type", forwarded.contentType).send(forwarded.body);
  } catch (error) {
    res.status(500).setHeader("Content-Type", "application/xml").send(buildTwiml(`Router error: ${error instanceof Error ? error.message : "Unknown router failure"}`));
  }
};