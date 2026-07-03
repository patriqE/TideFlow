import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { ApiError, apiRequest } from "@/lib/api";
import {
  AuthTokens,
  clearAuthTokens,
  loadAuthTokens,
  saveAuthTokens,
} from "@/lib/auth-storage";

type LoginResponse = {
  access: string;
  refresh: string;
  role?: string | null;
};

type RegisterInput = {
  email?: string;
  phone?: string;
  password: string;
};

type AuthContextValue = {
  isHydrated: boolean;
  isAuthenticated: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  role: string | null;
  login: (identity: string, password: string) => Promise<LoginResponse>;
  register: (input: RegisterInput) => Promise<unknown>;
  refreshSession: () => Promise<boolean>;
  logout: () => Promise<void>;
  authedRequest: <T>(path: string, options?: RequestInit) => Promise<T>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function normalizeLoginPayload(identity: string, password: string) {
  return identity.includes("@")
    ? { email: identity, password }
    : { phone: identity, password };
}

function mergeHeaders(headers: HeadersInit | undefined, extraHeaders: Record<string, string>) {
  if (headers instanceof Headers) {
    const mergedHeaders = new Headers(headers);
    Object.entries(extraHeaders).forEach(([key, value]) => mergedHeaders.set(key, value));
    return mergedHeaders;
  }

  return {
    ...(headers as Record<string, string> | undefined),
    ...extraHeaders,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    let isMounted = true;

    loadAuthTokens()
      .then((storedTokens) => {
        if (isMounted) {
          setTokens(storedTokens);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsHydrated(true);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const persistTokens = useCallback(async (nextTokens: AuthTokens | null) => {
    if (nextTokens) {
      await saveAuthTokens(nextTokens);
    } else {
      await clearAuthTokens();
    }

    setTokens(nextTokens);
  }, []);

  const refreshSession = useCallback(async () => {
    if (!tokens?.refresh) {
      return false;
    }

    try {
      const response = await apiRequest<LoginResponse>("/accounts/refresh/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh: tokens.refresh }),
      });

      await persistTokens({
        access: response.access,
        refresh: response.refresh,
        role: response.role ?? tokens.role ?? null,
      });

      return true;
    } catch {
      await persistTokens(null);
      return false;
    }
  }, [persistTokens, tokens]);

  const login = useCallback(
    async (identity: string, password: string) => {
      const response = await apiRequest<LoginResponse>("/accounts/login/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(normalizeLoginPayload(identity, password)),
      });

      await persistTokens({
        access: response.access,
        refresh: response.refresh,
        role: response.role ?? null,
      });

      return response;
    },
    [persistTokens],
  );

  const register = useCallback(async (input: RegisterInput) => {
    return apiRequest("/accounts/register/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    });
  }, []);

  const logout = useCallback(async () => {
    if (tokens?.refresh) {
      try {
        await apiRequest("/accounts/logout/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ refresh: tokens.refresh }),
        });
      } catch {
        // Local logout should still complete if the backend is unavailable.
      }
    }

    await persistTokens(null);
  }, [persistTokens, tokens]);

  const authedRequest = useCallback(
    async <T,>(path: string, options: RequestInit = {}) => {
      if (!tokens?.access) {
        throw new Error("Authentication required");
      }

      const requestOptions: RequestInit = {
        ...options,
        headers: mergeHeaders(options.headers, {
          Authorization: `Bearer ${tokens.access}`,
        }),
      };

      try {
        return await apiRequest<T>(path, requestOptions);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401 && tokens.refresh) {
          const refreshed = await refreshSession();
          if (refreshed) {
            const restoredTokens = await loadAuthTokens();
            if (restoredTokens?.access) {
              return apiRequest<T>(path, {
                ...options,
                headers: mergeHeaders(options.headers, {
                  Authorization: `Bearer ${restoredTokens.access}`,
                }),
              });
            }
          }
        }

        throw error;
      }
    },
    [refreshSession, tokens],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      isHydrated,
      isAuthenticated: Boolean(tokens?.access),
      accessToken: tokens?.access ?? null,
      refreshToken: tokens?.refresh ?? null,
      role: tokens?.role ?? null,
      login,
      register,
      refreshSession,
      logout,
      authedRequest,
    }),
    [authedRequest, isHydrated, login, logout, refreshSession, register, tokens],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}
