import React, { useState, useEffect, useMemo } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, RefreshControl, Alert } from 'react-native';
import { Stack, useLocalSearchParams } from 'expo-router';

import Colors from '../../constants/colors';
import { disasterAPI } from '../../services/api';
import TweetCard from '../../components/TweetCard';
import LoadingSpinner from '../../components/LoadingSpinner';

export default function NewsScreen() {
  const params = useLocalSearchParams();
  const initialTab = params.tab || 'verified';
  
  const [activeTab, setActiveTab] = useState(initialTab);
  const [verifiedNews, setVerifiedNews] = useState([]);
  const [rumorNews, setRumorNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [minConfidence, setMinConfidence] = useState(0.6);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [categories, setCategories] = useState(['all']);

  const currentNews = useMemo(() => {
    return activeTab === 'verified' ? verifiedNews : rumorNews;
  }, [activeTab, verifiedNews, rumorNews]);

  useEffect(() => {
    loadCategories();
    loadNews();
  }, []);

  useEffect(() => {
    loadNews();
  }, [selectedCategory]);

  const loadCategories = async () => {
    try {
      const response = await disasterAPI.getCategories();
      setCategories(response.data.categories || ['all']);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadNews = async () => {
    try {
      setLoading(true);
      
      const [verifiedResponse, rumorResponse] = await Promise.all([
        disasterAPI.getVerifiedNews(50, minConfidence, selectedCategory),
        disasterAPI.getRumors(50, 0.5, selectedCategory)
      ]);
      
      setVerifiedNews(verifiedResponse.data);
      setRumorNews(rumorResponse.data);
      
    } catch (error) {
      console.error('Error loading news:', error);
      Alert.alert(
        'Error', 
        'Failed to load news. Please check your connection and try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await loadNews();
    } catch (error) {
      console.error('Error refreshing:', error);
      Alert.alert('Error', 'Failed to refresh data');
    } finally {
      setRefreshing(false);
    }
  };

  const handleManualUpdate = async () => {
    try {
      Alert.alert(
        'Manual Update',
        'This will fetch fresh data from Reddit. It may take a few moments.',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Update',
            onPress: async () => {
              try {
                setRefreshing(true);
                await disasterAPI.forceUpdate();
                await loadNews();
                Alert.alert('Success', 'Data updated successfully!');
              } catch (error) {
                Alert.alert('Error', 'Failed to update data');
              } finally {
                setRefreshing(false);
              }
            }
          }
        ]
      );
    } catch (error) {
      console.error('Error in manual update:', error);
    }
  };

  const handleTabChange = (tab) => {
    console.log('Switching to tab:', tab);
    setActiveTab(tab);
  };

  const handleTweetPress = (tweet) => {
    Alert.alert(
      'Tweet Details',
      `Author: ${tweet.author}\nConfidence: ${Math.round(tweet.confidence * 100)}%\nLikes: ${tweet.like_count}\nRetweets: ${tweet.retweet_count}`,
      [{ text: 'OK' }]
    );
  };

  return (
    <View style={styles.container}>
      <Stack.Screen 
        options={{ 
          headerShown: true,
          title: 'News Feed',
          headerStyle: {
            backgroundColor: Colors.white,
          },
          headerTintColor: Colors.text,
          headerShadowVisible: false,
        }} 
      />

      <View style={styles.controlsContainer}>
        <View style={styles.tabsContainer}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'verified' && styles.tabActive]}
            onPress={() => handleTabChange('verified')}
            activeOpacity={0.7}
          >
            <Text style={{ fontSize: 18, color: activeTab === 'verified' ? Colors.white : Colors.verified }}>🛡️</Text>
            <Text style={[styles.tabText, activeTab === 'verified' && styles.tabTextActive]}>
              Verified
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tab, activeTab === 'rumor' && styles.tabActive]}
            onPress={() => handleTabChange('rumor')}
            activeOpacity={0.7}
          >
            <Text style={{ fontSize: 18, color: activeTab === 'rumor' ? Colors.white : Colors.rumor }}>⚠️</Text>
            <Text style={[styles.tabText, activeTab === 'rumor' && styles.tabTextActive]}>
              Rumor Tracker
            </Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity style={styles.refreshButton} onPress={handleManualUpdate}>
          <Text style={styles.refreshButtonText}>🔄 Update</Text>
        </TouchableOpacity>
      </View>
      
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false} 
        style={styles.categoryContainer}
        contentContainerStyle={styles.categoryContentContainer}
      >
        {categories.map((category) => (
          <TouchableOpacity
            key={category}
            style={[
              styles.categoryButton,
              selectedCategory === category && styles.activeCategoryButton
            ]}
            onPress={() => setSelectedCategory(category)}
          >
            <Text style={[
              styles.categoryButtonText,
              selectedCategory === category && styles.activeCategoryButtonText
            ]}>
              {category === 'all' ? 'All' : category.charAt(0).toUpperCase() + category.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {loading ? (
        <LoadingSpinner message="Loading disaster news..." />
      ) : (
        <ScrollView 
          style={styles.newsList} 
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
          {currentNews.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>
                {activeTab === 'verified' ? '🛡️' : '⚠️'}
              </Text>
              <Text style={styles.emptyStateTitle}>
                No {activeTab === 'verified' ? 'verified news' : 'rumors'} found
              </Text>
              <Text style={styles.emptyStateSubtitle}>
                Pull down to refresh or check back later
              </Text>
            </View>
          ) : (
            currentNews.map((tweet) => (
              <TweetCard
                key={tweet.id}
                tweet={tweet}
                onPress={handleTweetPress}
              />
            ))
          )}
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
  controlsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  tabsContainer: {
    flexDirection: 'row',
    gap: 12,
    flex: 1,
  },
  refreshButton: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    marginLeft: 12,
  },
  refreshButtonText: {
    color: Colors.white,
    fontSize: 12,
    fontWeight: '600',
  },
  categoryContainer: {
    maxHeight: 50,
    paddingHorizontal: 16,
    paddingVertical: 6,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  categoryContentContainer: {
    alignItems: 'center',
    paddingVertical: 2,
  },
  categoryButton: {
    backgroundColor: Colors.background,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 14,
    marginRight: 8,
    borderWidth: 1,
    borderColor: Colors.border,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  activeCategoryButton: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  categoryButtonText: {
    fontSize: 11,
    fontWeight: '500',
    color: Colors.text,
    textAlign: 'center',
  },
  activeCategoryButtonText: {
    color: Colors.white,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: Colors.background,
    gap: 8,
  },
  tabActive: {
    backgroundColor: Colors.primary,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  tabTextActive: {
    color: Colors.white,
  },
  newsList: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 40,
  },
  emptyStateText: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyStateTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 8,
  },
  emptyStateSubtitle: {
    fontSize: 14,
    color: Colors.textLight,
    textAlign: 'center',
    lineHeight: 20,
  },
});