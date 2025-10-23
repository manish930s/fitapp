"""
Complete MongoDB to Supabase data migration script for FitFlow application
This script migrates all data from MongoDB to Supabase
"""
import os
from pymongo import MongoClient
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# MongoDB Connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
print(f"Connecting to MongoDB: {MONGO_URL}")
mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client['fitflow_db']

# Supabase Connection
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
print(f"Connecting to Supabase: {SUPABASE_URL}")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def convert_datetime(obj):
    """Convert datetime objects to ISO format strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime(item) for item in obj]
    return obj

def migrate_collection(collection_name, table_name, transform_func=None):
    """
    Migrate a MongoDB collection to a Supabase table
    
    Args:
        collection_name: Name of MongoDB collection
        table_name: Name of Supabase table
        transform_func: Optional function to transform documents before insertion
    """
    try:
        print(f"\n📦 Migrating {collection_name} to {table_name}...")
        
        # Get all documents from MongoDB
        mongo_collection = mongo_db[collection_name]
        documents = list(mongo_collection.find({}))
        
        if not documents:
            print(f"   ⚠️  No documents found in {collection_name}")
            return 0
        
        print(f"   Found {len(documents)} documents")
        
        # Transform documents
        migrated_count = 0
        error_count = 0
        
        for doc in documents:
            try:
                # Remove MongoDB _id field
                doc.pop('_id', None)
                
                # Convert datetime objects
                doc = convert_datetime(doc)
                
                # Apply custom transformation if provided
                if transform_func:
                    doc = transform_func(doc)
                
                # Insert into Supabase
                result = supabase.table(table_name).insert(doc).execute()
                migrated_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"   ❌ Error migrating document: {str(e)}")
                print(f"   Document: {doc}")
        
        print(f"   ✅ Migrated {migrated_count} documents ({error_count} errors)")
        return migrated_count
        
    except Exception as e:
        print(f"   ❌ Error migrating {collection_name}: {str(e)}")
        return 0

def migrate_all_data():
    """Migrate all collections from MongoDB to Supabase"""
    print("🚀 Starting MongoDB to Supabase migration...\n")
    
    total_migrated = 0
    
    # 1. Migrate users (must be first due to foreign key constraints)
    print("=" * 60)
    count = migrate_collection('users', 'users')
    total_migrated += count
    
    # 2. Migrate food scans
    print("=" * 60)
    count = migrate_collection('food_scans', 'food_scans')
    total_migrated += count
    
    # 3. Migrate user stats
    print("=" * 60)
    count = migrate_collection('user_stats', 'user_stats')
    total_migrated += count
    
    # 4. Migrate goals
    print("=" * 60)
    count = migrate_collection('goals', 'goals')
    total_migrated += count
    
    # 5. Migrate measurements
    print("=" * 60)
    count = migrate_collection('measurements', 'measurements')
    total_migrated += count
    
    # 6. Migrate chat history
    print("=" * 60)
    count = migrate_collection('chat_history', 'chat_history')
    total_migrated += count
    
    # 7. Migrate meal plans
    print("=" * 60)
    count = migrate_collection('meal_plans', 'meal_plans')
    total_migrated += count
    
    # 8. Migrate exercises (must be before workout_sessions)
    print("=" * 60)
    count = migrate_collection('exercises', 'exercises')
    total_migrated += count
    
    # 9. Migrate workout sessions
    print("=" * 60)
    count = migrate_collection('workout_sessions', 'workout_sessions')
    total_migrated += count
    
    print("\n" + "=" * 60)
    print(f"🎉 Migration complete! Total documents migrated: {total_migrated}")
    print("=" * 60)

def verify_migration():
    """Verify data was migrated successfully"""
    print("\n🔍 Verifying migration...\n")
    
    tables = [
        'users', 'food_scans', 'user_stats', 'goals', 
        'measurements', 'chat_history', 'meal_plans', 
        'exercises', 'workout_sessions'
    ]
    
    for table in tables:
        try:
            result = supabase.table(table).select('*', count='exact').limit(1).execute()
            count = result.count if hasattr(result, 'count') else len(result.data)
            print(f"✅ {table}: {count} records")
        except Exception as e:
            print(f"❌ {table}: Error - {str(e)}")

if __name__ == "__main__":
    try:
        # Test MongoDB connection
        mongo_client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Test Supabase connection
        supabase.table('users').select('user_id').limit(1).execute()
        print("✅ Supabase connection successful\n")
        
        # Run migration
        migrate_all_data()
        
        # Verify migration
        verify_migration()
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        mongo_client.close()
        print("\n✅ MongoDB connection closed")
