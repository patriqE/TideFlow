import React from "react";
import {
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";

import { useAuth } from "@/context/auth-context";
import { useNetworkStatus } from "@/hooks/use-Network-Status";
import { COLORS, TYPOGRAPHY } from "@/utils/colors";
import { StatusBar as CustomStatusBar } from "@/components/StatusBar";

const DISPLAY_NAME = "Captain Aris";
const MEMBER_ID = "TF-99281";

function getOperatorRoleLabel(role: string | null) {
  if (role === "DECK_AGENT") {
    return "AGENT";
  }

  return "PASSENGER";
}

function ProfileActionItem({
  icon,
  title,
  subtitle,
  onPress,
}: {
  icon: keyof typeof MaterialIcons.glyphMap;
  title: string;
  subtitle: string;
  onPress: () => void;
}) {
  return (
    <Pressable style={styles.actionButton} onPress={onPress}>
      <View style={styles.actionLeft}>
        <View style={styles.actionIconWrap}>
          <MaterialIcons name={icon} size={22} color={COLORS.primary} />
        </View>
        <View>
          <Text style={styles.actionTitle}>{title}</Text>
          <Text style={styles.actionSubtitle}>{subtitle}</Text>
        </View>
      </View>
      <MaterialIcons name="chevron-right" size={22} color={COLORS.outline} />
    </Pressable>
  );
}

export default function ProfileScreen() {
  const { isOnline } = useNetworkStatus();
  const { role, logout, refreshSession } = useAuth();
  const roleLabel = getOperatorRoleLabel(role);

  const handleManualSync = async () => {
    const refreshed = await refreshSession();

    Alert.alert(
      refreshed ? "Synced" : "Sync unavailable",
      refreshed
        ? "Your session was refreshed successfully."
        : "The app could not refresh your session right now.",
    );
  };

  const handleLogout = async () => {
    await logout();
    router.replace("/login");
  };

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.surface} />

      <CustomStatusBar isOnline={isOnline} />

      <View style={styles.topBar}>
        <View style={styles.topBarLeft}>
          <MaterialIcons name="menu" size={24} color={COLORS.primary} />
          <Text style={TYPOGRAPHY.headlineMD}>TideFlow</Text>
        </View>

        <View style={styles.offlineBadge}>
          <MaterialIcons
            name={isOnline ? "cloud-done" : "signal-wifi-off"}
            size={16}
            color={isOnline ? COLORS.secondary : COLORS.outline}
          />
          <Text style={styles.offlineText}>
            {isOnline ? "ONLINE" : "OFFLINE MODE"}
          </Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.heroGrid}>
          <View style={styles.identityCard}>
            <View style={styles.avatarWrap}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>CA</Text>
              </View>
              <View style={styles.statusDot} />
            </View>

            <View style={styles.identityBody}>
              <Text style={styles.roleTag}>{roleLabel}</Text>
              <Text style={styles.name}>{DISPLAY_NAME}</Text>
              <View style={styles.memberIdRow}>
                <MaterialIcons
                  name="verified"
                  size={18}
                  color={COLORS.primary}
                />
                <Text style={styles.memberId}>ID: {MEMBER_ID}</Text>
              </View>

              <View style={styles.chipRow}>
                <View style={styles.chipPrimary}>
                  <Text style={styles.chipPrimaryText}>
                    {roleLabel === "AGENT" ? "OPERATIONS AGENT" : "PASSENGER"}
                  </Text>
                </View>
                <View style={styles.chipSecondary}>
                  <Text style={styles.chipSecondaryText}>FLEET ACCESS</Text>
                </View>
              </View>
            </View>
          </View>

          <View style={styles.statsCard}>
            <MaterialIcons
              name="directions-boat"
              size={48}
              color={COLORS.onPrimary}
            />
            <Text style={styles.statsValue}>4,280</Text>
            <Text style={styles.statsLabel}>Nautical Miles This Month</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Operator Settings</Text>

          <View style={styles.settingsCard}>
            <ProfileActionItem
              icon="person-outline"
              title="Edit Profile"
              subtitle="Update credentials and contact details"
              onPress={() =>
                Alert.alert(
                  "Coming soon",
                  "Profile editing will be wired to the backend profile API.",
                )
              }
            />
            <View style={styles.divider} />
            <ProfileActionItem
              icon="account-balance-wallet"
              title="Payment Methods"
              subtitle="Manage billing and checkout preferences"
              onPress={() =>
                Alert.alert(
                  "Coming soon",
                  "Payment methods are not connected yet.",
                )
              }
            />
            <View style={styles.divider} />
            <ProfileActionItem
              icon="notifications-active"
              title="Notification Preferences"
              subtitle="Tide alerts, schedule changes, and fleet updates"
              onPress={() =>
                Alert.alert(
                  "Coming soon",
                  "Notification preferences will be added next.",
                )
              }
            />
          </View>
        </View>

        <View style={styles.actionsSection}>
          <View>
            <View style={styles.syncTitleRow}>
              <View style={styles.syncDotWrap} />
              <Text style={styles.syncTitle}>SYNCED FOR OFFLINE USE</Text>
            </View>
            <Text style={styles.syncMeta}>Last synchronized: 12m ago</Text>
          </View>

          <View style={styles.buttonRow}>
            <Pressable
              style={styles.secondaryButton}
              onPress={handleManualSync}
            >
              <MaterialIcons name="sync" size={20} color={COLORS.primary} />
              <Text style={styles.secondaryButtonText}>Manual Sync</Text>
            </Pressable>

            <Pressable style={styles.primaryButton} onPress={handleLogout}>
              <MaterialIcons name="logout" size={20} color={COLORS.onPrimary} />
              <Text style={styles.primaryButtonText}>Logout</Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerBrand}>TideFlow</Text>
          <Text style={styles.footerVersion}>VERSION TF-1.0</Text>
          <Text style={styles.footerTagline}>
            Professional Maritime Operations Platform
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: COLORS.surface,
  },
  topBar: {
    height: 64,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: COLORS.outline,
    backgroundColor: COLORS.surface,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  topBarLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  offlineBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: COLORS.surfaceContainerHigh,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: COLORS.outline,
  },
  offlineText: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1,
    color: COLORS.onSurfaceVariant,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
    gap: 24,
  },
  heroGrid: {
    gap: 16,
  },
  identityCard: {
    backgroundColor: COLORS.surfaceContainerLowest,
    borderWidth: 1,
    borderColor: COLORS.outline,
    borderRadius: 20,
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
    shadowColor: "#000",
    shadowOpacity: 0.12,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  avatarWrap: {
    position: "relative",
  },
  avatar: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: COLORS.surfaceContainer,
    borderWidth: 4,
    borderColor: COLORS.surfaceContainerHigh,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarText: {
    fontSize: 30,
    fontWeight: "700",
    color: COLORS.primary,
    letterSpacing: -1,
  },
  statusDot: {
    position: "absolute",
    bottom: 4,
    right: 4,
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: "#22c55e",
    borderWidth: 2,
    borderColor: "#fff",
  },
  identityBody: {
    flex: 1,
  },
  roleTag: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 2,
    color: COLORS.primary,
  },
  name: {
    marginTop: 4,
    fontSize: 30,
    lineHeight: 36,
    fontWeight: "700",
    color: COLORS.onSurface,
  },
  memberId: {
    color: COLORS.onSurfaceVariant,
    fontSize: 14,
  },
  memberIdRow: {
    marginTop: 8,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 14,
  },
  chipPrimary: {
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  chipPrimaryText: {
    color: COLORS.onPrimary,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1,
  },
  chipSecondary: {
    backgroundColor: COLORS.secondaryContainer,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  chipSecondaryText: {
    color: COLORS.onSecondaryContainer,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1,
  },
  statsCard: {
    backgroundColor: COLORS.primary,
    borderRadius: 20,
    padding: 16,
    minHeight: 160,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: COLORS.primary,
    shadowOpacity: 0.2,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 8 },
    elevation: 4,
  },
  statsValue: {
    marginTop: 8,
    fontSize: 34,
    lineHeight: 40,
    fontWeight: "700",
    color: COLORS.onPrimary,
  },
  statsLabel: {
    marginTop: 6,
    fontSize: 12,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    fontWeight: "700",
    color: COLORS.onPrimary,
    opacity: 0.8,
    textAlign: "center",
  },
  section: {
    gap: 12,
  },
  sectionTitle: {
    paddingHorizontal: 4,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 2,
    textTransform: "uppercase",
    color: COLORS.onSurfaceVariant,
  },
  settingsCard: {
    backgroundColor: COLORS.surfaceContainerLowest,
    borderWidth: 1,
    borderColor: COLORS.outline,
    borderRadius: 20,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOpacity: 0.12,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  actionButton: {
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  actionLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
    flex: 1,
  },
  actionIconWrap: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.surfaceContainer,
    alignItems: "center",
    justifyContent: "center",
  },
  actionTitle: {
    fontSize: 18,
    lineHeight: 24,
    fontWeight: "600",
    color: COLORS.onSurface,
  },
  actionSubtitle: {
    marginTop: 2,
    fontSize: 14,
    lineHeight: 20,
    color: COLORS.onSurfaceVariant,
  },
  divider: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: COLORS.outline,
    marginHorizontal: 16,
  },
  actionsSection: {
    gap: 16,
    paddingTop: 8,
  },
  syncTitle: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 2,
    color: COLORS.onSurfaceVariant,
  },
  syncTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  syncDotWrap: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#f97316",
  },
  syncMeta: {
    marginTop: 4,
    fontSize: 14,
    color: COLORS.outline,
  },
  buttonRow: {
    flexDirection: "row",
    gap: 12,
  },
  secondaryButton: {
    flex: 1,
    minHeight: 56,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: COLORS.primary,
    backgroundColor: COLORS.surface,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: "700",
    color: COLORS.primary,
  },
  primaryButton: {
    flex: 1,
    minHeight: 56,
    borderRadius: 16,
    backgroundColor: COLORS.primary,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: "700",
    color: COLORS.onPrimary,
  },
  footer: {
    paddingTop: 16,
    paddingBottom: 24,
    alignItems: "center",
    gap: 4,
  },
  footerBrand: {
    fontSize: 20,
    fontWeight: "700",
    color: COLORS.onSurfaceVariant,
  },
  footerVersion: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 2,
    color: COLORS.outline,
  },
  footerTagline: {
    marginTop: 2,
    fontSize: 14,
    color: COLORS.outline,
    fontStyle: "italic",
    textAlign: "center",
  },
});
