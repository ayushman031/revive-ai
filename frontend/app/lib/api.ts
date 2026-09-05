/**
 * A simple, reusable API client wrapper over fetch to keep things clean and DRY.
 * Enforces the merchant_id across all calls.
 */

// We use a hardcoded dummy merchant_id for the frontend for now,
// or we can expect it to be passed. The user requested:
// "For development, use merchant_id as an explicit request parameter where necessary."
export const DEFAULT_MERCHANT_ID = process.env.NEXT_PUBLIC_MERCHANT_ID || "99999999-9999-9999-9999-999999999999";

// Ensure we default to localhost:8000 if env var is empty or undefined
const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
const API_BASE_URL = (envApiUrl && envApiUrl.trim() !== "") ? envApiUrl : "http://localhost:8000";

export async function fetchApi<T>(endpoint: string, params: Record<string, string | number> = {}): Promise<T> {
  const url = new URL(`${API_BASE_URL}${endpoint}`);

  // Enforce merchant_id
  if (!params.merchant_id) {
    url.searchParams.append("merchant_id", DEFAULT_MERCHANT_ID);
  }

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value));
    }
  }

  const response = await fetch(url.toString(), {
    headers: {
      "Content-Type": "application/json",
    },
    // We can add revalidate/cache options here if needed, but for dashboard it's usually no-store
    cache: 'no-store',
  });

  if (!response.ok) {
    let errorMessage = "API error";
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // Ignored
    }
    throw new Error(`Error ${response.status}: ${errorMessage}`);
  }

  return response.json();
}
