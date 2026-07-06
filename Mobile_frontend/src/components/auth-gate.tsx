import { useEffect } from "react";

import { router, useSegments } from "expo-router";

import { useAuth } from "@/context/auth-context";

export function AuthGate() {
  const segments = useSegments();
  const { isHydrated, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    const rootSegment = segments[0];
    const isAuthScreen = rootSegment === "login" || rootSegment === "signup";
    const isProtectedArea = rootSegment === "(tabs)";
    const isLandingScreen = rootSegment === "index";

    if (!isAuthenticated && isProtectedArea) {
      router.replace("/login");
      return;
    }

    if (isAuthenticated && (isAuthScreen || isLandingScreen)) {
      router.replace("/(tabs)/home");
    }
  }, [isAuthenticated, isHydrated, segments]);

  return null;
}
