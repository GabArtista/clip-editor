import { ReactNode } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "@theme/colors";

type Props = {
  label: string;
  icon: ReactNode;
  onPress: () => void;
  accent?: "primary" | "neutral" | "danger";
};

export function QuickActionButton({
  label,
  icon,
  onPress,
  accent = "primary"
}: Props) {
  const palette = {
    primary: {
      backgroundColor: colors.goldPrimary,
      color: colors.textPrimary
    },
    neutral: {
      backgroundColor: colors.surface,
      color: colors.textPrimary
    },
    danger: {
      backgroundColor: colors.accentCoral,
      color: colors.surface
    }
  }[accent];

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        {
          backgroundColor: palette.backgroundColor
        },
        pressed && styles.pressed
      ]}
      accessibilityRole="button"
      accessibilityLabel={label}
    >
      <View style={styles.iconContainer}>{icon}</View>
      <Text style={[styles.label, { color: palette.color }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    width: "48%",
    borderRadius: 20,
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-start",
    gap: spacing.md,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 3
  },
  pressed: {
    opacity: 0.9,
    transform: [{ scale: 0.98 }]
  },
  iconContainer: {
    backgroundColor: "rgba(0,0,0,0.06)",
    padding: spacing.sm,
    borderRadius: 16
  },
  label: {
    fontSize: typography.headingS,
    fontWeight: "600"
  }
});
