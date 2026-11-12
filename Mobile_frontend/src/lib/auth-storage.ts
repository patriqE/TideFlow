import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";

export type AuthTokens = {
  access: string;
  refresh: string;
  role: string | null;
};

const AUTH_STORAGE_KEY = "tideflow.auth.tokens";

async function getStoredValue() {
  if (Platform.OS === "web") {
    return AsyncStorage.getItem(AUTH_STORAGE_KEY);
  }

  return SecureStore.getItemAsync(AUTH_STORAGE_KEY);
}

async function setStoredValue(value: string) {
  if (Platform.OS === "web") {
    await AsyncStorage.setItem(AUTH_STORAGE_KEY, value);
    return;
  }

  await SecureStore.setItemAsync(AUTH_STORAGE_KEY, value);
}

async function removeStoredValue() {
  if (Platform.OS === "web") {
    await AsyncStorage.removeItem(AUTH_STORAGE_KEY);
    return;
  }

  await SecureStore.deleteItemAsync(AUTH_STORAGE_KEY);
}

export async function loadAuthTokens() {
  const storedValue = await getStoredValue();
  if (!storedValue) {
    return null;
  }

  try {
    return JSON.parse(storedValue) as AuthTokens;
  } catch {
    await removeStoredValue();
    return null;
  }
}

export async function saveAuthTokens(tokens: AuthTokens) {
  await setStoredValue(JSON.stringify(tokens));
}

export async function clearAuthTokens() {
  await removeStoredValue();
}
