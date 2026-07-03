const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function getApiBaseUrl() {
  const rawUrl = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
  return (rawUrl || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
}

function buildUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getApiBaseUrl()}${normalizedPath}`;
}

function isJsonResponse(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";
  return contentType.includes("application/json");
}

async function readResponseBody(response: Response) {
  if (isJsonResponse(response)) {
    return response.json();
  }

  const text = await response.text();
  return text ? { detail: text } : null;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(buildUrl(path), {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.headers as Record<string, string> | undefined),
    },
  });

  const body = await readResponseBody(response);

  if (!response.ok) {
    const message =
      typeof body === "object" && body && "detail" in body
        ? String((body as { detail?: unknown }).detail ?? `Request failed (${response.status})`)
        : `Request failed (${response.status})`;

    throw new ApiError(message, response.status, body);
  }

  return body as T;
}
