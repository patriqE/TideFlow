import React, { useState } from "react";
import {
  View,
  Text,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  Image,
  StatusBar,
} from "react-native";
import { MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";

import { COLORS, TYPOGRAPHY } from "@/utils/colors";
import { useNetworkStatus } from "@/hooks/use-Network-Status";
import { StatusBar as CustomStatusBar } from "@/components/StatusBar";

// Types for ride data
interface Ride {
  id: string;
  title: string;
  date: string;
  month: string;
  location: string;
  time: string;
  status: "CONFIRMED" | "REVIEW NEEDED";
  hasAlert?: boolean;
  alertText?: string;
}

export default function HomeScreen() {
  const { isOnline } = useNetworkStatus();
  const [activeTab, setActiveTab] = useState("home");

  // Sample ride data
  const upcomingRides: Ride[] = [
    {
      id: "1",
      title: "Harbor Express #902",
      date: "24",
      month: "OCT",
      location: "Pier 42",
      time: "14:00 - 15:30",
      status: "CONFIRMED",
    },
    {
      id: "2",
      title: "Twilight Ferry Cruise",
      date: "25",
      month: "OCT",
      location: "North Dock",
      time: "18:30 - 20:00",
      status: "REVIEW NEEDED",
      hasAlert: true,
      alertText: "Weather Alert",
    },
  ];

  const handleBookRide = () => {
    router.push("/rides" as any);
  };

  const handleViewAll = () => {
    router.push("/rides" as any);
  };

  const handleRidePress = (rideId: string) => {
    router.push(`/ride-details/${rideId}` as any);
  };

  const handleQRPress = (rideId: string) => {
    router.push(`/ticket/${rideId}` as any);
  };

  const handleTabPress = (tab: string) => {
    setActiveTab(tab);
    switch (tab) {
      case "home":
        // Already on home
        break;
      case "rides":
        router.push("/rides" as any);
        break;
      case "schedule":
        router.push("/schedule" as any);
        break;
      case "profile":
        router.push("/profile" as any);
        break;
    }
  };

  const getInitials = () => {
    return "CA"; // Captain Aris
  };

  return (
    <SafeAreaView className="flex-1 bg-surface">
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.surface} />

      <CustomStatusBar isOnline={isOnline} />

      {/* Top App Bar */}
      <View className="bg-surface border-b border-outline-variant h-16 flex-row items-center justify-between px-4">
        <View className="flex-row items-center gap-2">
          <TouchableOpacity className="p-2 rounded-full hover:bg-surface-container-high">
            <MaterialIcons name="menu" size={24} color={COLORS.primary} />
          </TouchableOpacity>
          <Text
            style={[TYPOGRAPHY.headlineMD, { fontWeight: "800" as const }]}
            className="text-primary tracking-tight"
          >
            TideFlow
          </Text>
        </View>
        <View className="flex-row items-center gap-4">
          {/* Offline Status Badge */}
          <View
            className={`flex-row items-center gap-2 px-3 py-1 rounded-full ${
              isOnline ? "bg-secondary-container/20" : "bg-surface-container"
            }`}
          >
            <MaterialIcons
              name={isOnline ? "cloud-done" : "signal-wifi-off"}
              size={16}
              color={isOnline ? COLORS.secondary : COLORS.outline}
            />
            <Text
              className={`text-[10px] font-label-caps uppercase tracking-widest ${
                isOnline ? "text-secondary" : "text-on-surface-variant"
              }`}
            >
              {isOnline ? "Connected" : "Cached"}
            </Text>
          </View>

          {/* Profile Avatar */}
          <TouchableOpacity className="w-10 h-10 rounded-full border-2 border-primary overflow-hidden items-center justify-center bg-primary/10">
            <Text className="text-primary font-bold text-sm">
              {getInitials()}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        className="flex-1"
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 100 }}
      >
        <View className="px-4 pt-6 max-w-5xl mx-auto w-full">
          {/* Welcome Section */}
          <View className="mb-6">
            <Text className="text-on-surface-variant font-label-caps uppercase text-xs">
              Operational Overview
            </Text>
            <Text
              style={TYPOGRAPHY.headlineXL}
              className="text-on-surface tracking-tight"
            >
              Good morning, Captain
            </Text>
          </View>

          {/* Bento Grid Layout */}
          <View className="flex-col gap-4">
            {/* Book a New Ride - Full Width */}
            <TouchableOpacity
              className="w-full bg-primary rounded-xl p-4 min-h-[220px] relative overflow-hidden"
              onPress={handleBookRide}
              activeOpacity={0.9}
            >
              {/* Background Image */}
              <View className="absolute inset-0 opacity-20">
                <Image
                  source={{
                    uri: "https://lh3.googleusercontent.com/aida-public/AB6AXuAS6ULCzES8_fLAab4e6JynhX0Lkievw6v82ZCFgscBDk1f5LXIJMPK-XMPSVQgxtrq3f9snuzvIhq_rjNwm_GvGr6XkxBdIouuv6EKlbsfvjSVPizM8m2lDFn-DBwJYk6WKJ1x7a_ysI_L32l10Zk5InndyYSXr17WP9IpDW-ODEiI1N9WljkISz9IUuhUY-st0hV9kg_lk18J717vOhpU_JB8jfQ7KFfrjiKUkUyOjfPHDPNgTxxbp5Yk6S65kEHYEo3KP_YGFlI",
                  }}
                  style={{ width: "100%", height: "100%" }}
                  resizeMode="cover"
                />
              </View>

              <View className="relative z-10 flex-1 justify-between">
                <View>
                  <View className="bg-primary-container w-14 h-14 rounded-xl items-center justify-center mb-4">
                    <MaterialIcons
                      name="directions-boat"
                      size={32}
                      color={COLORS.onPrimaryContainer}
                    />
                  </View>
                  <Text
                    style={TYPOGRAPHY.headlineLG}
                    className="text-white mb-2"
                  >
                    Book a New Ride
                  </Text>
                  <Text className="text-white/80 font-body-md max-w-xs">
                    Schedule your next vessel operation or charter in seconds
                    with prioritized docking.
                  </Text>
                </View>
                <View className="flex-row items-center gap-2 mt-4">
                  <Text style={TYPOGRAPHY.actionLG} className="text-white">
                    Initialize Dispatch
                  </Text>
                  <MaterialIcons name="arrow-forward" size={24} color="white" />
                </View>
              </View>
            </TouchableOpacity>

            {/* Stats Row - 2 columns */}
            <View className="flex-row gap-4">
              {/* Fleet Status */}
              <View className="flex-1 bg-surface-container-high rounded-xl p-4 flex-row items-center justify-between">
                <View>
                  <Text className="text-label-caps text-on-surface-variant">
                    FLEET STATUS
                  </Text>
                  <Text
                    style={TYPOGRAPHY.headlineMD}
                    className="text-primary font-bold"
                  >
                    12/14 Ready
                  </Text>
                </View>
                <MaterialIcons
                  name="sailing"
                  size={24}
                  color={COLORS.primary}
                />
              </View>

              {/* Next Shift */}
              <View className="flex-1 bg-tertiary-container rounded-xl p-4 flex-row items-center justify-between">
                <View>
                  <Text className="text-label-caps text-on-tertiary-container">
                    NEXT SHIFT
                  </Text>
                  <Text
                    style={TYPOGRAPHY.headlineMD}
                    className="text-on-tertiary-container font-bold"
                  >
                    08:30 AM
                  </Text>
                </View>
                <MaterialIcons
                  name="schedule"
                  size={24}
                  color={COLORS.onTertiaryContainer}
                />
              </View>
            </View>

            {/* Upcoming Rides Section */}
            <View className="mt-2">
              <View className="flex-row items-center justify-between mb-4">
                <Text style={TYPOGRAPHY.headlineMD} className="text-on-surface">
                  Upcoming Rides
                </Text>
                <TouchableOpacity onPress={handleViewAll}>
                  <Text className="text-primary font-bold text-body-sm">
                    View All
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Ride Cards */}
              <View className="space-y-4">
                {upcomingRides.map((ride) => (
                  <TouchableOpacity
                    key={ride.id}
                    className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden flex-row shadow-sm"
                    onPress={() => handleRidePress(ride.id)}
                    activeOpacity={0.7}
                  >
                    {/* Date Sidebar */}
                    <View
                      className={`w-24 flex-col items-center justify-center ${
                        ride.status === "CONFIRMED"
                          ? "bg-primary-container"
                          : "bg-surface-container-high"
                      }`}
                    >
                      <Text
                        className={`text-label-caps ${
                          ride.status === "CONFIRMED"
                            ? "text-on-primary-container"
                            : "text-on-surface-variant"
                        }`}
                      >
                        {ride.month}
                      </Text>
                      <Text
                        style={TYPOGRAPHY.headlineLG}
                        className={`font-bold ${
                          ride.status === "CONFIRMED"
                            ? "text-on-primary-container"
                            : "text-on-surface-variant"
                        }`}
                      >
                        {ride.date}
                      </Text>
                    </View>

                    {/* Ride Details */}
                    <View className="flex-1 p-4 flex-row items-center justify-between">
                      <View className="flex-1">
                        <Text
                          style={TYPOGRAPHY.headlineMD}
                          className="text-on-surface"
                        >
                          {ride.title}
                        </Text>
                        <View className="flex-row items-center gap-4 mt-1">
                          <View className="flex-row items-center gap-1">
                            <MaterialIcons
                              name="location-on"
                              size={16}
                              color={COLORS.onSurfaceVariant}
                            />
                            <Text className="text-on-surface-variant text-body-sm">
                              {ride.location}
                            </Text>
                          </View>
                          <View className="flex-row items-center gap-1">
                            <MaterialIcons
                              name="timer"
                              size={16}
                              color={COLORS.onSurfaceVariant}
                            />
                            <Text className="text-on-surface-variant text-body-sm">
                              {ride.time}
                            </Text>
                          </View>
                          {ride.hasAlert && (
                            <View className="flex-row items-center gap-1">
                              <MaterialIcons
                                name="warning"
                                size={16}
                                color={COLORS.error}
                              />
                              <Text className="text-error text-body-sm">
                                {ride.alertText}
                              </Text>
                            </View>
                          )}
                        </View>
                      </View>

                      <View className="flex-row items-center gap-3">
                        {/* Status Badge */}
                        <View
                          className={`px-3 py-1 rounded-full ${
                            ride.status === "CONFIRMED"
                              ? "bg-surface-variant"
                              : "bg-error-container"
                          }`}
                        >
                          <Text
                            className={`text-label-caps ${
                              ride.status === "CONFIRMED"
                                ? "text-on-surface-variant"
                                : "text-on-error-container"
                            }`}
                          >
                            {ride.status}
                          </Text>
                        </View>

                        {/* QR Code Button */}
                        <TouchableOpacity
                          className="w-10 h-10 rounded-full border border-outline items-center justify-center"
                          onPress={() => handleQRPress(ride.id)}
                        >
                          <MaterialIcons
                            name="qr-code-2"
                            size={24}
                            color={COLORS.primary}
                          />
                        </TouchableOpacity>
                      </View>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>
      </ScrollView>

      {/* Bottom Navigation Bar */}
      <View className="fixed bottom-0 left-0 w-full bg-surface flex-row justify-around items-center px-4 py-2 border-t border-outline-variant shadow-lg">
        {/* Home */}
        <TouchableOpacity
          className="flex-col items-center justify-center"
          onPress={() => handleTabPress("home")}
        >
          <MaterialIcons
            name="home"
            size={24}
            color={activeTab === "home" ? COLORS.primary : COLORS.outline}
          />
          <Text
            className={`text-label-caps mt-1 ${
              activeTab === "home"
                ? "text-primary font-bold"
                : "text-on-surface-variant"
            }`}
          >
            Home
          </Text>
        </TouchableOpacity>

        {/* My Rides */}
        <TouchableOpacity
          className="flex-col items-center justify-center"
          onPress={() => handleTabPress("rides")}
        >
          <MaterialIcons
            name="directions-boat"
            size={24}
            color={activeTab === "rides" ? COLORS.primary : COLORS.outline}
          />
          <Text
            className={`text-label-caps mt-1 ${
              activeTab === "rides"
                ? "text-primary font-bold"
                : "text-on-surface-variant"
            }`}
          >
            My Rides
          </Text>
        </TouchableOpacity>

        {/* Schedule */}
        <TouchableOpacity
          className="flex-col items-center justify-center"
          onPress={() => handleTabPress("schedule")}
        >
          <MaterialIcons
            name="calendar-month"
            size={24}
            color={activeTab === "schedule" ? COLORS.primary : COLORS.outline}
          />
          <Text
            className={`text-label-caps mt-1 ${
              activeTab === "schedule"
                ? "text-primary font-bold"
                : "text-on-surface-variant"
            }`}
          >
            Schedule
          </Text>
        </TouchableOpacity>

        {/* Profile */}
        <TouchableOpacity
          className="flex-col items-center justify-center"
          onPress={() => handleTabPress("profile")}
        >
          <MaterialIcons
            name="person"
            size={24}
            color={activeTab === "profile" ? COLORS.primary : COLORS.outline}
          />
          <Text
            className={`text-label-caps mt-1 ${
              activeTab === "profile"
                ? "text-primary font-bold"
                : "text-on-surface-variant"
            }`}
          >
            Profile
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}
