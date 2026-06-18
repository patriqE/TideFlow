import React, { useRef, useState } from "react";
import {
  FlatList,
  Pressable,
  SafeAreaView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from "react-native";
import { router } from "expo-router";

import { slides } from "@/data/onboardingSlides";
import { OnboardingSlide } from "@/components/OnboardingSlide";

export default function OnboardingScreen() {
  const { width } = useWindowDimensions();
  const listRef = useRef<FlatList>(null);
  const [currentIndex, setCurrentIndex] = useState(0);

  const goToLogin = () => {
    router.push("/login");
  };

  const handleNext = () => {
    if (currentIndex < slides.length - 1) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      listRef.current?.scrollToIndex({
        index: nextIndex,
        animated: true,
      });
      return;
    }
    goToLogin();
  };

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar barStyle="dark-content" backgroundColor="#F9F9FF" />

      <View style={styles.header}>
        <Text style={styles.brand}>TideFlow</Text>
        <Pressable onPress={goToLogin} hitSlop={12}>
          <Text style={styles.skip}>Skip</Text>
        </Pressable>
      </View>

      <View style={styles.backgroundOrbTop} />
      <View style={styles.backgroundOrbLeft} />
      <View style={styles.backgroundBand} />

      <FlatList
        ref={listRef}
        data={slides}
        renderItem={({ item }) => <OnboardingSlide item={item} />}
        keyExtractor={(item) => item.key}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(event) => {
          const nextIndex = Math.round(
            event.nativeEvent.contentOffset.x / width,
          );
          setCurrentIndex(nextIndex);
        }}
        bounces={false}
        style={styles.carousel}
      />

      <View style={styles.footer}>
        <View style={styles.dots}>
          {slides.map((slide, index) => {
            const active = index === currentIndex;
            return (
              <View
                key={slide.key}
                style={[styles.dot, active && styles.dotActive]}
              />
            );
          })}
        </View>

        <Pressable style={styles.primaryButton} onPress={handleNext}>
          <Text style={styles.primaryButtonText}>
            {currentIndex === slides.length - 1 ? "Get Started" : "Next"}
          </Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#F9F9FF",
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 10,
    height: 64,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    zIndex: 3,
  },
  brand: {
    fontSize: 20,
    fontWeight: "700",
    color: "#003667",
    letterSpacing: -0.4,
  },
  skip: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.1,
    textTransform: "uppercase",
    color: "#424750",
  },
  backgroundOrbTop: {
    position: "absolute",
    top: -90,
    right: -80,
    width: 240,
    height: 240,
    borderRadius: 240,
    backgroundColor: "rgba(10, 77, 140, 0.12)",
  },
  backgroundOrbLeft: {
    position: "absolute",
    left: -100,
    bottom: 140,
    width: 220,
    height: 220,
    borderRadius: 220,
    backgroundColor: "rgba(123, 58, 0, 0.08)",
  },
  backgroundBand: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    height: "42%",
    backgroundColor: "rgba(224, 235, 255, 0.68)",
  },
  carousel: {
    flex: 1,
  },
  footer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
    paddingTop: 8,
  },
  dots: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 16,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 99,
    backgroundColor: "#C2C6D2",
    marginHorizontal: 4,
  },
  dotActive: {
    width: 24,
    backgroundColor: "#003667",
  },
  primaryButton: {
    minHeight: 56,
    borderRadius: 18,
    backgroundColor: "#003667",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#003667",
    shadowOpacity: 0.22,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 8 },
    elevation: 6,
  },
  primaryButtonText: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
  },
});
