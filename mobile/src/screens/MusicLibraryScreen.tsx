import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import {
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";

import { Card } from "@components/Card";
import { StatusChip } from "@components/StatusChip";
import { colors, spacing, typography } from "@theme/colors";
import { RootStackParamList } from "@navigation/types";

const musicItems = [
  {
    id: "music-1",
    title: "Doze Intro",
    duration: "03:12",
    status: "Pronta",
    tone: "success" as const
  },
  {
    id: "music-2",
    title: "Gratidão",
    duration: "04:08",
    status: "Processando",
    tone: "warning" as const
  },
  {
    id: "music-3",
    title: "Noites Urbanas",
    duration: "02:56",
    status: "Pronta",
    tone: "success" as const
  }
];

type Navigation = NativeStackNavigationProp<RootStackParamList>;

export function MusicLibraryScreen() {
  const navigation = useNavigation<Navigation>();

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Biblioteca de músicas</Text>
        <Pressable
          style={styles.uploadButton}
          onPress={() => navigation.navigate("UploadMusic")}
        >
          <Ionicons name="add" size={22} color={colors.textPrimary} />
          <Text style={styles.uploadLabel}>Adicionar</Text>
        </Pressable>
      </View>

      <View style={styles.search}>
        <Ionicons name="search" size={18} color={colors.textMuted} />
        <TextInput
          placeholder="Buscar por título ou humor"
          placeholderTextColor={colors.textMuted}
          style={styles.searchInput}
          accessibilityLabel="Buscar músicas"
        />
      </View>

      <FlatList
        data={musicItems}
        contentContainerStyle={styles.listContent}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Card rounded={20} padding={spacing.md}>
            <Pressable
              onPress={() => navigation.navigate("TranscriptEditor", { musicId: item.id })}
              style={styles.itemRow}
            >
              <View style={styles.thumb}>
                <Ionicons name="musical-note" size={28} color={colors.textPrimary} />
              </View>
              <View style={styles.itemContent}>
                <Text style={styles.itemTitle}>{item.title}</Text>
                <Text style={styles.itemSubtitle}>{item.duration}</Text>
                <StatusChip label={item.status} tone={item.tone} />
              </View>
              <View style={styles.chevron}>
                <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
              </View>
            </Pressable>
          </Card>
        )}
        ItemSeparatorComponent={() => <View style={{ height: spacing.md }} />}
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
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.lg
  },
  title: {
    fontSize: typography.headingM,
    fontWeight: "700",
    color: colors.textPrimary
  },
  uploadButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: 16,
    backgroundColor: colors.goldPrimary
  },
  uploadLabel: {
    fontWeight: "600",
    color: colors.textPrimary
  },
  search: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: 16,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.lg
  },
  searchInput: {
    flex: 1,
    fontSize: typography.body,
    color: colors.textPrimary
  },
  listContent: {
    paddingBottom: spacing.xxl
  },
  itemRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md
  },
  thumb: {
    width: 56,
    height: 56,
    borderRadius: 18,
    backgroundColor: colors.goldHighlight,
    alignItems: "center",
    justifyContent: "center"
  },
  itemContent: {
    flex: 1,
    gap: spacing.xs / 1.5
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
  chevron: {
    padding: spacing.sm
  }
});
