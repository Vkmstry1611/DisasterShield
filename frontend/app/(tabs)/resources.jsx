import React from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, Platform, Linking, Alert } from 'react-native';
import { Stack } from 'expo-router';

import Colors from '../../constants/colors';

const emergencyContacts = [
  {
    id: '1',
    name: 'Police',
    description: 'Law enforcement emergency',
    number: '911',
    icon: '🚔',
    color: Colors.primary,
  },
  {
    id: '2',
    name: 'Ambulance',
    description: 'Medical emergency',
    number: '911',
    icon: '🚑',
    color: Colors.success,
  },
  {
    id: '3',
    name: 'Fire Department',
    description: 'Fire and rescue services',
    number: '911',
    icon: '🚒',
    color: Colors.rumor,
  },
  {
    id: '4',
    name: 'Disaster Control',
    description: 'Disaster management center',
    number: '1-800-DISASTER',
    icon: '📞',
    color: Colors.warning,
  },
];

export default function ResourcesScreen() {
  const handleCall = (name, number) => {
    Alert.alert(
      `Call ${name}`,
      `Are you sure you want to call ${number}?`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Call',
          onPress: () => {
            const phoneUrl = `tel:${number}`;
            Linking.openURL(phoneUrl).catch((err) => {
              console.error('Failed to open phone app:', err);
              Alert.alert('Error', 'Unable to make phone call');
            });
          },
          style: 'default',
        },
      ],
    );
  };

  return (
    <View style={styles.container}>
      <Stack.Screen 
        options={{ 
          headerShown: true,
          title: 'Emergency Resources',
          headerStyle: {
            backgroundColor: Colors.white,
          },
          headerTintColor: Colors.text,
          headerShadowVisible: false,
        }} 
      />

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Emergency Contacts</Text>
          <Text style={styles.headerSubtitle}>Quick access to emergency services</Text>
        </View>

        <View style={styles.warningBanner}>
          <Text style={{ fontSize: 20, color: Colors.warning }}>⚠️</Text>
          <Text style={styles.warningText}>
            If you are in immediate danger, contact your local emergency services
          </Text>
        </View>

        <View style={styles.contactsList}>
          {emergencyContacts.map((contact) => (
            <View key={contact.id} style={styles.contactCard}>
              <View style={styles.contactInfo}>
                <View style={[styles.iconCircle, { backgroundColor: contact.color + '15' }]}>
                  <Text style={{ fontSize: 28, color: contact.color }}>{contact.icon}</Text>
                </View>
                <View style={styles.contactText}>
                  <Text style={styles.contactName}>{contact.name}</Text>
                  <Text style={styles.contactDescription}>{contact.description}</Text>
                  <Text style={styles.contactNumber}>{contact.number}</Text>
                </View>
              </View>
              <TouchableOpacity
                style={[styles.callButton, { backgroundColor: contact.color }]}
                onPress={() => handleCall(contact.name, contact.number)}
                activeOpacity={0.8}
              >
                <Text style={{ fontSize: 18, color: Colors.white }}>📞</Text>
                <Text style={styles.callButtonText}>Call Now</Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>

        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>Safety Tips</Text>
          <View style={styles.tipsList}>
            <View style={styles.tipItem}>
              <Text style={styles.tipBullet}>•</Text>
              <Text style={styles.tipText}>Keep emergency contacts saved in your phone</Text>
            </View>
            <View style={styles.tipItem}>
              <Text style={styles.tipBullet}>•</Text>
              <Text style={styles.tipText}>Know your evacuation routes and assembly points</Text>
            </View>
            <View style={styles.tipItem}>
              <Text style={styles.tipBullet}>•</Text>
              <Text style={styles.tipText}>Prepare an emergency kit with essential supplies</Text>
            </View>
            <View style={styles.tipItem}>
              <Text style={styles.tipBullet}>•</Text>
              <Text style={styles.tipText}>Stay informed through verified news sources</Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    flex: 1,
  },
  header: {
    padding: 20,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.warning + '15',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    gap: 12,
  },
  warningText: {
    flex: 1,
    fontSize: 13,
    color: Colors.warning,
    fontWeight: '500',
    lineHeight: 18,
  },
  contactsList: {
    paddingHorizontal: 16,
    gap: 12,
  },
  contactCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 16,
    ...Colors.shadow,
  },
  contactInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  iconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  contactText: {
    flex: 1,
  },
  contactName: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
  },
  contactDescription: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginBottom: 4,
  },
  contactNumber: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.primary,
  },
  callButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  callButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.white,
  },
  infoSection: {
    margin: 16,
    marginTop: 24,
    padding: 20,
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    ...Colors.shadow,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 16,
  },
  tipsList: {
    gap: 12,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  tipBullet: {
    fontSize: 16,
    color: Colors.primary,
    fontWeight: '700',
  },
  tipText: {
    flex: 1,
    fontSize: 14,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
});