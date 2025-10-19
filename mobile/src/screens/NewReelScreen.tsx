import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  Pressable
} from "react-native";

import { Card } from "@components/Card";
import { PrimaryButton } from "@components/PrimaryButton";
import { StatusChip } from "@components/StatusChip";
import { colors, spacing, typography } from "@theme/colors";

const availableMusic = [
  { id: "music-1", title: "Doze Intro", status: "ready" },
  { id: "music-2", title: "Ensaio Final", status: "ready" },
  { id: "music-3", title: "Gratidão", status: "processing" }
];

export function NewReelScreen() {
  const [selectedMusic, setSelectedMusic] = useState<string>("music-1");

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Card rounded={26} padding={spacing.lg}>
        <Text style={styles.stepTitle}>1. Cole o link do Reels</Text>
        <TextInput
          placeholder="https://www.instagram.com/reel/..."
          placeholderTextColor={colors.textMuted}
          style={styles.input}
          keyboardType="url"
          autoCapitalize="none"
        />
        <Pressable style={styles.detectButton}>
          <Ionicons name="search-outline" size={20} color={colors.textPrimary} />
          <Text style={styles.detectLabel}>Detectar detalhes</Text>
        </Pressable>
      </Card>

      <Card rounded={26} padding={spacing.lg}>
        <Text style={styles.stepTitle}>2. Escolha a música</Text>
        <View style={styles.musicList}>
          {availableMusic.map((music) => {
            const isSelected = selectedMusic === music.id;
            const disabled = music.status !== "ready";
            return (
              <Pressable
                key={music.id}
                style={[
                  styles.musicItem,
                  isSelected && styles.musicItemSelected,
                  disabled && styles.musicItemDisabled
                ]}
                onPress={() => !disabled && setSelectedMusic(music.id)}
                accessibilityState={{ selected: isSelected, disabled }}
              >
                <View style={styles.musicIcon}>
                  <Ionicons
                    name={isSelected ? "musical-note" : "musical-notes-outline"}
                    size={22}
                    color={colors.textPrimary}
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.musicTitle}>{music.title}</Text>
                  <Text style={styles.musicSubtitle}>Transcrição concluída</Text>
                </View>
                <StatusChip
                  label={music.status === "ready" ? "Pronta" : "Processando"}
                  tone={music.status === "ready" ? "success" : "warning"}
                />
              </Pressable>
            );
          })}
        </View>

        <View style={styles.sliderCard}>
          <Text style={styles.sliderLabel}>Impacto da música</Text>
          <View style={styles.sliderMock} />
          <Text style={styles.sliderCaption}>Ajuste a energia da música vs. áudio original.</Text>
        </View>
        <View style={styles.sliderCard}>
          <Text style={styles.sliderLabel}>Impacto do vídeo</Text>
          <View style={styles.sliderMock} />
          <Text style={styles.sliderCaption}>Sincronize cortes com as batidas detectadas.</Text>
        </View>

        <Text style={styles.label}>Notas para a IA</Text>
        <TextInput
          placeholder="Ex: Comece no verso 2 e destaque quando digo 'Doze'."
          placeholderTextColor={colors.textMuted}
          style={[styles.input, styles.textarea]}
          multiline
        />
      </Card>

      <Card rounded={26} padding={spacing.lg}>
        <Text style={styles.stepTitle}>3. Resumo</Text>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Música</Text>
          <Text style={styles.summaryValue}>Doze Intro</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Duração do Reels</Text>
          <Text style={styles.summaryValue}>00:45</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Entrega estimada</Text>
          <Text style={styles.summaryValue}>~2 minutos</Text>
        </View>
      </Card>

      <PrimaryButton label="Gerar edição" onPress={() => {}} />
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
  stepTitle: {
    fontSize: typography.headingS,
    fontWeight: "700",
    color: colors.textPrimary,
    marginBottom: spacing.sm
  },
  input: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: typography.body,
    color: colors.textPrimary
  },
  detectButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    marginTop: spacing.sm,
    alignSelf: "flex-start",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 16,
    backgroundColor: colors.goldHighlight
  },
  detectLabel: {
    fontWeight: "600",
    color: colors.textPrimary
  },
  musicList: {
    gap: spacing.sm,
    marginBottom: spacing.lg
  },
  musicItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    backgroundColor: colors.surfaceMuted,
    borderRadius: 18,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: "transparent"
  },
  musicItemSelected: {
    backgroundColor: colors.surface,
    borderColor: colors.goldPrimary,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.14,
    shadowRadius: 14,
    elevation: 3
  },
  musicItemDisabled: {
    opacity: 0.5
  },
  musicIcon: {
    backgroundColor: colors.goldPrimary,
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center"
  },
  musicTitle: {
    fontSize: typography.headingS,
    fontWeight: "600",
    color: colors.textPrimary
  },
  musicSubtitle: {
    fontSize: typography.caption,
    color: colors.textMuted
  },
  sliderCard: {
    marginTop: spacing.sm,
    gap: spacing.xs
  },
  sliderLabel: {
    fontWeight: "600",
    fontSize: typography.body,
    color: colors.textSecondary
  },
  sliderMock: {
    height: 6,
    borderRadius: 6,
    backgroundColor: colors.goldPrimary
  },
  sliderCaption: {
    fontSize: typography.caption,
    color: colors.textMuted
  },
  textarea: {
    minHeight: 120,
    textAlignVertical: "top"
  },
  label: {
    marginTop: spacing.md,
    marginBottom: spacing.xs,
    fontWeight: "600",
    color: colors.textSecondary
  },
  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.sm
  },
  summaryLabel: {
    fontSize: typography.body,
    color: colors.textMuted
  },
  summaryValue: {
    fontSize: typography.body,
    fontWeight: "600",
    color: colors.textPrimary
  }
});
