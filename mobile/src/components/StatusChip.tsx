import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "@theme/colors";

type Props = {
  label: string;
  tone?: "default" | "success" | "warning" | "error" | "dark";
};

const toneStyles = {
  default: {
    bg: colors.surfaceMuted,
    text: colors.textPrimary
  },
  success: {
    bg: colors.accentMint,
    text: colors.textPrimary
  },
  warning: {
    bg: colors.accentWarning,
    text: colors.textPrimary
  },
  error: {
    bg: colors.accentCoral,
    text: colors.surface
  },
  dark: {
    bg: colors.textPrimary,
    text: colors.goldPrimary
  }
} as const;

export function StatusChip({ label, tone = "default" }: Props) {
  const selected = toneStyles[tone];

  return (
    <View
      accessibilityRole="text"
      style={[styles.chip, { backgroundColor: selected.bg }]}
    >
      <Text style={[styles.label, { color: selected.text }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    borderRadius: 999,
    paddingVertical: spacing.xs / 1.5,
    paddingHorizontal: spacing.md
  },
  label: {
    fontSize: typography.caption,
    fontWeight: "600",
    letterSpacing: 0.4
  }
});
