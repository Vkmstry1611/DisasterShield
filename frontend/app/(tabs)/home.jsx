import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { useRouter, Stack, useFocusEffect } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

import Colors from '../../constants/colors';
import { disasterAPI } from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner';

const actionCards = [
  {
    id: '1',
    title: 'Verified News',
    description: 'Trusted disaster updates',
    color: Colors.verified,
    route: '/news?tab=verified',
  },
  {
    id: '2',
    title: 'Rumor News',
    description: 'AI-detected misinformation',
    color: Colors.rumor,
    route: '/news?tab=rumor',
  },
  {
    id: '3',
    title: 'Emergency Resources',
    description: 'Quick access to help',
    color: Colors.error,
    route: '/resources',
  },
];

export default function HomeScreen() {
  const router = useRouter();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    loadDashboardStats();
    checkLoginStatus();
  }, []);

  // Check login status when screen comes into focus
  useFocusEffect(
    React.useCallback(() => {
      checkLoginStatus();
    }, [])
  );

  const checkLoginStatus = async () => {
    try {
      const userInfo = await AsyncStorage.getItem('user_info');
      if (userInfo) {
        setUser(JSON.parse(userInfo));
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Error checking login status:', error);
      setUser(null);
    }
  };

  const loadDashboardStats = async () => {
    try {
      console.log('📊 Loading dashboard stats from database...');
      const response = await disasterAPI.getDashboardStats();
      setStats(response.data);
      console.log('✅ Dashboard stats loaded from database');
    } catch (error) {
      console.error('❌ Error loading dashboard stats:', error.message);
      // Set default stats if network fails
      setStats({
        stats: {
          verified: { count: 0, avg_confidence: 0 },
          rumor: { count: 0, avg_confidence: 0 }
        },
        last_updated: new Date().toISOString()
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardStats();
    setRefreshing(false);
  };

  const handleCardPress = (route) => {
    console.log('Navigating to:', route);
    router.push(route);
  };

  return (
    <View style={styles.container}>
      <Stack.Screen 
        options={{ 
          headerShown: true,
          title: 'DisasterShield',
          headerStyle: {
            backgroundColor: Colors.white,
          },
          headerTintColor: Colors.text,
          headerShadowVisible: false,
        }} 
      />
      
      {loading ? (
        <LoadingSpinner message="Loading dashboard..." />
      ) : (
        <ScrollView 
          contentContainerStyle={styles.scrollContent} 
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              colors={[Colors.primary]}
              tintColor={Colors.primary}
            />
          }
        >
          <View style={styles.header}>
            <View style={styles.logoContainer}>
              <View style={styles.logoShield}>
                <Text style={styles.logoText}>DS</Text>
              </View>
            </View>
            <Text style={styles.title}>
              Welcome{user ? `, ${user.full_name || user.username}` : ' to DisasterShield'}
            </Text>
            <Text style={styles.subtitle}>Your Trusted Source in Emergencies</Text>
            
            {user && (
              <View style={styles.loginStatus}>
                <Text style={styles.loginStatusText}>✅ Logged in as {user.username}</Text>
              </View>
            )}
            
            {!stats?.stats && !loading && (
              <View style={styles.networkStatus}>
                <Text style={styles.networkStatusText}>⚠️ Connecting to database...</Text>
                <Text style={styles.networkStatusSubtext}>Make sure backend server is running</Text>
              </View>
            )}
          </View>

          {stats && (
            <View style={styles.statsContainer}>
              <Text style={styles.statsTitle}>Today's Activity</Text>
              <View style={styles.statsGrid}>
                <View style={styles.statCard}>
                  <Text style={styles.statNumber}>
                    {stats.stats.verified?.count || 0}
                  </Text>
                  <Text style={styles.statLabel}>Verified News</Text>
                  <Text style={styles.statConfidence}>
                    {stats.stats.verified ? `${Math.round(stats.stats.verified.avg_confidence * 100)}% avg` : 'N/A'}
                  </Text>
                </View>
                <View style={styles.statCard}>
                  <Text style={styles.statNumber}>
                    {stats.stats.rumor?.count || 0}
                  </Text>
                  <Text style={styles.statLabel}>Rumors Detected</Text>
                  <Text style={styles.statConfidence}>
                    {stats.stats.rumor ? `${Math.round(stats.stats.rumor.avg_confidence * 100)}% avg` : 'N/A'}
                  </Text>
                </View>
              </View>
              <Text style={styles.lastUpdated}>
                Last updated: {new Date(stats.last_updated).toLocaleTimeString()}
              </Text>
            </View>
          )}

          <View style={styles.cardsContainer}>
            {actionCards.map((card) => {
              return (
                <TouchableOpacity
                  key={card.id}
                  style={styles.card}
                  onPress={() => handleCardPress(card.route)}
                  activeOpacity={0.8}
                >
                  <View style={[styles.iconContainer, { backgroundColor: card.color + '15' }]}>
                    <Text style={[styles.iconText, { color: card.color }]}>📰</Text>
                  </View>
                  <Text style={styles.cardTitle}>{card.title}</Text>
                  <Text style={styles.cardDescription}>{card.description}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <View style={styles.infoSection}>
            <View style={styles.infoBadge}>
              <Text style={styles.infoBadgeIcon}>🛡️</Text>
              <Text style={styles.infoBadgeText}>AI-Powered Protection</Text>
            </View>
            <Text style={styles.infoText}>
              DisasterShield uses advanced AI to verify news sources and detect misinformation,
              helping you stay safe and informed during emergencies.
            </Text>
          </View>
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  header: {
    alignItems: 'center',
    paddingTop: 32,
    paddingBottom: 40,
  },
  logoContainer: {
    marginBottom: 16,
  },
  logoShield: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    ...Colors.shadowMd,
  },
  logoText: {
    fontSize: 32,
    fontWeight: '700',
    color: Colors.white,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  cardsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 32,
  },
  card: {
    width: '48%',
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    alignItems: 'center',
    ...Colors.shadow,
  },
  iconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 6,
  },
  cardDescription: {
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
  infoSection: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 20,
    ...Colors.shadow,
  },
  iconText: {
    fontSize: 24,
    fontWeight: '600',
  },
  infoBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: Colors.primary + '15',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    marginBottom: 12,
    gap: 6,
  },
  infoBadgeIcon: {
    fontSize: 16,
  },
  infoBadgeText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.primary,
  },
  infoText: {
    fontSize: 14,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  statsContainer: {
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    ...Colors.shadow,
  },
  statsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 12,
    backgroundColor: Colors.background,
    borderRadius: 12,
    marginHorizontal: 4,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.primary,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 2,
  },
  statConfidence: {
    fontSize: 10,
    color: Colors.textLight,
    textAlign: 'center',
  },
  lastUpdated: {
    fontSize: 11,
    color: Colors.textLight,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  loginStatus: {
    backgroundColor: Colors.verified + '15',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    marginTop: 12,
  },
  loginStatusText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.verified,
    textAlign: 'center',
  },
  networkStatus: {
    backgroundColor: Colors.rumor + '15',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    marginTop: 12,
  },
  networkStatus: {
    backgroundColor: Colors.rumor + '15',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    marginTop: 12,
  },
  networkStatusText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.rumor,
    textAlign: 'center',
  },
  networkStatusSubtext: {
    fontSize: 10,
    color: Colors.rumor,
    textAlign: 'center',
    marginTop: 2,
  },
});