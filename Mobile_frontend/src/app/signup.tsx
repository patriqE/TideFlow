import React from "react";
import { View, Text, SafeAreaView, TouchableOpacity } from "react-native";
import { router } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, TYPOGRAPHY } from "@/utils/colors";

export default function SignupScreen() {
  return (
    <SafeAreaView className="flex-1 bg-surface">
      <View className="flex-1 items-center justify-center px-6 py-8">
        <TouchableOpacity
          onPress={() => router.back()}
          className="mb-6 flex-row items-center self-start"
        >
          <MaterialIcons name="arrow-back" size={24} color={COLORS.primary} />
          <Text className="text-primary ml-2 font-body-md">Back</Text>
        </TouchableOpacity>

        <View className="w-full max-w-[440px] items-center">
          <MaterialIcons name="sailing" size={64} color={COLORS.primary} />
          <Text style={TYPOGRAPHY.headlineLG} className="text-primary mt-4">
            Create Account
          </Text>
          <Text
            style={TYPOGRAPHY.bodyMD}
            className="text-on-surface-variant mt-2 text-center"
          >
            Sign up to start booking boat rides
          </Text>
          <Text
            style={TYPOGRAPHY.bodySM}
            className="text-on-surface-variant mt-8"
          >
            Sign up form coming soon...
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}
