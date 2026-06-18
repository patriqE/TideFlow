export type Slide = {
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

export const slides: Slide[] = [
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
