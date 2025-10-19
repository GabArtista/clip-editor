import { Ionicons } from "@expo/vector-icons";
import {
  createBottomTabNavigator,
  BottomTabNavigationOptions
} from "@react-navigation/bottom-tabs";
import {
  createNativeStackNavigator,
  NativeStackNavigationOptions
} from "@react-navigation/native-stack";
import { Text } from "react-native";

import { colors, typography } from "@theme/colors";
import { HomeScreen } from "@screens/HomeScreen";
import { MusicLibraryScreen } from "@screens/MusicLibraryScreen";
import { EditsScreen } from "@screens/EditsScreen";
import { SettingsScreen } from "@screens/SettingsScreen";
import { UploadMusicScreen } from "@screens/UploadMusicScreen";
import { TranscriptEditorScreen } from "@screens/TranscriptEditorScreen";
import { NewReelScreen } from "@screens/NewReelScreen";
import { JobDetailScreen } from "@screens/JobDetailScreen";

import { RootStackParamList, TabsParamList } from "./types";

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tabs = createBottomTabNavigator<TabsParamList>();

const headerOptions: NativeStackNavigationOptions = {
  headerTransparent: true,
  headerTitle: "",
  headerTintColor: colors.textPrimary
};

const tabOptions: BottomTabNavigationOptions = {
  headerShown: false,
  tabBarActiveTintColor: colors.textPrimary,
  tabBarInactiveTintColor: colors.textMuted,
  tabBarShowLabel: true,
  tabBarLabelStyle: {
    fontSize: typography.caption,
    fontWeight: "600"
  },
  tabBarStyle: {
    backgroundColor: colors.surface,
    borderTopColor: colors.border,
    paddingVertical: 8,
    height: 72
  }
};

function MainTabs() {
  return (
    <Tabs.Navigator screenOptions={tabOptions}>
      <Tabs.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home-outline" size={size} color={color} />
          ),
          tabBarLabel: "Início"
        }}
      />
      <Tabs.Screen
        name="Music"
        component={MusicLibraryScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="musical-notes-outline" size={size} color={color} />
          ),
          tabBarLabel: "Músicas"
        }}
      />
      <Tabs.Screen
        name="Edits"
        component={EditsScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="sparkles-outline" size={size} color={color} />
          ),
          tabBarLabel: "Edições"
        }}
      />
      <Tabs.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings-outline" size={size} color={color} />
          ),
          tabBarLabel: "Configurações"
        }}
      />
    </Tabs.Navigator>
  );
}

export function AppNavigator() {
  return (
    <Stack.Navigator screenOptions={headerOptions}>
      <Stack.Screen name="MainTabs" component={MainTabs} />
      <Stack.Screen
        name="UploadMusic"
        component={UploadMusicScreen}
        options={{
          headerShown: true,
          headerTitle: () => <Text style={{ fontSize: 20, fontWeight: "600" }}>Enviar música</Text>
        }}
      />
      <Stack.Screen
        name="TranscriptEditor"
        component={TranscriptEditorScreen}
        options={{
          headerShown: true,
          headerTitle: () => (
            <Text style={{ fontSize: 20, fontWeight: "600" }}>Transcrição</Text>
          )
        }}
      />
      <Stack.Screen
        name="NewReel"
        component={NewReelScreen}
        options={{
          headerShown: true,
          headerTitle: () => (
            <Text style={{ fontSize: 20, fontWeight: "600" }}>Editar Reels</Text>
          )
        }}
      />
      <Stack.Screen
        name="JobDetail"
        component={JobDetailScreen}
        options={{
          headerShown: true,
          headerTitle: () => (
            <Text style={{ fontSize: 20, fontWeight: "600" }}>Resultado</Text>
          )
        }}
      />
    </Stack.Navigator>
  );
}
