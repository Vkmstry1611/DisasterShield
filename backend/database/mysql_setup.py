import mysql.connector
from mysql.connector import pooling, Error
import logging
from typing import Optional, List, Dict
import os
from datetime import datetime

class MySQLDatabase:
    def __init__(self):
        self.config = {
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', 'root'),
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'database': os.getenv('MYSQL_DATABASE', 'disaster_shield_db'),
            'pool_name': 'disaster_pool',
            'pool_size': 5,
            'autocommit': True
        }
        self.connection_pool = None
        self.init_connection_pool()
        self.create_tables()

    def init_connection_pool(self):
        """Initialize MySQL connection pool"""
        try:
            self.connection_pool = pooling.MySQLConnectionPool(**self.config)
            logging.info("MySQL connection pool created successfully")
        except Error as e:
            logging.error(f"Error creating connection pool: {e}")
            raise

    def get_connection(self):
        """Get connection from pool"""
        try:
            return self.connection_pool.get_connection()
        except Error as e:
            logging.error(f"Error getting connection: {e}")
            raise

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        create_tweets_table = """
        CREATE TABLE IF NOT EXISTS tweets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tweet_id VARCHAR(50) UNIQUE NOT NULL,
            text TEXT NOT NULL,
            username VARCHAR(100),
            user_followers INT DEFAULT 0,
            tweet_timestamp DATETIME,
            classification_label ENUM('verified', 'rumor') NOT NULL,
            confidence_score DECIMAL(5,4) NOT NULL,
            model_version VARCHAR(20) DEFAULT 'v2.0',
            likes INT DEFAULT 0,
            retweets INT DEFAULT 0,
            replies INT DEFAULT 0,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            
            INDEX idx_classification (classification_label, confidence_score),
            INDEX idx_timestamp (tweet_timestamp DESC),
            INDEX idx_confidence (confidence_score DESC)
        )
        """
        
        create_classification_details = """
        CREATE TABLE IF NOT EXISTS classification_details (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tweet_id VARCHAR(50),
            distilbert_verified DECIMAL(5,4),
            distilbert_rumor DECIMAL(5,4),
            svm_verified DECIMAL(5,4),
            zero_shot_verified DECIMAL(5,4),
            final_confidence DECIMAL(5,4),
            processing_time_ms INT,
            
            FOREIGN KEY (tweet_id) REFERENCES tweets(tweet_id) ON DELETE CASCADE
        )
        """
        
        create_api_logs = """
        CREATE TABLE IF NOT EXISTS api_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            endpoint VARCHAR(100),
            request_count INT DEFAULT 1,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            last_login TIMESTAMP NULL,
            
            INDEX idx_username (username),
            INDEX idx_email (email)
        )
        """

        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute(create_tweets_table)
            cursor.execute(create_classification_details)
            cursor.execute(create_api_logs)
            cursor.execute(create_users_table)
            
            logging.info("Database tables created successfully")
            
        except Error as e:
            logging.error(f"Error creating tables: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def insert_tweet(self, tweet_data: Dict) -> bool:
        """Insert classified tweet into database"""
        insert_query = """
        INSERT INTO tweets (tweet_id, text, username, user_followers, tweet_timestamp,
                           classification_label, confidence_score, category, model_version,
                           likes, retweets, replies)
        VALUES (%(tweet_id)s, %(text)s, %(username)s, %(user_followers)s, %(tweet_timestamp)s,
                %(classification_label)s, %(confidence_score)s, %(category)s, %(model_version)s,
                %(likes)s, %(retweets)s, %(replies)s)
        ON DUPLICATE KEY UPDATE
        classification_label = VALUES(classification_label),
        confidence_score = VALUES(confidence_score),
        category = VALUES(category),
        processed_at = CURRENT_TIMESTAMP
        """
        
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(insert_query, tweet_data)
            return True
            
        except Error as e:
            logging.error(f"Error inserting tweet: {e}")
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def get_verified_tweets(self, limit: int = 50, min_confidence: float = 0.6, category: str = None) -> List[Dict]:
        """Get verified tweets from database"""
        if category and category != 'all':
            query = """
            SELECT tweet_id, text, username, tweet_timestamp, classification_label,
                   confidence_score, category, likes, retweets, replies, processed_at
            FROM tweets 
            WHERE classification_label = 'verified' 
            AND confidence_score >= %s 
            AND category = %s
            AND is_active = TRUE
            ORDER BY tweet_timestamp DESC 
            LIMIT %s
            """
            return self._execute_select_query(query, (min_confidence, category, limit))
        else:
            query = """
            SELECT tweet_id, text, username, tweet_timestamp, classification_label,
                   confidence_score, category, likes, retweets, replies, processed_at
            FROM tweets 
            WHERE classification_label = 'verified' 
            AND confidence_score >= %s 
            AND is_active = TRUE
            ORDER BY tweet_timestamp DESC 
            LIMIT %s
            """
            return self._execute_select_query(query, (min_confidence, limit))

    def get_rumor_tweets(self, limit: int = 50, min_confidence: float = 0.5, category: str = None) -> List[Dict]:
        """Get rumor tweets from database"""
        if category and category != 'all':
            query = """
            SELECT tweet_id, text, username, tweet_timestamp, classification_label,
                   confidence_score, category, likes, retweets, replies, processed_at
            FROM tweets 
            WHERE classification_label = 'rumor' 
            AND confidence_score >= %s 
            AND category = %s
            AND is_active = TRUE
            ORDER BY tweet_timestamp DESC 
            LIMIT %s
            """
            return self._execute_select_query(query, (min_confidence, category, limit))
        else:
            query = """
            SELECT tweet_id, text, username, tweet_timestamp, classification_label,
                   confidence_score, category, likes, retweets, replies, processed_at
            FROM tweets 
            WHERE classification_label = 'rumor' 
            AND confidence_score >= %s 
            AND is_active = TRUE
            ORDER BY tweet_timestamp DESC 
            LIMIT %s
            """
            return self._execute_select_query(query, (min_confidence, limit))

    def get_all_tweets(self, limit: int = 100, category: str = None) -> List[Dict]:
        """Get all tweets from database"""
        if category and category != 'all':
            query = """
            SELECT tweet_id, text, username, tweet_timestamp, classification_label,
                   confidence_score, category, likes, retweets, replies, processed_at
            FROM tweets 
            WHERE is_active = TRUE AND category = %s
            ORDER BY tweet_timestamp DESC 
            LIMIT %s
            """
            return self._execute_select_query(query, (category, limit))
        else:
            query = """
            SELECT tweet_id, text, username, tweet_timestamp, classification_label,
                   confidence_score, category, likes, retweets, replies, processed_at
            FROM tweets 
            WHERE is_active = TRUE
            ORDER BY tweet_timestamp DESC 
            LIMIT %s
            """
            return self._execute_select_query(query, (limit,))

    def get_stats(self) -> Dict:
        """Get classification statistics"""
        query = """
        SELECT 
            classification_label,
            COUNT(*) as count,
            AVG(confidence_score) as avg_confidence,
            MAX(confidence_score) as max_confidence,
            MIN(confidence_score) as min_confidence
        FROM tweets 
        WHERE processed_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        AND is_active = TRUE
        GROUP BY classification_label
        """
        
        results = self._execute_select_query(query)
        stats = {}
        for row in results:
            stats[row['classification_label']] = {
                'count': row['count'],
                'avg_confidence': float(row['avg_confidence']),
                'max_confidence': float(row['max_confidence']),
                'min_confidence': float(row['min_confidence'])
            }
        return stats

    def _execute_select_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SELECT query and return results as list of dictionaries"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            results = cursor.fetchall()
            
            # Convert datetime objects to strings for JSON serialization
            for result in results:
                for key, value in result.items():
                    if isinstance(value, datetime):
                        result[key] = value.isoformat()
                        
            return results
            
        except Error as e:
            logging.error(f"Error executing query: {e}")
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def log_api_request(self, endpoint: str):
        """Log API request for analytics"""
        query = """
        INSERT INTO api_logs (endpoint, request_count, last_accessed)
        VALUES (%s, 1, NOW())
        ON DUPLICATE KEY UPDATE
        request_count = request_count + 1,
        last_accessed = NOW()
        """
        
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, (endpoint,))
            
        except Error as e:
            logging.error(f"Error logging API request: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    # Authentication Methods
    def create_user(self, username: str, email: str, password_hash: str, full_name: str = None) -> bool:
        """Create a new user"""
        insert_query = """
        INSERT INTO users (username, email, password_hash, full_name)
        VALUES (%s, %s, %s, %s)
        """
        
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(insert_query, (username, email, password_hash, full_name))
            return True
            
        except Error as e:
            logging.error(f"Error creating user: {e}")
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        query = """
        SELECT id, username, email, password_hash, full_name, created_at, last_login, is_active
        FROM users 
        WHERE username = %s AND is_active = TRUE
        """
        
        results = self._execute_select_query(query, (username,))
        return results[0] if results else None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = """
        SELECT id, username, email, password_hash, full_name, created_at, last_login, is_active
        FROM users 
        WHERE email = %s AND is_active = TRUE
        """
        
        results = self._execute_select_query(query, (email,))
        return results[0] if results else None

    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        update_query = """
        UPDATE users 
        SET last_login = NOW() 
        WHERE id = %s
        """
        
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(update_query, (user_id,))
            return True
            
        except Error as e:
            logging.error(f"Error updating last login: {e}")
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def check_username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        query = "SELECT COUNT(*) as count FROM users WHERE username = %s"
        results = self._execute_select_query(query, (username,))
        return results[0]['count'] > 0 if results else False

    def check_email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        query = "SELECT COUNT(*) as count FROM users WHERE email = %s"
        results = self._execute_select_query(query, (email,))
        return results[0]['count'] > 0 if results else False

# Global database instance
db = MySQLDatabase()