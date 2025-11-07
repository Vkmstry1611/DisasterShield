import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Colors from '../constants/colors';

const NewsCard = ({ tweet, onPress }) => {
  const isVerified = tweet.label === 'verified';
  const confidenceColor = getConfidenceColor(tweet.confidence);
  const confidencePercentage = Math.round(tweet.confidence * 100);

  return (
    <TouchableOpacity style={styles.card} onPress={() => onPress?.(tweet)}>
      <View style={styles.header}>
        <Text style={styles.author}>{tweet.author}</Text>
        <View style={[styles.badge, { backgroundColor: isVerified ? Colors.success : Colors.warning }]}>
          <Text style={styles.badgeText}>
            {isVerified ? 'VERIFIED' : 'RUMOR'}
          </Text>
        </View>
      </View>
      
      <Text style={styles.text} numberOfLines={0}>{tweet.text}</Text>
      
      <View style={styles.footer}>
        <View style={styles.engagement}>
          <Text style={styles.engagementText}>
            ⬆️ {formatNumber(tweet.like_count)} upvotes
          </Text>
        </View>
        
        <View style={[styles.confidenceBadge, { backgroundColor: confidenceColor }]}>
          <Text style={styles.confidenceText}>{confidencePercentage}%</Text>
        </View>
      </View>
      
      <Text style={styles.timestamp}>
        {formatTimestamp(tweet.created_at)}
      </Text>
    </TouchableOpacity>
  );
};

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return Colors.success;
  if (confidence >= 0.6) return Colors.warning;
  return Colors.error;
};

const formatNumber = (num) => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: 12,
    padding: 16,
    marginVertical: 6,
    marginHorizontal: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  author: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.primary,
    flex: 1,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.white,
  },
  text: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textDark,
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  engagement: {
    flex: 1,
  },
  engagementText: {
    fontSize: 12,
    color: Colors.textLight,
  },
  confidenceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.white,
  },
  timestamp: {
    fontSize: 11,
    color: Colors.textLight,
    textAlign: 'right',
  },
});

export default NewsCard;
