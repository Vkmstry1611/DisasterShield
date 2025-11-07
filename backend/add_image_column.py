"""
Migration script to add image_url column to existing tweets table
Run this once to update the Render database schema
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def add_image_column():
    """Add image_url column to tweets table"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        database_url = f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'disastershield_db')}"
    
    try:
        connection = psycopg2.connect(database_url)
        cursor = connection.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='tweets' AND column_name='image_url'
        """)
        
        if cursor.fetchone():
            print("✅ Column 'image_url' already exists")
        else:
            # Add the column
            cursor.execute("ALTER TABLE tweets ADD COLUMN image_url TEXT")
            connection.commit()
            print("✅ Successfully added 'image_url' column to tweets table")
        
        # Fix api_logs constraint issue
        cursor.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name='api_logs' AND constraint_type='UNIQUE'
        """)
        
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE api_logs ADD CONSTRAINT api_logs_endpoint_key UNIQUE (endpoint)")
            connection.commit()
            print("✅ Added unique constraint to api_logs table")
        else:
            print("✅ api_logs constraint already exists")
        
        cursor.close()
        connection.close()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    add_image_column()
