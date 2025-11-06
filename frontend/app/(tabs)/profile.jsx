import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, Platform, Alert } from 'react-native';
import { Stack, router, useFocusEffect } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

import Colors from '../../constants/colors';
import { disasterAPI } from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner';

export default function ProfileScreen() {
  const [isGuest, setIsGuest] = useState(true);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Refresh auth status when screen comes into focus
  useFocusEffect(
    React.useCallback(() => {
      console.log('📱 Profile screen focused, checking auth...');
      checkAuthStatus();
    }, [])
  );

  const checkAuthStatus = async () => {
    try {
      console.log('🔍 Checking auth status...');
      const token = await AsyncStorage.getItem('access_token');
      const userInfo = await AsyncStorage.getItem('user_info');
      
      console.log('📱 Token exists:', !!token);
      console.log('📱 User info exists:', !!userInfo);
      
      if (token && userInfo) {
        const user = JSON.parse(userInfo);
        console.log('👤 User found:', user.username);
        setUser(user);
        setIsGuest(false);
      } else {
        console.log('🚫 No auth data found');
      }
    } catch (error) {
      console.error('Auth check error:', error);
      await AsyncStorage.removeItem('access_token');
      await AsyncStorage.removeItem('user_info');
    } finally {
      setLoading(false);
    }
  };

  const handlePress = (action) => {
    switch (action) {
      case 'login':
        router.push('/login');
        break;
      case 'signup':
        router.push('/signup');
        break;
      case 'logout':
        handleLogout();
        break;
      default:
        console.log(`Action: ${action}`);
    }
  };

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            try {
              console.log('🚪 Starting logout process...');
              
              // Clear local storage first (most important)
              await AsyncStorage.removeItem('access_token');
              await AsyncStorage.removeItem('user_info');
              console.log('🗑️ Cleared local storage');
              
              // Update UI state
              setUser(null);
              setIsGuest(true);
              console.log('🔄 Updated UI state');
              
              // Try to call logout API (optional, don't fail if it doesn't work)
              try {
                await disasterAPI.logout();
                console.log('📡 API logout successful');
              } catch (apiError) {
                console.log('⚠️ API logout failed (but local logout succeeded):', apiError.message);
              }
              
              Alert.alert('Success', 'Logged out successfully');
              console.log('✅ Logout complete');
              
            } catch (error) {
              console.error('💥 Logout error:', error);
              // Even if there's an error, try to clear storage and update UI
              try {
                await AsyncStorage.removeItem('access_token');
                await AsyncStorage.removeItem('user_info');
                setUser(null);
                setIsGuest(true);
                Alert.alert('Success', 'Logged out successfully');
              } catch (fallbackError) {
                console.error('💥 Fallback logout failed:', fallbackError);
                Alert.alert('Error', 'Logout failed. Please try again.');
              }
            }
          }
        }
      ]
    );
  };

  if (loading) {
    return <LoadingSpinner message="Loading profile..." />;
  }

  return (
    <View style={styles.container}>
      <Stack.Screen 
        options={{ 
          headerShown: true,
          title: 'Profile',
          headerStyle: {
            backgroundColor: Colors.white,
          },
          headerTintColor: Colors.text,
          headerShadowVisible: false,
        }} 
      />

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.profileHeader}>
          <View style={styles.avatarContainer}>
            <Text style={{ fontSize: 80, color: Colors.primary }}>👤</Text>
          </View>
          
          {isGuest ? (
            <View style={styles.guestInfo}>
              <Text style={styles.guestTitle}>Browsing as Guest</Text>
              <Text style={styles.guestSubtitle}>Sign in to access all features</Text>
              
              <View style={styles.authButtons}>
                <TouchableOpacity
                  style={styles.loginButton}
                  onPress={() => handlePress('login')}
                  activeOpacity={0.8}
                >
                  <Text style={{ fontSize: 18, color: Colors.white }}>🔑</Text>
                  <Text style={styles.loginButtonText}>Login</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.signupButton}
                  onPress={() => handlePress('signup')}
                  activeOpacity={0.8}
                >
                  <Text style={styles.signupButtonText}>Sign Up</Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <View style={styles.userInfo}>
              <Text style={styles.userName}>{user?.full_name || user?.username}</Text>
              <View style={styles.emailContainer}>
                <Text style={{ fontSize: 14, color: Colors.textSecondary }}>📧</Text>
                <Text style={styles.userEmail}>{user?.email}</Text>
              </View>
              <Text style={styles.joinDate}>
                Joined {new Date(user?.created_at).toLocaleDateString()}
              </Text>
              
              <View style={styles.buttonContainer}>
                <TouchableOpacity
                  style={styles.logoutButton}
                  onPress={() => handlePress('logout')}
                  activeOpacity={0.8}
                >
                  <Text style={{ fontSize: 16, color: Colors.white }}>🚪</Text>
                  <Text style={styles.logoutButtonText}>Logout</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.forceLogoutButton}
                  onPress={async () => {
                    console.log('🔧 Force logout triggered');
                    await AsyncStorage.clear();
                    setUser(null);
                    setIsGuest(true);
                    Alert.alert('Success', 'Force logout complete');
                  }}
                  activeOpacity={0.8}
                >
                  <Text style={styles.forceLogoutButtonText}>Force Logout</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>

        <View style={styles.menuSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Settings</Text>
            <TouchableOpacity
              style={styles.refreshButton}
              onPress={() => {
                console.log('🔄 Manual refresh triggered');
                setLoading(true);
                checkAuthStatus();
              }}
              activeOpacity={0.7}
            >
              <Text style={styles.refreshButtonText}>🔄 Refresh</Text>
            </TouchableOpacity>
          </View>
          
          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => handlePress('notifications')}
            activeOpacity={0.7}
          >
            <View style={styles.menuItemLeft}>
              <View style={[styles.menuIcon, { backgroundColor: Colors.primary + '15' }]}>
                <Text style={{ fontSize: 20, color: Colors.primary }}>🔔</Text>
              </View>
              <Text style={styles.menuItemText}>Notifications</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => handlePress('settings')}
            activeOpacity={0.7}
          >
            <View style={styles.menuItemLeft}>
              <View style={[styles.menuIcon, { backgroundColor: Colors.secondary + '15' }]}>
                <Text style={{ fontSize: 20, color: Colors.secondary }}>⚙️</Text>
              </View>
              <Text style={styles.menuItemText}>App Settings</Text>
            </View>
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>DisasterShield v1.0.0</Text>
          <Text style={styles.footerSubtext}>Keeping you safe and informed</Text>
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
  profileHeader: {
    backgroundColor: Colors.white,
    alignItems: 'center',
    paddingVertical: 32,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  avatarContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: Colors.primary + '10',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    ...Colors.shadow,
  },
  guestInfo: {
    alignItems: 'center',
    width: '100%',
  },
  guestTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
  },
  guestSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 20,
  },
  authButtons: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  loginButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  loginButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.white,
  },
  signupButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.background,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: Colors.primary,
  },
  signupButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.primary,
  },
  userInfo: {
    alignItems: 'center',
  },
  userName: {
    fontSize: 22,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  emailContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  userEmail: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  joinDate: {
    fontSize: 12,
    color: Colors.textLight,
    marginBottom: 16,
  },
  buttonContainer: {
    width: '100%',
    gap: 8,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.rumor,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 12,
    gap: 8,
  },
  logoutButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.white,
  },
  forceLogoutButton: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.textLight,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  forceLogoutButtonText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.white,
  },
  menuSection: {
    marginTop: 24,
    paddingHorizontal: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  refreshButton: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  refreshButtonText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.white,
  },
  menuItem: {
    backgroundColor: Colors.cardBg,
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    ...Colors.shadow,
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  menuIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuItemText: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.text,
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  footerText: {
    fontSize: 13,
    color: Colors.textLight,
    marginBottom: 4,
  },
  footerSubtext: {
    fontSize: 12,
    color: Colors.textLight,
  },
});