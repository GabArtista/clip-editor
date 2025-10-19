import { ReactNode } from "react";
import { StyleSheet, View } from "react-native";

import { colors, spacing } from "@theme/colors";

type Props = {
  children: ReactNode;
  elevated?: boolean;
  padding?: number;
  rounded?: number;
  backgroundColor?: string;
};

export function Card({
  children,
  elevated = true,
  padding = spacing.lg,
  rounded = 20,
  backgroundColor = colors.surface
}: Props) {
  return (
    <View
      style={[
        styles.card,
        { padding, borderRadius: rounded, backgroundColor },
        elevated && styles.elevated
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: "100%"
  },
  elevated: {
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.16,
    shadowRadius: 18,
    elevation: 4
  }
});
