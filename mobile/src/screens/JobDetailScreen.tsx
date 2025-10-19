import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { ScrollView, StyleSheet, Text, View, Pressable } from "react-native";

import { Card } from "@components/Card";
import { PrimaryButton } from "@components/PrimaryButton";
import { StatusChip } from "@components/StatusChip";
import { colors, spacing, typography } from "@theme/colors";

export function JobDetailScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <LinearGradient
        colors={[colors.textPrimary, "#1F1F1F"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.banner}
      >
        <View style={styles.bannerContent}>
          <Text style={styles.bannerTitle}>Edição entregue</Text>
          <Text style={styles.bannerSubtitle}>Teaser Tour - 45 segundos</Text>
        </View>
        <StatusChip label="URL expira em 6h" tone="dark" />
      </LinearGradient>

      <Card rounded={26} padding={spacing.lg} backgroundColor={colors.surface}>
        <View style={styles.player}>
          <View style={styles.playerPreview}>
            <Ionicons name="play-circle" size={48} color={colors.textPrimary} />
          </View>
          <View style={styles.playerActions}>
            <PrimaryButton label="Baixar vídeo" onPress={() => {}} />
            <Pressable style={styles.secondaryButton}>
              <Ionicons name="share-outline" size={20} color={colors.textPrimary} />
              <Text style={styles.secondaryLabel}>Compartilhar link</Text>
            </Pressable>
          </View>
        </View>
      </Card>

      <Card rounded={24} padding={spacing.lg}>
        <Text style={styles.sectionTitle}>Feedback</Text>
        <View style={styles.feedbackRow}>
          <Pressable style={[styles.feedbackCard, styles.feedbackSuccess]}>
            <Ionicons name="checkmark-circle-outline" size={28} color={colors.textPrimary} />
            <Text style={styles.feedbackLabel}>Aprovado</Text>
          </Pressable>
          <Pressable style={[styles.feedbackCard, styles.feedbackIdea]}>
            <Ionicons name="bulb-outline" size={28} color={colors.textPrimary} />
            <Text style={styles.feedbackLabel}>Aprovado com ideia</Text>
          </Pressable>
          <Pressable style={[styles.feedbackCard, styles.feedbackRetry]}>
            <Ionicons name="refresh-outline" size={28} color={colors.surface} />
            <Text style={[styles.feedbackLabel, { color: colors.surface }]}>Refazer</Text>
          </Pressable>
        </View>
        <View style={styles.ideaBox}>
          <Text style={styles.ideaTitle}>Compartilhe sua visão</Text>
          <Text style={styles.ideaSubtitle}>
            “Comece na segunda parte da música e corte no drop aos 00:32”
          </Text>
        </View>
      </Card>

      <Card rounded={24} padding={spacing.lg}>
        <Text style={styles.sectionTitle}>Linha do tempo</Text>
        <View style={styles.timeline}>
          <View style={styles.timelineItem}>
            <View style={styles.timelineDot} />
            <View>
              <Text style={styles.timelineLabel}>Download concluído</Text>
              <Text style={styles.timelineMeta}>12 set, 14:02</Text>
            </View>
          </View>
          <View style={styles.timelineDivider} />
          <View style={styles.timelineItem}>
            <View style={styles.timelineDot} />
            <View>
              <Text style={styles.timelineLabel}>Análise de cenas</Text>
              <Text style={styles.timelineMeta}>12 set, 14:03</Text>
            </View>
          </View>
          <View style={styles.timelineDivider} />
          <View style={styles.timelineItem}>
            <View style={styles.timelineDot} />
            <View>
              <Text style={styles.timelineLabel}>Renderização entregue</Text>
              <Text style={styles.timelineMeta}>12 set, 14:05</Text>
            </View>
          </View>
        </View>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background
  },
  content: {
    gap: spacing.lg,
    padding: spacing.lg,
    paddingBottom: spacing.xxl
  },
  banner: {
    borderRadius: 28,
    padding: spacing.lg,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between"
  },
  bannerContent: {
    gap: spacing.xs
  },
  bannerTitle: {
    fontSize: typography.headingM,
    fontWeight: "700",
    color: colors.goldPrimary
  },
  bannerSubtitle: {
    fontSize: typography.body,
    color: colors.surface
  },
  player: {
    gap: spacing.lg
  },
  playerPreview: {
    height: 200,
    borderRadius: 20,
    backgroundColor: colors.surfaceMuted,
    alignItems: "center",
    justifyContent: "center"
  },
  playerActions: {
    gap: spacing.sm
  },
  secondaryButton: {
    flexDirection: "row",
    gap: spacing.xs,
    alignItems: "center",
    alignSelf: "flex-start",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 16,
    backgroundColor: colors.surfaceMuted
  },
  secondaryLabel: {
    fontWeight: "600",
    color: colors.textPrimary
  },
  sectionTitle: {
    fontSize: typography.headingS,
    fontWeight: "700",
    color: colors.textPrimary,
    marginBottom: spacing.sm
  },
  feedbackRow: {
    flexDirection: "row",
    gap: spacing.sm,
    marginBottom: spacing.md
  },
  feedbackCard: {
    flex: 1,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: spacing.md,
    gap: spacing.xs
  },
  feedbackSuccess: {
    backgroundColor: colors.accentMint
  },
  feedbackIdea: {
    backgroundColor: colors.goldPrimary
  },
  feedbackRetry: {
    backgroundColor: colors.accentCoral
  },
  feedbackLabel: {
    fontWeight: "600",
    color: colors.textPrimary,
    textAlign: "center"
  },
  ideaBox: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: 18,
    padding: spacing.md,
    gap: spacing.xs
  },
  ideaTitle: {
    fontWeight: "600",
    color: colors.textPrimary
  },
  ideaSubtitle: {
    fontSize: typography.body,
    color: colors.textMuted,
    lineHeight: 20
  },
  timeline: {
    gap: spacing.sm
  },
  timelineItem: {
    flexDirection: "row",
    gap: spacing.md,
    alignItems: "center"
  },
  timelineDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: colors.goldPrimary
  },
  timelineDivider: {
    height: 32,
    marginLeft: 7,
    borderLeftWidth: 2,
    borderLeftColor: colors.border
  },
  timelineLabel: {
    fontSize: typography.body,
    fontWeight: "600",
    color: colors.textPrimary
  },
  timelineMeta: {
    fontSize: typography.caption,
    color: colors.textMuted
  }
});
