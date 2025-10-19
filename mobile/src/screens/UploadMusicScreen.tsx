import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";

import { PrimaryButton } from "@components/PrimaryButton";
import { colors, spacing, typography } from "@theme/colors";

export function UploadMusicScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <LinearGradient
        colors={[colors.goldPrimary, colors.goldSecondary]}
        style={styles.dropZone}
        start={{ x: 0, y: 0.5 }}
        end={{ x: 1, y: 0.5 }}
      >
        <Ionicons name="cloud-upload-outline" size={48} color={colors.textPrimary} />
        <Text style={styles.dropZoneTitle}>Arraste sua música aqui</Text>
        <Text style={styles.dropZoneSubtitle}>
          Aceitamos formatos WAV, AIFF, MP3. Até 500 MB.
        </Text>
        <Pressable style={styles.dropButton}>
          <Text style={styles.dropButtonLabel}>Selecionar arquivo</Text>
        </Pressable>
      </LinearGradient>

      <View style={styles.form}>
        <Text style={styles.sectionTitle}>Detalhes da faixa</Text>
        <View style={styles.field}>
          <Text style={styles.label}>Título</Text>
          <TextInput
            placeholder="Ex: Doze Intro"
            placeholderTextColor={colors.textMuted}
            style={styles.input}
          />
        </View>
        <View style={styles.row}>
          <View style={[styles.field, { flex: 1 }]}>
            <Text style={styles.label}>Gênero</Text>
            <TextInput
              placeholder="Trap, R&B, etc."
              placeholderTextColor={colors.textMuted}
              style={styles.input}
            />
          </View>
          <View style={[styles.field, { width: 110 }]}>
            <Text style={styles.label}>BPM</Text>
            <TextInput
              placeholder="120"
              placeholderTextColor={colors.textMuted}
              keyboardType="numeric"
              style={styles.input}
            />
          </View>
        </View>
        <View style={styles.field}>
          <Text style={styles.label}>Notas criativas</Text>
          <TextInput
            placeholder="Conte à IA onde estão os momentos chave..."
            placeholderTextColor={colors.textMuted}
            style={[styles.input, styles.textarea]}
            multiline
            numberOfLines={4}
          />
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Aprendizado automático</Text>
        <Text style={styles.cardText}>
          Após o upload, transcrevemos a música inteira para alinhar com seus vídeos.
          Você poderá ajustar a transcrição antes de aprovar futuras edições.
        </Text>
      </View>

      <PrimaryButton label="Enviar música" onPress={() => {}} />
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
  dropZone: {
    borderRadius: 28,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.xl,
    gap: spacing.sm
  },
  dropZoneTitle: {
    fontSize: typography.headingM,
    fontWeight: "700",
    color: colors.textPrimary
  },
  dropZoneSubtitle: {
    fontSize: typography.body,
    color: colors.textPrimary,
    textAlign: "center"
  },
  dropButton: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: 20,
    marginTop: spacing.sm
  },
  dropButtonLabel: {
    fontWeight: "600",
    color: colors.textPrimary
  },
  form: {
    backgroundColor: colors.surface,
    borderRadius: 24,
    padding: spacing.lg,
    gap: spacing.md,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 4
  },
  sectionTitle: {
    fontSize: typography.headingS,
    fontWeight: "600",
    color: colors.textPrimary
  },
  field: {
    gap: spacing.xs
  },
  label: {
    fontSize: typography.caption,
    fontWeight: "600",
    color: colors.textSecondary
  },
  input: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: 16,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: typography.body,
    color: colors.textPrimary,
    borderWidth: 1,
    borderColor: colors.border
  },
  textarea: {
    minHeight: 120,
    textAlignVertical: "top"
  },
  row: {
    flexDirection: "row",
    gap: spacing.md
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 24,
    padding: spacing.lg,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 14,
    elevation: 3
  },
  cardText: {
    fontSize: typography.body,
    color: colors.textMuted,
    marginTop: spacing.sm,
    lineHeight: 22
  }
});
