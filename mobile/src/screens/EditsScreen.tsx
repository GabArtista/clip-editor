import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import {
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View
} from "react-native";

import { Card } from "@components/Card";
import { StatusChip } from "@components/StatusChip";
import { colors, spacing, typography } from "@theme/colors";
import { RootStackParamList } from "@navigation/types";

const jobs = [
  {
    id: "job-1",
    title: "Campanha Outubro",
    createdAt: "12 set 2024",
    status: "delivered",
    length: "00:45",
    music: "Doze Intro"
  },
  {
    id: "job-2",
    title: "Teaser Tour",
    createdAt: "10 set 2024",
    status: "queued",
    length: "01:00",
    music: "Ensaio Final"
  },
  {
    id: "job-3",
    title: "Aftermovie Club",
    createdAt: "05 set 2024",
    status: "processing",
    length: "00:30",
    music: "Gratidão"
  }
];

const statusTone = {
  delivered: { label: "Entregue", tone: "success" as const },
  queued: { label: "Na fila", tone: "default" as const },
  processing: { label: "Processando", tone: "warning" as const }
};

type Navigation = NativeStackNavigationProp<RootStackParamList>;

export function EditsScreen() {
  const navigation = useNavigation<Navigation>();

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Edições</Text>
        <Pressable
          style={styles.primaryCTA}
          onPress={() => navigation.navigate("NewReel", {})}
        >
          <Ionicons name="sparkles-outline" size={20} color={colors.textPrimary} />
          <Text style={styles.primaryLabel}>Nova edição</Text>
        </Pressable>
      </View>

      <FlatList
        data={jobs}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        ItemSeparatorComponent={() => <View style={{ height: spacing.md }} />}
        renderItem={({ item }) => {
          const tone = statusTone[item.status as keyof typeof statusTone];
          return (
            <Card rounded={20} padding={spacing.md}>
              <Pressable
                style={styles.item}
                onPress={() => navigation.navigate("JobDetail", { jobId: item.id })}
              >
                <View style={styles.itemHeader}>
                  <Text style={styles.itemTitle}>{item.title}</Text>
                  <StatusChip label={tone.label} tone={tone.tone} />
                </View>
                <Text style={styles.itemSubtitle}>Criado em {item.createdAt}</Text>
                <View style={styles.metaRow}>
                  <View style={styles.metaBadge}>
                    <Ionicons name="time-outline" size={16} color={colors.textPrimary} />
                    <Text style={styles.metaText}>{item.length}</Text>
                  </View>
                  <View style={styles.metaBadge}>
                    <Ionicons name="musical-note" size={16} color={colors.textPrimary} />
                    <Text style={styles.metaText}>{item.music}</Text>
                  </View>
                </View>
              </Pressable>
            </Card>
          );
        }}
      />
    </View>
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
  primaryCTA: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    backgroundColor: colors.goldPrimary,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 16
  },
  primaryLabel: {
    fontWeight: "600",
    color: colors.textPrimary
  },
  listContent: {
    paddingBottom: spacing.xxl
  },
  item: {
    gap: spacing.sm
  },
  itemHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  itemTitle: {
    fontSize: typography.headingS,
    fontWeight: "600",
    color: colors.textPrimary
  },
  itemSubtitle: {
    fontSize: typography.caption,
    color: colors.textMuted
  },
  metaRow: {
    flexDirection: "row",
    gap: spacing.sm
  },
  metaBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 12
  },
  metaText: {
    fontSize: typography.caption,
    fontWeight: "600",
    color: colors.textPrimary
  }
});
