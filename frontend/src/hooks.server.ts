import { env } from "$env/dynamic/private";
const { APP_PASSWORD } = env;
import type { Handle } from "@sveltejs/kit";

export const handle: Handle = async ({ event, resolve }) => {
  const authHeader = event.request.headers.get("authorization");

  if (!authHeader || !authHeader.startsWith("Basic ")) {
    return new Response("Unauthorized", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="Lead Seeker"',
      },
    });
  }

  const base64Credentials = authHeader.slice("Basic ".length);
  let credentials: string;

  try {
    credentials = atob(base64Credentials);
  } catch {
    return new Response("Unauthorized", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="Lead Seeker"',
      },
    });
  }

  const colonIndex = credentials.indexOf(":");
  if (colonIndex === -1) {
    return new Response("Unauthorized", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="Lead Seeker"',
      },
    });
  }

  const password = credentials.slice(colonIndex + 1);
  const expectedPassword = APP_PASSWORD;

  // Constant-time comparison to prevent timing attacks
  if (
    !expectedPassword ||
    password.length !== expectedPassword.length ||
    !timingSafeEqual(password, expectedPassword)
  ) {
    return new Response("Unauthorized", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="Lead Seeker"',
      },
    });
  }

  return resolve(event);
};

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}
