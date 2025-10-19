import { Ionicons } from "@expo/vector-icons";
import {
  FlatList,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View
} from "react-native";

import { PrimaryButton } from "@components/PrimaryButton";
import { StatusChip } from "@components/StatusChip";
import { colors, spacing, typography } from "@theme/colors";

const transcriptMock = [
  { id: "1", time: "00:00", text: "Intro instrumental com synth e beat suave." },
  {
    id: "2",
    time: "00:16",
    text: "Yeah, a noite cai e a cidade desperta, luzes dançam na janela."
  },
  { id: "3", time: "00:30", text: "Batida cresce, público vibra, refrão pronto pra explodir." }
];

export function TranscriptEditorScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Doze Intro</Text>
          <Text style={styles.subtitle}>Transcrição automática pronta.</Text>
        </View>
        <StatusChip label="Sincronizada" tone="dark" />
      </View>

      <View style={styles.waveformCard}>
        <View style={styles.waveDummy} />
        <Pressable style={styles.playButton}>
          <Ionicons name="play" size={26} color={colors.textPrimary} />
        </Pressable>
      </View>

      <FlatList
        data={transcriptMock}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        ItemSeparatorComponent={() => <View style={{ height: spacing.sm }} />}
        renderItem={({ item }) => (
          <View style={styles.lineItem}>
            <View style={styles.timeBadge}>
              <Text style={styles.timeText}>{item.time}</Text>
            </View>
            <View style={styles.lineContent}>
              <Text style={styles.lineText}>{item.text}</Text>
              <View style={styles.lineActions}>
                <Pressable style={styles.lineButton}>
                  <Ionicons name="create-outline" size={18} color={colors.textPrimary} />
                  <Text style={styles.lineButtonLabel}>Editar</Text>
                </Pressable>
                <Pressable style={styles.lineButton}>
                  <Ionicons name="refresh-outline" size={18} color={colors.textPrimary} />
                  <Text style={styles.lineButtonLabel}>Reverter</Text>
                </Pressable>
              </View>
            </View>
          </View>
        )}
      />

      <View style={styles.footer}>
        <PrimaryButton label="Salvar alterações" onPress={() => {}} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    padding: spacing.lg
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.lg
  },
  title: {
    fontSize: typography.headingM,
    fontWeight: "700",
    color: colors.textPrimary
  },
  subtitle: {
    fontSize: typography.body,
    color: colors.textMuted
  },
  waveformCard: {
    backgroundColor: colors.surface,
    borderRadius: 24,
    padding: spacing.md,
    marginBottom: spacing.lg,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 14,
    elevation: 3
  },
  waveDummy: {
    height: 90,
    borderRadius: 18,
    backgroundColor: colors.surfaceMuted
  },
  playButton: {
    position: "absolute",
    right: spacing.md,
    bottom: spacing.md,
    backgroundColor: colors.goldPrimary,
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 5
  },
  listContent: {
    paddingBottom: spacing.xxl
  },
  lineItem: {
    flexDirection: "row",
    gap: spacing.md,
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: 18,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 2
  },
  timeBadge: {
    backgroundColor: colors.goldPrimary,
    borderRadius: 14,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    alignSelf: "flex-start"
  },
  timeText: {
    fontWeight: "700",
    color: colors.textPrimary
  },
  lineContent: {
    flex: 1,
    gap: spacing.sm
  },
  lineText: {
    fontSize: typography.body,
    lineHeight: 22,
    color: colors.textSecondary
  },
  lineActions: {
    flexDirection: "row",
    gap: spacing.md
  },
  lineButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    backgroundColor: colors.surfaceMuted,
    borderRadius: 12,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm
  },
  lineButtonLabel: {
    fontSize: typography.caption,
    fontWeight: "600",
    color: colors.textPrimary
  },
  footer: {
    position: "absolute",
    left: spacing.lg,
    right: spacing.lg,
    bottom: spacing.lg
  }
});
