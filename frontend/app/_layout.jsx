import { Stack } from "expo-router";
import React from "react";
import { View } from "react-native";

function RootLayoutNav() {
    return (
        <Stack screenOptions={{ headerBackTitle: "Back" }}>
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        </Stack>
    );
}

export default function RootLayout() {
    return (
        <View style={{ flex: 1 }}>
            <RootLayoutNav />
        </View>
    );
}