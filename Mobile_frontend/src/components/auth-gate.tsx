import { useEffect } from "react";

import { router, usePathname } from "expo-router";

import { useAuth } from "@/context/auth-context";

export function AuthGate() {
  const pathname = usePathname();
  const { isHydrated, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    const isAuthScreen = pathname === "/login" || pathname === "/signup";
    const isLandingScreen = pathname === "/";

    if (!isAuthenticated && !isAuthScreen) {
      router.replace("/login");
      return;
    }

    if (isAuthenticated && (isAuthScreen || isLandingScreen)) {
      router.replace("/");
    }
  }, [isAuthenticated, isHydrated, pathname]);

  return null;
}
