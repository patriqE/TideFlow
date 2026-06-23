import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  StatusBar,
  ActivityIndicator,
} from "react-native";
import { MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";

import { COLORS, TYPOGRAPHY } from "@/utils/colors";
import { useNetworkStatus } from "@/hooks/use-Network-Status";
import { StatusBar as CustomStatusBar } from "@/components/StatusBar";
import { LoadingOverlay } from "@/components/LoadingOverlay";

interface LoginFormData {
  identity: string;
  password: string;
}

export default function LoginScreen() {
  const [formData, setFormData] = useState<LoginFormData>({
    identity: "",
    password: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [focusedField, setFocusedField] = useState<
    "identity" | "password" | null
  >(null);

  const { isOnline } = useNetworkStatus();

  const handleLogin = async () => {
    if (!formData.identity || !formData.password) {
      Alert.alert("Validation Error", "Please fill in all fields");
      return;
    }

    setIsLoading(true);

    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      Alert.alert(
        "Authentication Successful",
        "Redirecting to bridge dashboard...",
        [
          {
            text: "OK",
            onPress: () => router.replace("/(tabs)/home" as any),
          },
        ],
      );
    }, 2500);
  };

  return (
    <SafeAreaView className="flex-1 bg-surface">
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.surface} />

      <CustomStatusBar isOnline={isOnline} />

      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        className="flex-1"
      >
        <View className="flex-1 items-center justify-center px-6 py-8 bg-surface">
          <View className="w-full max-w-[440px]">
            {/* Back to Onboarding */}
            <TouchableOpacity
              onPress={() => router.back()}
              className="mb-6 flex-row items-center"
            >
              <MaterialIcons
                name="arrow-back"
                size={24}
                color={COLORS.primary}
              />
              <Text className="text-primary ml-2 font-body-md">Back</Text>
            </TouchableOpacity>

            {/* Logo */}
            <View className="flex-col items-center mb-8">
              <MaterialIcons
                name="sailing"
                size={48}
                color={COLORS.primary}
                style={{ marginBottom: 12 }}
              />
              <Text style={TYPOGRAPHY.headlineLG} className="text-primary">
                TideFlow
              </Text>
            </View>

            {/* Welcome Text */}
            <View className="mb-6">
              <Text
                style={TYPOGRAPHY.headlineLG}
                className="text-on-surface mb-2"
              >
                Welcome back, Captain
              </Text>
              <Text
                style={TYPOGRAPHY.bodyMD}
                className="text-on-surface-variant"
              >
                Please authenticate to access the fleet dashboard.
              </Text>
            </View>

            {/* Requirement Banner */}
            <View className="mb-4 p-3 bg-surface-container-low border border-outline-variant rounded-lg flex-row items-start gap-2">
              <MaterialIcons
                name="info"
                size={20}
                color={COLORS.primary}
                style={{ marginTop: 2 }}
              />
              <Text
                style={TYPOGRAPHY.bodySM}
                className="text-on-surface-variant flex-1"
              >
                Internet connection required for vessel manifest
                synchronization.
              </Text>
            </View>

            {/* Login Form */}
            <View className="space-y-4">
              {/* Email/Phone Field */}
              <View className="space-y-1">
                <Text
                  style={TYPOGRAPHY.labelCaps}
                  className="text-on-surface-variant px-1"
                >
                  Email/Phone
                </Text>
                <View
                  className={`relative flex-row items-center bg-white border rounded-xl h-14 px-4 ${
                    focusedField === "identity"
                      ? "border-primary ring-2 ring-primary/20"
                      : "border-outline-variant"
                  }`}
                >
                  <MaterialIcons
                    name="person"
                    size={24}
                    color={
                      focusedField === "identity"
                        ? COLORS.primary
                        : COLORS.outline
                    }
                  />
                  <TextInput
                    className="flex-1 ml-3 text-on-surface"
                    style={TYPOGRAPHY.bodyMD}
                    placeholder="captain@tideflow.io"
                    placeholderTextColor={COLORS.outline}
                    value={formData.identity}
                    onChangeText={(text) =>
                      setFormData({ ...formData, identity: text })
                    }
                    onFocus={() => setFocusedField("identity")}
                    onBlur={() => setFocusedField(null)}
                    autoCapitalize="none"
                    keyboardType="email-address"
                    returnKeyType="next"
                  />
                </View>
              </View>

              {/* Password Field */}
              <View className="space-y-1">
                <View className="flex-row justify-between items-center px-1">
                  <Text
                    style={TYPOGRAPHY.labelCaps}
                    className="text-on-surface-variant"
                  >
                    Password
                  </Text>
                  <TouchableOpacity>
                    <Text style={TYPOGRAPHY.labelCaps} className="text-primary">
                      Forgot password?
                    </Text>
                  </TouchableOpacity>
                </View>
                <View
                  className={`relative flex-row items-center bg-white border rounded-xl h-14 px-4 ${
                    focusedField === "password"
                      ? "border-primary ring-2 ring-primary/20"
                      : "border-outline-variant"
                  }`}
                >
                  <MaterialIcons
                    name="lock"
                    size={24}
                    color={
                      focusedField === "password"
                        ? COLORS.primary
                        : COLORS.outline
                    }
                  />
                  <TextInput
                    className="flex-1 ml-3 text-on-surface"
                    style={TYPOGRAPHY.bodyMD}
                    placeholder="••••••••"
                    placeholderTextColor={COLORS.outline}
                    secureTextEntry={!showPassword}
                    value={formData.password}
                    onChangeText={(text) =>
                      setFormData({ ...formData, password: text })
                    }
                    onFocus={() => setFocusedField("password")}
                    onBlur={() => setFocusedField(null)}
                    returnKeyType="done"
                    onSubmitEditing={handleLogin}
                  />
                  <TouchableOpacity
                    onPress={() => setShowPassword(!showPassword)}
                  >
                    <MaterialIcons
                      name={showPassword ? "visibility" : "visibility-off"}
                      size={24}
                      color={COLORS.outline}
                    />
                  </TouchableOpacity>
                </View>
              </View>

              {/* Login Button */}
              <TouchableOpacity
                className="w-full h-14 bg-primary rounded-xl shadow-md active:scale-[0.98] flex-row items-center justify-center gap-2"
                onPress={handleLogin}
                disabled={isLoading}
                style={{
                  shadowColor: COLORS.primary,
                  shadowOffset: { width: 0, height: 2 },
                  shadowOpacity: 0.2,
                  shadowRadius: 4,
                  elevation: 4,
                }}
              >
                {isLoading ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <>
                    <Text style={TYPOGRAPHY.actionLG} className="text-white">
                      Login
                    </Text>
                    <MaterialIcons
                      name="arrow-forward"
                      size={24}
                      color="white"
                    />
                  </>
                )}
              </TouchableOpacity>
            </View>

            {/* Create Account Link */}
            <View className="mt-6 pt-4 border-t border-outline-variant items-center">
              <Text
                style={TYPOGRAPHY.bodySM}
                className="text-on-surface-variant"
              >
                New vessel operator?{" "}
                <Text
                  className="text-primary font-bold"
                  onPress={() => router.push("/signup" as any)}
                >
                  Create account
                </Text>
              </Text>
            </View>

            {/* Footer Legal */}
            <View className="mt-6 flex-row justify-center gap-4">
              <TouchableOpacity>
                <Text className="text-outline font-label-caps text-[10px] uppercase tracking-widest">
                  Privacy Policy
                </Text>
              </TouchableOpacity>
              <Text className="text-outline-variant">•</Text>
              <TouchableOpacity>
                <Text className="text-outline font-label-caps text-[10px] uppercase tracking-widest">
                  Terms of Service
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </KeyboardAvoidingView>

      <LoadingOverlay visible={isLoading} />
    </SafeAreaView>
  );
}
