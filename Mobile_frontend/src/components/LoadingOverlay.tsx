import React, { useEffect, useRef } from "react";
import {
  Modal,
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  Platform,
} from "react-native";

const { width } = Dimensions.get("window");
type Props = {
  visible: boolean;
  message?: string;
};

export default function LoadingOverlay({ visible, message }: Props) {
  const pulse = useRef(new Animated.Value(1)).current;
  const slide = useRef(new Animated.Value(-0.5)).current; // relative position

  useEffect(() => {
    const pulseAnim = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 1.03,
          duration: 1200,
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 1,
          duration: 1200,
          useNativeDriver: true,
        }),
      ]),
    );

    const slideAnim = Animated.loop(
      Animated.timing(slide, {
        toValue: 1.5,
        duration: 1600,
        useNativeDriver: true,
      }),
    );

    pulseAnim.start();
    slideAnim.start();

    return () => {
      pulseAnim.stop();
      slideAnim.stop();
    };
  }, [pulse, slide]);

  const translateX = slide.interpolate({
    inputRange: [-0.5, 1.5],
    outputRange: [-width * 0.7, width * 0.7],
  });

  return (
    <Modal visible={visible} transparent animationType="fade">
      <View style={styles.backdrop} pointerEvents={visible ? "auto" : "none"}>
        <View style={styles.container}>
          <Animated.Image
            source={require("../../assets/images/screen.png")}
            style={[styles.logo, { transform: [{ scale: pulse }] }]}
            resizeMode="contain"
          />

          <View style={styles.titleWrap}>
            <Text style={styles.title}>TideFlow</Text>
            <Text style={styles.subtitle}>Maritime Systems</Text>
          </View>

          <View style={styles.progressWrap}>
            <View style={styles.waveContainer}>
              <Animated.View
                style={[styles.waveProgress, { transform: [{ translateX }] }]}
              />
            </View>
            <Text style={styles.progressLabel}>
              {message ?? "Initializing Offline Cache"}
            </Text>
          </View>

          <View style={styles.footer}>
            <View style={styles.offlineBadge}>
              <Text style={styles.offlineText}>Ready for Offline Duty</Text>
            </View>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.25)",
    justifyContent: "center",
    alignItems: "center",
  },
  container: {
    width: "100%",
    paddingHorizontal: 24,
    alignItems: "center",
  },
  logo: {
    width: 140,
    height: 140,
    marginBottom: 18,
  },
  titleWrap: {
    alignItems: "center",
    marginBottom: 18,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#003667",
  },
  subtitle: {
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: "#6b7280",
    marginTop: 6,
  },
  progressWrap: {
    alignItems: "center",
    marginTop: 8,
  },
  waveContainer: {
    width: 140,
    height: 6,
    backgroundColor: "rgba(0,54,103,0.08)",
    borderRadius: 4,
    overflow: "hidden",
  },
  waveProgress: {
    position: "absolute",
    left: 0,
    top: 0,
    height: "100%",
    width: "40%",
    backgroundColor: "#003667",
  },
  progressLabel: {
    marginTop: 8,
    fontSize: 12,
    color: "#0f172a",
  },
  footer: {
    position: "absolute",
    bottom: Platform.OS === "android" ? 34 : 48,
    alignItems: "center",
  },
  offlineBadge: {
    backgroundColor: "#eef6ff",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "rgba(40,95,159,0.12)",
  },
  offlineText: {
    color: "#003667",
    fontWeight: "600",
    fontSize: 12,
  },
});
