import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { StatusBar } from "expo-status-bar";
import { useColorScheme } from "react-native";

import { AppNavigator } from "@navigation/AppNavigator";
import { colors } from "@theme/colors";

const LightTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: colors.background,
    card: colors.surface,
    primary: colors.goldPrimary,
    text: colors.textPrimary,
    border: colors.border,
    notification: colors.accentCoral
  }
};

export default function App() {
  const scheme = useColorScheme();

  return (
    <>
      <NavigationContainer theme={LightTheme}>
        <AppNavigator />
      </NavigationContainer>
      <StatusBar style={scheme === "dark" ? "light" : "dark"} />
    </>
  );
}
