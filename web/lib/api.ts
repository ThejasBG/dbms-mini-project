export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("Accept", "application/json");
  let response: Response;
  try {
    response = await fetch(path, { ...init, headers, credentials: "same-origin", cache: "no-store" });
  } catch {
    throw new ApiError(0, "The application API could not be reached. Check that the Python API is running.");
  }

  const contentType = response.headers.get("content-type") || "";
  const data: unknown = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const detail = data && typeof data === "object" && "detail" in data
      ? (data as { detail?: unknown }).detail
      : undefined;
    const message = typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map((item: unknown) => {
          if (!item || typeof item !== "object") return String(item);
          const issue = item as { loc?: (string | number)[]; msg?: string };
          return `${issue.loc?.slice(-1)[0] ?? "Input"}: ${issue.msg ?? "is invalid"}`;
        }).join("; ")
        : `Request failed (${response.status}).`;
    throw new ApiError(response.status, message);
  }
  return data as T;
}

export function jsonBody(value: unknown): string {
  return JSON.stringify(value);
}
