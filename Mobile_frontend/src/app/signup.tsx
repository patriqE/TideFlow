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
  ScrollView,
} from "react-native";
import { MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";

import { COLORS, TYPOGRAPHY } from "@/utils/colors";
import { useNetworkStatus } from "@/hooks/use-Network-Status";
import { StatusBar as CustomStatusBar } from "@/components/StatusBar";
import LoadingOverlay from "@/components/LoadingOverlay";

interface SignupFormData {
  fullName: string;
  email: string;
  phone: string;
  password: string;
  confirmPassword: string;
  agreeToTerms: boolean;
}

export default function SignupScreen() {
  const [formData, setFormData] = useState<SignupFormData>({
    fullName: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
    agreeToTerms: false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const { isOnline } = useNetworkStatus();

  const handleSignup = async () => {
    // Validation
    if (
      !formData.fullName ||
      !formData.email ||
      !formData.phone ||
      !formData.password ||
      !formData.confirmPassword
    ) {
      Alert.alert("Validation Error", "Please fill in all fields");
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      Alert.alert("Validation Error", "Passwords do not match");
      return;
    }

    if (formData.password.length < 8) {
      Alert.alert("Validation Error", "Password must be at least 8 characters");
      return;
    }

    if (!formData.agreeToTerms) {
      Alert.alert(
        "Validation Error",
        "Please agree to the Terms of Service and Privacy Policy",
      );
      return;
    }

    setIsLoading(true);

    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      Alert.alert(
        "Account Created!",
        "Your TideFlow account has been created successfully. Please login to continue.",
        [
          {
            text: "Go to Login",
            onPress: () => router.replace("/login"),
          },
        ],
      );
    }, 2500);
  };

  const getFieldStyle = (fieldName: string) => {
    return focusedField === fieldName
      ? "border-primary ring-2 ring-primary/20"
      : "border-outline-variant";
  };

  const getIconColor = (fieldName: string) => {
    return focusedField === fieldName ? COLORS.primary : COLORS.outline;
  };

  return (
    <SafeAreaView className="flex-1 bg-surface">
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.surface} />

      <CustomStatusBar isOnline={isOnline} />

      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        className="flex-1"
      >
        <ScrollView
          className="flex-1 bg-surface"
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ flexGrow: 1 }}
        >
          <View className="flex-1 items-center justify-center px-6 py-8">
            <View className="w-full max-w-[440px]">
              {/* Back to Login */}
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
              <View className="flex-col items-center mb-6">
                <MaterialIcons
                  name="sailing"
                  size={48}
                  color={COLORS.primary}
                  style={{ marginBottom: 12 }}
                />
                <Text style={TYPOGRAPHY.headlineLG} className="text-primary">
                  TideFlow
                </Text>
                <Text
                  style={TYPOGRAPHY.bodySM}
                  className="text-on-surface-variant mt-1"
                >
                  Create your account
                </Text>
              </View>

              {/* Welcome Text */}
              <View className="mb-6">
                <Text
                  style={TYPOGRAPHY.headlineLG}
                  className="text-on-surface mb-2"
                >
                  Join the Fleet
                </Text>
                <Text
                  style={TYPOGRAPHY.bodyMD}
                  className="text-on-surface-variant"
                >
                  Start your maritime journey with TideFlow today.
                </Text>
              </View>

              {/* Signup Form */}
              <View className="space-y-4">
                {/* Full Name Field */}
                <View className="space-y-1">
                  <Text
                    style={TYPOGRAPHY.labelCaps}
                    className="text-on-surface-variant px-1"
                  >
                    Full Name
                  </Text>
                  <View
                    className={`relative flex-row items-center bg-white border rounded-xl h-14 px-4 ${getFieldStyle(
                      "fullName",
                    )}`}
                  >
                    <MaterialIcons
                      name="person"
                      size={24}
                      color={getIconColor("fullName")}
                    />
                    <TextInput
                      className="flex-1 ml-3 text-on-surface"
                      style={TYPOGRAPHY.bodyMD}
                      placeholder="Captain James T. Cook"
                      placeholderTextColor={COLORS.outline}
                      value={formData.fullName}
                      onChangeText={(text) =>
                        setFormData({ ...formData, fullName: text })
                      }
                      onFocus={() => setFocusedField("fullName")}
                      onBlur={() => setFocusedField(null)}
                      returnKeyType="next"
                    />
                  </View>
                </View>

                {/* Email Field */}
                <View className="space-y-1">
                  <Text
                    style={TYPOGRAPHY.labelCaps}
                    className="text-on-surface-variant px-1"
                  >
                    Email Address
                  </Text>
                  <View
                    className={`relative flex-row items-center bg-white border rounded-xl h-14 px-4 ${getFieldStyle(
                      "email",
                    )}`}
                  >
                    <MaterialIcons
                      name="email"
                      size={24}
                      color={getIconColor("email")}
                    />
                    <TextInput
                      className="flex-1 ml-3 text-on-surface"
                      style={TYPOGRAPHY.bodyMD}
                      placeholder="james.cook@vessel.com"
                      placeholderTextColor={COLORS.outline}
                      value={formData.email}
                      onChangeText={(text) =>
                        setFormData({ ...formData, email: text })
                      }
                      onFocus={() => setFocusedField("email")}
                      onBlur={() => setFocusedField(null)}
                      autoCapitalize="none"
                      keyboardType="email-address"
                      returnKeyType="next"
                    />
                  </View>
                </View>

                {/* Phone Field */}
                <View className="space-y-1">
                  <Text
                    style={TYPOGRAPHY.labelCaps}
                    className="text-on-surface-variant px-1"
                  >
                    Phone Number
                  </Text>
                  <View
                    className={`relative flex-row items-center bg-white border rounded-xl h-14 px-4 ${getFieldStyle(
                      "phone",
                    )}`}
                  >
                    <MaterialIcons
                      name="call"
                      size={24}
                      color={getIconColor("phone")}
                    />
                    <TextInput
                      className="flex-1 ml-3 text-on-surface"
                      style={TYPOGRAPHY.bodyMD}
                      placeholder="+1 (555) 000-0000"
                      placeholderTextColor={COLORS.outline}
                      value={formData.phone}
                      onChangeText={(text) =>
                        setFormData({ ...formData, phone: text })
                      }
                      onFocus={() => setFocusedField("phone")}
                      onBlur={() => setFocusedField(null)}
                      keyboardType="phone-pad"
                      returnKeyType="next"
                    />
                  </View>
                </View>

                {/* Password Fields - Side by Side */}
                <View className="flex-row gap-3">
                  <View className="flex-1 space-y-1">
                    <Text
                      style={TYPOGRAPHY.labelCaps}
                      className="text-on-surface-variant px-1"
                    >
                      Password
                    </Text>
                    <View
                      className={`relative flex-row items-center bg-white border rounded-xl h-14 px-4 ${getFieldStyle(
                        "password",
                      )}`}
                    >
                      <MaterialIcons
                        name="lock"
                        size={24}
                        color={getIconColor("password")}
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
                        returnKeyType="next"
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

                  <View className="flex-1 space-y-1">
                    <Text
                      style={TYPOGRAPHY.labelCaps}
                      className="text-on-surface-variant px-1"
                    >
                      Confirm
                    </Text>
                    <View
                      className={`relative flex-row items-center bg-white border rounded-xl h-14 px-4 ${getFieldStyle(
                        "confirmPassword",
                      )}`}
                    >
                      <MaterialIcons
                        name="verified-user"
                        size={24}
                        color={getIconColor("confirmPassword")}
                      />
                      <TextInput
                        className="flex-1 ml-3 text-on-surface"
                        style={TYPOGRAPHY.bodyMD}
                        placeholder="••••••••"
                        placeholderTextColor={COLORS.outline}
                        secureTextEntry={!showConfirmPassword}
                        value={formData.confirmPassword}
                        onChangeText={(text) =>
                          setFormData({ ...formData, confirmPassword: text })
                        }
                        onFocus={() => setFocusedField("confirmPassword")}
                        onBlur={() => setFocusedField(null)}
                        returnKeyType="done"
                        onSubmitEditing={handleSignup}
                      />
                      <TouchableOpacity
                        onPress={() =>
                          setShowConfirmPassword(!showConfirmPassword)
                        }
                      >
                        <MaterialIcons
                          name={
                            showConfirmPassword
                              ? "visibility"
                              : "visibility-off"
                          }
                          size={24}
                          color={COLORS.outline}
                        />
                      </TouchableOpacity>
                    </View>
                  </View>
                </View>

                {/* Terms Checkbox */}
                <TouchableOpacity
                  onPress={() =>
                    setFormData({
                      ...formData,
                      agreeToTerms: !formData.agreeToTerms,
                    })
                  }
                  className="flex-row items-start gap-3 py-2"
                >
                  <View
                    className={`w-5 h-5 rounded border-2 mt-0.5 flex items-center justify-center ${
                      formData.agreeToTerms
                        ? "bg-primary border-primary"
                        : "border-outline-variant bg-white"
                    }`}
                  >
                    {formData.agreeToTerms && (
                      <MaterialIcons name="check" size={16} color="white" />
                    )}
                  </View>
                  <Text
                    style={TYPOGRAPHY.bodySM}
                    className="text-on-surface-variant flex-1"
                  >
                    I agree to the{" "}
                    <Text className="text-primary font-bold">
                      Terms of Service
                    </Text>{" "}
                    and{" "}
                    <Text className="text-primary font-bold">
                      Privacy Policy
                    </Text>{" "}
                    regarding maritime data handling.
                  </Text>
                </TouchableOpacity>

                {/* Sign Up Button */}
                <TouchableOpacity
                  className="w-full h-14 bg-primary rounded-xl shadow-md active:scale-[0.98] flex-row items-center justify-center gap-2 mt-2"
                  onPress={handleSignup}
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
                        Sign Up
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

              {/* Login Link */}
              <View className="mt-6 pt-4 border-t border-outline-variant items-center">
                <Text
                  style={TYPOGRAPHY.bodySM}
                  className="text-on-surface-variant"
                >
                  Already part of the crew?{" "}
                  <Text
                    className="text-primary font-bold"
                    onPress={() => router.push("/login" as any)}
                  >
                    Login
                  </Text>
                </Text>
              </View>

              {/* Offline Compliance Badge */}
              <View className="mt-6 pt-4 border-t border-outline-variant flex-row justify-between opacity-60">
                <View className="flex-row items-center gap-1">
                  <MaterialIcons
                    name="cloud-off"
                    size={16}
                    color={COLORS.onSurfaceVariant}
                  />
                  <Text className="text-[10px] font-label-caps text-on-surface-variant uppercase">
                    Offline Secure
                  </Text>
                </View>
                <View className="flex-row items-center gap-1">
                  <MaterialIcons
                    name="security"
                    size={16}
                    color={COLORS.onSurfaceVariant}
                  />
                  <Text className="text-[10px] font-label-caps text-on-surface-variant uppercase">
                    Encrypted
                  </Text>
                </View>
              </View>

              {/* Footer */}
              <Text className="text-outline font-body-sm text-center mt-4">
                © 2024 TideFlow Maritime Systems. Ver. 2.4.0-Stable
              </Text>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      <LoadingOverlay visible={isLoading} message="Creating your account..." />
    </SafeAreaView>
  );
}
