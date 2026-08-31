import { supabase } from "@/lib/supabase";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export async function apiFetch(
  path: string,
  init: RequestInit = {}
) {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error("Authentication required.");
  }

  const headers = new Headers(init.headers);

  headers.set(
    "Authorization",
    `Bearer ${session.access_token}`
  );

  if (
    init.body &&
    !(init.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set(
      "Content-Type",
      "application/json"
    );
  }

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...init,
      headers,
    }
  );

  if (response.status === 401) {
    await supabase.auth.signOut();

    throw new Error(
      "Your session expired. Please sign in again."
    );
  }

  return response;
}