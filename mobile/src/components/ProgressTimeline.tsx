import { StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "@theme/colors";
import { StatusChip } from "./StatusChip";

type Step = {
  id: string;
  label: string;
  status: "pending" | "active" | "completed";
  description?: string;
};

type Props = {
  steps: Step[];
};

export function ProgressTimeline({ steps }: Props) {
  return (
    <View style={styles.container} accessibilityRole="list">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;
        const indicatorStyle = {
          backgroundColor:
            step.status === "completed"
              ? colors.goldPrimary
              : step.status === "active"
              ? colors.goldSecondary
              : colors.border
        };

        return (
          <View key={step.id} style={styles.step} accessibilityRole="listitem">
            <View style={styles.indicatorColumn}>
              <View style={[styles.indicator, indicatorStyle]} />
              {!isLast && <View style={styles.line} />}
            </View>
            <View style={styles.content}>
              <Text style={styles.label}>{step.label}</Text>
              {step.description ? (
                <Text style={styles.description}>{step.description}</Text>
              ) : null}
              <StatusChip
                label={
                  step.status === "completed"
                    ? "Concluído"
                    : step.status === "active"
                    ? "Em andamento"
                    : "Na fila"
                }
                tone={
                  step.status === "completed"
                    ? "success"
                    : step.status === "active"
                    ? "warning"
                    : "default"
                }
              />
            </View>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
    gap: spacing.lg
  },
  step: {
    flexDirection: "row",
    gap: spacing.md
  },
  indicatorColumn: {
    alignItems: "center"
  },
  indicator: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: colors.surface,
    marginTop: spacing.xs
  },
  line: {
    width: 2,
    flex: 1,
    backgroundColor: colors.border,
    marginTop: spacing.xs
  },
  content: {
    flex: 1,
    backgroundColor: colors.surfaceMuted,
    borderRadius: 16,
    padding: spacing.md
  },
  label: {
    fontSize: typography.headingS,
    fontWeight: "600",
    color: colors.textPrimary,
    marginBottom: spacing.xs / 1.5
  },
  description: {
    fontSize: typography.body,
    color: colors.textMuted,
    marginBottom: spacing.xs
  }
});
