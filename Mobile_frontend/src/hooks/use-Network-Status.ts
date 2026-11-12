import { useState, useEffect } from "react";
import NetInfo from "@react-native-community/netinfo";

export const useNetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    // If you have @react-native-community/netinfo installed
    // const unsubscribe = NetInfo.addEventListener((state) => {
    //   setIsOnline(state.isConnected ?? true);
    // });
    // return () => unsubscribe();

    // Simulated for now (matches your HTML version)
    const interval = setInterval(() => {
      // In production: check actual network status
      // setIsOnline(navigator.onLine);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return { isOnline };
};
