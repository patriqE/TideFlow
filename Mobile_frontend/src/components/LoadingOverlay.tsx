import React from "react";
import { View, Text, ActivityIndicator } from "react-native";
import { MaterialIcons } from "@expo/vector-icons";
import Animated, { FadeIn, FadeOut } from "react-native-reanimated";
import { COLORS, TYPOGRAPHY } from "@/utils/colors";

interface LoadingOverlayProps {
  visible: boolean;
  message?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  visible,
  message = "Synchronizing Manifest...",
}) => {
  if (!visible) return null;

  return (
    <Animated.View
      entering={FadeIn}
      exiting={FadeOut}
      className="absolute inset-0 bg-primary/95 items-center justify-center z-50"
    >
      <View className="items-center">
        <View className="relative w-24 h-24 mb-4">
          <View className="absolute inset-0 border-4 border-white/20 rounded-full" />
          <View className="absolute inset-0 border-4 border-t-secondary-container rounded-full animate-spin" />
          <View className="absolute inset-0 items-center justify-center">
            <MaterialIcons
              name="anchor"
              size={32}
              color={COLORS.white}
              style={{ opacity: 0.8 }}
            />
          </View>
        </View>
        <Text
          style={TYPOGRAPHY.labelCaps}
          className="text-white tracking-[0.2em]"
        >
          {message}
        </Text>
      </View>
    </Animated.View>
  );
};
