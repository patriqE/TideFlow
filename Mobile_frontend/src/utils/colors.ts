export const COLORS = {
  primary: "#003667",
  primaryContainer: "#0a4d8c",
  primaryFixed: "#d4e3ff",
  primaryFixedDim: "#a5c8ff",
  onPrimary: "#ffffff",
  onPrimaryContainer: "#94bfff",
  onPrimaryFixed: "#001c3a",
  onPrimaryFixedVariant: "#004785",

  secondary: "#006874",
  secondaryContainer: "#4de7fd",
  secondaryFixed: "#98f0ff",
  secondaryFixedDim: "#37d9ee",
  onSecondary: "#ffffff",
  onSecondaryContainer: "#006571",
  onSecondaryFixed: "#001f24",
  onSecondaryFixedVariant: "#004f58",

  tertiary: "#592800",
  tertiaryContainer: "#7b3a00",
  tertiaryFixed: "#ffdbc7",
  tertiaryFixedDim: "#ffb688",
  onTertiary: "#ffffff",
  onTertiaryContainer: "#ffa96f",
  onTertiaryFixed: "#311300",
  onTertiaryFixedVariant: "#733600",

  error: "#ba1a1a",
  errorContainer: "#ffdad6",
  onError: "#ffffff",
  onErrorContainer: "#93000a",

  surface: "#f9f9ff",
  surfaceBright: "#f9f9ff",
  surfaceDim: "#cfdaf1",
  surfaceContainer: "#e7eeff",
  surfaceContainerLow: "#f0f3ff",
  surfaceContainerLowest: "#ffffff",
  surfaceContainerHigh: "#dee8ff",
  surfaceContainerHighest: "#d8e3fa",
  onSurface: "#111c2c",
  onSurfaceVariant: "#424750",

  outline: "#727781",
  outlineVariant: "#c2c6d2",

  inverseSurface: "#263142",
  inverseOnSurface: "#ebf1ff",
  inversePrimary: "#a5c8ff",

  background: "#f9f9ff",
  onBackground: "#111c2c",

  surfaceTint: "#285f9f",

  white: "#ffffff",
  black: "#000000",
  transparent: "transparent",
} as const;

export const TYPOGRAPHY = {
  headlineXL: {
    fontSize: 32,
    lineHeight: 38.4,
    fontWeight: "700" as const,
    letterSpacing: -0.02,
  },
  headlineLG: {
    fontSize: 24,
    lineHeight: 31.2,
    fontWeight: "600" as const,
  },
  headlineMD: {
    fontSize: 20,
    lineHeight: 28,
    fontWeight: "600" as const,
  },
  bodyLG: {
    fontSize: 18,
    lineHeight: 28.8,
    fontWeight: "400" as const,
  },
  bodyMD: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: "400" as const,
  },
  bodySM: {
    fontSize: 14,
    lineHeight: 21,
    fontWeight: "400" as const,
  },
  actionLG: {
    fontSize: 18,
    lineHeight: 21.6,
    fontWeight: "600" as const,
  },
  labelCaps: {
    fontSize: 12,
    lineHeight: 14.4,
    fontWeight: "700" as const,
    letterSpacing: 0.6,
    textTransform: "uppercase" as const,
  },
} as const;
