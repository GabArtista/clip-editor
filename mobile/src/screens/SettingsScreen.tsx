import { Ionicons } from "@expo/vector-icons";
import { ScrollView, StyleSheet, Switch, Text, View, Pressable } from "react-native";

import { Card } from "@components/Card";
import { PrimaryButton } from "@components/PrimaryButton";
import { colors, spacing, typography } from "@theme/colors";

export function SettingsScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Card rounded={22} padding={spacing.lg}>
        <Text style={styles.sectionTitle}>Conta</Text>
        <View style={styles.row}>
          <View>
            <Text style={styles.primaryText}>doze@studio.com</Text>
            <Text style={styles.secondaryText}>Plano Creator</Text>
          </View>
          <PrimaryButton label="Gerenciar assinatura" onPress={() => {}} />
        </View>
      </Card>

      <Card rounded={22} padding={spacing.lg}>
        <Text style={styles.sectionTitle}>Instagram vinculado</Text>
        <View style={[styles.row, styles.rowAlign]}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>IG</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.primaryText}>@doze.oficial</Text>
            <Text style={styles.secondaryText}>Cookies válidos até 20 set 2024</Text>
          </View>
          <Pressable style={styles.secondaryButton}>
            <Ionicons name="refresh-outline" size={18} color={colors.textPrimary} />
            <Text style={styles.secondaryButtonLabel}>Atualizar cookies</Text>
          </Pressable>
        </View>
        <Pressable style={styles.uploadZone}>
          <Ionicons name="document-text-outline" size={22} color={colors.textPrimary} />
          <Text style={styles.uploadText}>Enviar JSON de cookies</Text>
        </Pressable>
      </Card>

      <Card rounded={22} padding={spacing.lg}>
        <Text style={styles.sectionTitle}>Preferências</Text>
        <View style={styles.preferenceRow}>
          <View>
            <Text style={styles.primaryText}>Notificações push</Text>
            <Text style={styles.secondaryText}>Receber alertas quando a edição ficar pronta</Text>
          </View>
          <Switch value trackColor={{ true: colors.goldPrimary }} />
        </View>
        <View style={styles.preferenceRow}>
          <View>
            <Text style={styles.primaryText}>Limpeza automática</Text>
            <Text style={styles.secondaryText}>Remover vídeos após 24 horas</Text>
          </View>
          <Switch value trackColor={{ true: colors.goldPrimary }} />
        </View>
        <View style={styles.preferenceRow}>
          <View>
            <Text style={styles.primaryText}>Modo escuro</Text>
            <Text style={styles.secondaryText}>Em breve</Text>
          </View>
          <Switch value={false} trackColor={{ true: colors.goldPrimary }} disabled />
        </View>
      </Card>

      <Card rounded={22} padding={spacing.lg} backgroundColor={colors.accentCoral}>
        <Text style={[styles.sectionTitle, { color: colors.surface }]}>Zona de risco</Text>
        <Text style={[styles.secondaryText, { color: colors.surface }]}>
          Exclua todos os dados da conta. Esta ação é irreversível.
        </Text>
        <Pressable style={styles.dangerButton}>
          <Ionicons name="trash-outline" size={18} color={colors.surface} />
          <Text style={styles.dangerLabel}>Excluir conta</Text>
        </Pressable>
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
  sectionTitle: {
    fontSize: typography.headingS,
    fontWeight: "700",
    color: colors.textPrimary,
    marginBottom: spacing.sm
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: spacing.md
  },
  rowAlign: {
    alignItems: "center",
    marginBottom: spacing.md
  },
  primaryText: {
    fontSize: typography.body,
    fontWeight: "600",
    color: colors.textPrimary
  },
  secondaryText: {
    fontSize: typography.caption,
    color: colors.textMuted
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: colors.goldPrimary,
    alignItems: "center",
    justifyContent: "center"
  },
  avatarText: {
    fontWeight: "700",
    color: colors.textPrimary
  },
  secondaryButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 14,
    backgroundColor: colors.surfaceMuted
  },
  secondaryButtonLabel: {
    fontWeight: "600",
    color: colors.textPrimary
  },
  uploadZone: {
    marginTop: spacing.md,
    borderRadius: 16,
    borderWidth: 1,
    borderStyle: "dashed",
    borderColor: colors.goldPrimary,
    paddingVertical: spacing.lg,
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    backgroundColor: colors.surfaceMuted
  },
  uploadText: {
    fontWeight: "600",
    color: colors.textPrimary
  },
  preferenceRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingVertical: spacing.md
  },
  dangerButton: {
    marginTop: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.surface
  },
  dangerLabel: {
    fontWeight: "600",
    color: colors.surface
  }
});
