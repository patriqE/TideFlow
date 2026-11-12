import React from "react";
import { View, Text, useWindowDimensions, StyleSheet } from "react-native";
import { Slide } from "@/data/onboardingSlides";

interface OnboardingSlideProps {
  item: Slide;
}

export const OnboardingSlide: React.FC<OnboardingSlideProps> = ({ item }) => {
  const { width } = useWindowDimensions();

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

            {item.key === "book" && (
              <View style={styles.heroContent}>
                <View
                  style={[styles.deck, { backgroundColor: item.palette.soft }]}
                >
                  <View
                    style={[styles.deckLine, { backgroundColor: item.accent }]}
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
            )}

            {item.key === "pay" && (
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
            )}

            {item.key === "ticket" && (
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
            )}
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

const styles = StyleSheet.create({
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
});
