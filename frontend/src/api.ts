export async function api(path: string, method = "GET", body?: unknown) {
  const r = await fetch("/api/" + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  return data;
}
export function formatSeconds(n: number | null | undefined): string {
  if (n === null || n === undefined || !Number.isFinite(n))
    return "Unavailable";
  return n < 60
    ? `${n.toFixed(1)} sec`
    : n < 3600
      ? `${(n / 60).toFixed(1)} min`
      : `${(n / 3600).toFixed(1)} hr`;
}
