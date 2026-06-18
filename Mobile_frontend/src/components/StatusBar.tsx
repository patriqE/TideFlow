import React from "react";
import { View, Text } from "react-native";
import { MaterialIcons } from "@expo/vector-icons";
import { COLORS, TYPOGRAPHY } from "@/utils/colors";

interface StatusBarProps {
  isOnline: boolean;
}

export const StatusBar: React.FC<StatusBarProps> = ({ isOnline }) => {
  return (
    <View className="flex-row items-center justify-between h-12 px-4 bg-surface">
      <View className="flex-row items-center gap-2">
        <View
          className={`w-2.5 h-2.5 rounded-full ${
            isOnline ? "bg-secondary" : "bg-error"
          }`}
        />
        <Text style={TYPOGRAPHY.labelCaps} className="text-on-surface-variant">
          {isOnline ? "System Online" : "Offline: Connection Required"}
        </Text>
      </View>
      <View className="flex-row items-center gap-2">
        <MaterialIcons name="wifi" size={18} color={COLORS.primary} />
        <Text style={TYPOGRAPHY.labelCaps} className="text-primary">
          SECURE CHANNEL
        </Text>
      </View>
    </View>
  );
};
