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

import { NavigationContainer } from "@react-navigation/native";
import {
  createNativeStackNavigator,
  NativeStackNavigationProp,
} from "@react-navigation/native-stack";

type RootStackParamList = {
  onboarding: undefined;
  "login-screen": undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

type OnboardingScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  "onboarding"
>;

type Slide = {
  key: string;
  title: string;
  description: string;
  accent: string;
  icon: string;
  subtitle: string;
  palette: {
    halo: string;
    card: string;
    soft: string;
  };
};

const slides: Slide[] = [
  {
    key: "book",
    title: "Book boat rides easily",
    description:
      "Reserve your seat in a few taps and keep your trip planning fast, clear, and stress-free.",
    accent: "#0A4D8C",
    icon: "⛴",
    subtitle: "Fast reservations",
    palette: {
      halo: "rgba(10, 77, 140, 0.18)",
      card: "#F7FAFF",
      soft: "#D8E3FA",
    },
  },
  {
    key: "pay",
    title: "Pay securely in-app",
    description:
      "Complete checkout inside TideFlow with a smooth, protected payment flow.",
    accent: "#006874",
    icon: "◉",
    subtitle: "Protected checkout",
    palette: {
      halo: "rgba(0, 104, 116, 0.18)",
      card: "#F5FCFD",
      soft: "#BFEFF6",
    },
  },
  {
    key: "ticket",
    title: "Offline tickets – scan & board",
    description:
      "Keep your ticket ready even without signal so boarding stays quick at the dock.",
    accent: "#7B3A00",
    icon: "▣",
    subtitle: "Offline ready",
    palette: {
      halo: "rgba(123, 58, 0, 0.18)",
      card: "#FFF8F2",
      soft: "#FFD5B9",
    },
  },
];

function OnboardingScreen({
  navigation,
}: {
  navigation: OnboardingScreenNavigationProp;
}) {
  const { width } = useWindowDimensions();

  const listRef = useRef<FlatList>(null);

  const [currentIndex, setCurrentIndex] = useState(0);

  const goToLogin = () => {
    navigation.navigate("login-screen");
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

  const renderSlide = ({ item }: { item: Slide }) => {
    return (
      <View style={[styles.slide, { width }]}>
        <View style={styles.slideShell}>
          <View style={[styles.heroWrap, { borderColor: item.accent }]}>
            <View
              style={[styles.heroGlow, { backgroundColor: item.palette.halo }]}
            />
            <View
              style={[styles.heroCard, { backgroundColor: item.palette.card }]}
            >
              <View style={[styles.badge, { backgroundColor: item.accent }]}>
                <Text style={styles.badgeText}>
                  {item.subtitle.toUpperCase()}
                </Text>
              </View>

              {item.key === "book" ? (
                <View style={styles.heroContent}>
                  <View
                    style={[
                      styles.deck,
                      { backgroundColor: item.palette.soft },
                    ]}
                  >
                    <View
                      style={[
                        styles.deckLine,
                        { backgroundColor: item.accent },
                      ]}
                    />
                    <View
                      style={[
                        styles.deckLine,
                        styles.deckLineShort,
                        { backgroundColor: item.accent },
                      ]}
                    />
                    <View
                      style={[styles.deckCabin, { borderColor: item.accent }]}
                    >
                      <Text style={[styles.symbol, { color: item.accent }]}>
                        {item.icon}
                      </Text>
                    </View>
                  </View>
                  <View style={styles.tickerRow}>
                    <View
                      style={[
                        styles.ticketPill,
                        { backgroundColor: item.accent },
                      ]}
                    />
                    <View
                      style={[
                        styles.ticketPillMuted,
                        { backgroundColor: item.palette.soft },
                      ]}
                    />
                  </View>
                </View>
              ) : null}

              {item.key === "pay" ? (
                <View style={styles.heroContent}>
                  <View
                    style={[
                      styles.walletBody,
                      {
                        borderColor: item.accent,
                        backgroundColor: item.palette.soft,
                      },
                    ]}
                  >
                    <View
                      style={[
                        styles.walletChip,
                        { backgroundColor: item.accent },
                      ]}
                    />
                    <View style={styles.walletLines}>
                      <View
                        style={[
                          styles.walletLine,
                          { backgroundColor: item.accent },
                        ]}
                      />
                      <View
                        style={[
                          styles.walletLine,
                          styles.walletLineShort,
                          { backgroundColor: item.accent },
                        ]}
                      />
                    </View>
                  </View>
                  <View
                    style={[styles.lockPill, { backgroundColor: item.accent }]}
                  >
                    <Text style={styles.lockText}>SECURE PAY</Text>
                  </View>
                </View>
              ) : null}

              {item.key === "ticket" ? (
                <View style={styles.heroContent}>
                  <View style={[styles.qrFrame, { borderColor: item.accent }]}>
                    <Text style={[styles.qrGlyph, { color: item.accent }]}>
                      {item.icon}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.offlinePill,
                      { backgroundColor: item.palette.soft },
                    ]}
                  >
                    <Text style={styles.offlineText}>OFFLINE READY</Text>
                  </View>
                </View>
              ) : null}
            </View>
          </View>

          <View style={styles.textBlock}>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.description}>{item.description}</Text>
          </View>
        </View>
      </View>
    );
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
        renderItem={renderSlide}
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
          <Text style={styles.primaryButtonText}>Next</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

function LoginScreen() {
  return (
    <SafeAreaView style={styles.loginScreen}>
      <View style={styles.loginBackgroundOrb} />
      <View style={styles.loginCard}>
        <Text style={styles.loginLabel}>login-screen</Text>
        <Text style={styles.loginTitle}>Welcome back</Text>
        <Text style={styles.loginCopy}>
          Wire your login form here. The onboarding flow already routes to this
          screen.
        </Text>
      </View>
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{ headerShown: false }}
        initialRouteName="onboarding"
      >
        <Stack.Screen name="onboarding" component={OnboardingScreen} />
        <Stack.Screen name="login-screen" component={LoginScreen} />
      </Stack.Navigator>
    </NavigationContainer>
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
  slide: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 24,
    paddingBottom: 36,
  },
  slideShell: {
    width: "100%",
    alignItems: "center",
    justifyContent: "center",
  },
  heroWrap: {
    width: "100%",
    maxWidth: 344,
    aspectRatio: 1,
    borderRadius: 32,
    borderWidth: 1,
    backgroundColor: "rgba(255,255,255,0.74)",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOpacity: 0.12,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 12 },
    elevation: 8,
    marginBottom: 28,
    overflow: "hidden",
  },
  heroGlow: {
    position: "absolute",
    width: 220,
    height: 220,
    borderRadius: 220,
    opacity: 0.32,
    transform: [{ scale: 1.08 }],
  },
  heroCard: {
    width: "78%",
    height: "78%",
    borderRadius: 28,
    borderWidth: 1,
    borderColor: "#E2E8F4",
    padding: 18,
    justifyContent: "space-between",
  },
  badge: {
    alignSelf: "flex-start",
    minWidth: 72,
    height: 32,
    paddingHorizontal: 12,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  badgeText: {
    color: "#FFFFFF",
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1.1,
  },
  heroContent: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 10,
  },
  deck: {
    width: 180,
    height: 180,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  deckLine: {
    position: "absolute",
    width: 120,
    height: 12,
    borderRadius: 999,
    top: 48,
    opacity: 0.85,
  },
  deckLineShort: {
    top: 74,
    width: 82,
  },
  deckCabin: {
    width: 116,
    height: 116,
    borderRadius: 999,
    borderWidth: 2,
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
  },
  tickerRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 18,
  },
  ticketPill: {
    width: 92,
    height: 12,
    borderRadius: 999,
    marginRight: 10,
  },
  ticketPillMuted: {
    width: 74,
    height: 12,
    borderRadius: 999,
  },
  walletBody: {
    width: 190,
    height: 136,
    borderRadius: 22,
    borderWidth: 1,
    padding: 18,
    justifyContent: "space-between",
  },
  walletChip: {
    width: 32,
    height: 24,
    borderRadius: 8,
  },
  walletLines: {
    marginTop: 10,
  },
  walletLine: {
    height: 12,
    borderRadius: 999,
    marginBottom: 10,
    opacity: 0.9,
  },
  walletLineShort: {
    width: "62%",
  },
  lockPill: {
    marginTop: 16,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 999,
  },
  lockText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.2,
  },
  qrFrame: {
    width: 164,
    height: 164,
    borderRadius: 24,
    borderWidth: 2,
    borderStyle: "dashed",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF",
  },
  qrGlyph: {
    fontSize: 88,
    fontWeight: "700",
  },
  offlinePill: {
    marginTop: 16,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 999,
  },
  offlineText: {
    color: "#311300",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.2,
  },
  symbol: {
    fontSize: 54,
    fontWeight: "700",
    lineHeight: 58,
  },
  textBlock: {
    maxWidth: 320,
    alignItems: "center",
  },
  title: {
    fontSize: 30,
    lineHeight: 36,
    fontWeight: "700",
    letterSpacing: -0.7,
    color: "#0F1C2D",
    textAlign: "center",
    marginBottom: 12,
  },
  description: {
    fontSize: 17,
    lineHeight: 27,
    color: "#424750",
    textAlign: "center",
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
  loginScreen: {
    flex: 1,
    backgroundColor: "#F9F9FF",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  loginBackgroundOrb: {
    position: "absolute",
    top: -80,
    right: -90,
    width: 240,
    height: 240,
    borderRadius: 240,
    backgroundColor: "rgba(10, 77, 140, 0.12)",
  },
  loginCard: {
    width: "100%",
    borderRadius: 28,
    padding: 24,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#D8E3FA",
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 10 },
    elevation: 5,
  },
  loginLabel: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: "#006874",
    marginBottom: 12,
  },
  loginTitle: {
    fontSize: 32,
    lineHeight: 38,
    fontWeight: "700",
    letterSpacing: -0.7,
    color: "#111C2C",
    marginBottom: 12,
  },
  loginCopy: {
    fontSize: 16,
    lineHeight: 24,
    color: "#424750",
  },
});
