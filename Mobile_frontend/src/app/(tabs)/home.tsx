import React from "react";
import { View, Text, SafeAreaView } from "react-native";
import { COLORS, TYPOGRAPHY } from "@/utils/colors";

export default function HomeScreen() {
  return (
    <SafeAreaView className="flex-1 bg-surface">
      <View className="flex-1 items-center justify-center p-6">
        <Text style={TYPOGRAPHY.headlineLG} className="text-on-surface">
          Welcome to TideFlow
        </Text>
        <Text
          style={TYPOGRAPHY.bodyMD}
          className="text-on-surface-variant mt-2"
        >
          Your maritime dashboard
        </Text>
      </View>
    </SafeAreaView>
  );
}
