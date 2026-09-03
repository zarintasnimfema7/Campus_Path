import { useAuth, useClerk } from "@clerk/nextjs";
import { useCallback } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export function useApiFetch() {
  const { getToken } = useAuth();
  const { signOut } = useClerk();

  return useCallback(async (
    path: string,
    init: RequestInit = {}
  ) => {
  const token = await getToken();

  if (!token) {
    throw new Error("Authentication required.");
  }

  const headers = new Headers(init.headers);

  headers.set(
    "Authorization",
    `Bearer ${token}`
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
    await signOut();

    throw new Error(
      "Your session expired. Please sign in again."
    );
  }

  return response;
  }, [getToken, signOut]);
}
