const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");
const apiBaseUrl = configuredBaseUrl || "/api";

function responseMessage(payload) {
  if (typeof payload?.detail === "string") return payload.detail;

  if (Array.isArray(payload?.detail)) {
    return payload.detail
      .map((issue) => issue.msg || issue.message)
      .filter(Boolean)
      .join(" · ");
  }

  return "The marketplace service could not complete this run.";
}

export async function runMarketplace(request) {
  let response;

  try {
    response = await fetch(`${apiBaseUrl}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
  } catch {
    throw new Error(
      "Unable to reach the marketplace API. Confirm the backend is running and the development proxy is available.",
    );
  }

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(responseMessage(payload));
  }

  return payload;
}
