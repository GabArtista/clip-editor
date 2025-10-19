import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { LinearGradient } from "expo-linear-gradient";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { Card } from "@components/Card";
import { PrimaryButton } from "@components/PrimaryButton";
import { ProgressTimeline } from "@components/ProgressTimeline";
import { QuickActionButton } from "@components/QuickActionButton";
import { StatusChip } from "@components/StatusChip";
import { colors, spacing, typography } from "@theme/colors";
import { RootStackParamList } from "@navigation/types";

type Navigation = NativeStackNavigationProp<RootStackParamList>;

const mockJobs = [
  {
    id: "job-123",
    title: "Reels - Release 15/09",
    music: "DOZE - Intro",
    status: "processing",
    progress: [
      { id: "download", label: "Download do Reels", status: "completed" as const },
      { id: "analysis", label: "Análise de cenas", status: "active" as const },
      { id: "mix", label: "Combinar com música", status: "pending" as const },
      { id: "render", label: "Renderizar", status: "pending" as const }
    ]
  }
];

const recentEdits = [
  {
    id: "1",
    title: "Teaser Tour",
    status: "Entregue",
    tone: "success" as const,
    deliveredAt: "Há 2 horas"
  },
  {
    id: "2",
    title: "Clube Set",
    status: "Em revisão",
    tone: "warning" as const,
    deliveredAt: "Ontem"
  }
];

export function HomeScreen() {
  const navigation = useNavigation<Navigation>();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <LinearGradient
        colors={[colors.goldPrimary, colors.goldSecondary]}
        style={styles.hero}
        start={{ x: 0, y: 0.5 }}
        end={{ x: 1, y: 0.5 }}
      >
        <View style={styles.heroProfile}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>DOZE</Text>
          </View>
          <View style={styles.heroInfo}>
            <Text style={styles.heroGreeting}>Bem-vindo de volta!</Text>
            <Text style={styles.heroSubtitle}>Vamos criar algo épico hoje?</Text>
          </View>
        </View>
        <StatusChip label="Cookies Instagram válidos" tone="dark" />
      </LinearGradient>

      <View style={styles.actionsRow}>
        <QuickActionButton
          label="Subir música"
          icon={<Ionicons name="cloud-upload-outline" size={24} color={colors.textPrimary} />}
          onPress={() => navigation.navigate("UploadMusic")}
        />
        <QuickActionButton
          label="Editar Reels"
          icon={<Ionicons name="film-outline" size={24} color={colors.textPrimary} />}
          onPress={() => navigation.navigate("NewReel", {})}
        />
      </View>
      <View style={styles.actionsRow}>
        <QuickActionButton
          label="Transcrições"
          icon={<Ionicons name="document-text-outline" size={24} color={colors.textPrimary} />}
          onPress={() => navigation.navigate("TranscriptEditor", { musicId: "demo" })}
          accent="neutral"
        />
        <QuickActionButton
          label="Limpar cache"
          icon={<Ionicons name="trash-outline" size={24} color={colors.surface} />}
          onPress={() => {
            // TODO: Hook to backend cleanup endpoint
          }}
          accent="danger"
        />
      </View>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Edições recentes</Text>
        <Text style={styles.sectionAction}>Ver tudo</Text>
      </View>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.cardsRow}
      >
        {recentEdits.map((item) => (
          <Card key={item.id} padding={spacing.lg} rounded={24}>
            <View style={styles.recentCard}>
              <View style={styles.thumbnailPlaceholder}>
                <Ionicons name="play-outline" size={32} color={colors.textPrimary} />
              </View>
              <Text style={styles.recentTitle}>{item.title}</Text>
              <StatusChip label={item.status} tone={item.tone} />
              <Text style={styles.recentSubtitle}>{item.deliveredAt}</Text>
              <PrimaryButton
                label="Abrir"
                onPress={() => navigation.navigate("JobDetail", { jobId: item.id })}
              />
            </View>
          </Card>
        ))}
      </ScrollView>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Fila em andamento</Text>
        <Text style={styles.sectionSubtitle}>Acompanhe cada etapa em tempo real</Text>
      </View>

      {mockJobs.map((job) => (
        <Card key={job.id} rounded={22}>
          <View style={styles.jobHeader}>
            <View>
              <Text style={styles.jobTitle}>{job.title}</Text>
              <Text style={styles.jobSubtitle}>Música: {job.music}</Text>
            </View>
            <StatusChip label="Processando" tone="warning" />
          </View>
          <ProgressTimeline steps={job.progress} />
        </Card>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl
  },
  hero: {
    borderRadius: 28,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    gap: spacing.sm
  },
  heroProfile: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md
  },
  avatar: {
    width: 60,
    height: 60,
    borderRadius: 18,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center"
  },
  avatarText: {
    fontWeight: "700",
    fontSize: 18,
    color: colors.textPrimary
  },
  heroInfo: {
    flex: 1
  },
  heroGreeting: {
    fontSize: typography.headingM,
    fontWeight: "700",
    color: colors.textPrimary
  },
  heroSubtitle: {
    color: colors.textPrimary,
    fontSize: typography.body
  },
  actionsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.lg
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    marginTop: spacing.lg,
    marginBottom: spacing.sm
  },
  sectionTitle: {
    fontSize: typography.headingM,
    fontWeight: "700",
    color: colors.textPrimary
  },
  sectionAction: {
    fontSize: typography.caption,
    fontWeight: "600",
    color: colors.textMuted
  },
  sectionSubtitle: {
    fontSize: typography.body,
    color: colors.textMuted
  },
  cardsRow: {
    gap: spacing.lg,
    paddingRight: spacing.lg
  },
  recentCard: {
    width: 240,
    gap: spacing.sm
  },
  thumbnailPlaceholder: {
    height: 120,
    borderRadius: 20,
    backgroundColor: colors.surfaceMuted,
    alignItems: "center",
    justifyContent: "center"
  },
  recentTitle: {
    fontSize: typography.headingS,
    fontWeight: "600",
    color: colors.textPrimary
  },
  recentSubtitle: {
    fontSize: typography.caption,
    color: colors.textMuted
  },
  jobHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.md
  },
  jobTitle: {
    fontSize: typography.headingS,
    fontWeight: "600",
    color: colors.textPrimary
  },
  jobSubtitle: {
    fontSize: typography.body,
    color: colors.textMuted
  }
});
