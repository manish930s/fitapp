"""
Comprehensive MongoDB to Supabase migration script for server.py
"""
import re

def convert_mongodb_to_supabase(content):
    """Convert MongoDB operations to Supabase operations"""
    
    # 1. Replace imports
    content = content.replace(
        'from pymongo import MongoClient',
        'from supabase import create_client, Client'
    )
    
    # 2. Replace connection setup
    mongo_conn_pattern = r'# MongoDB Connection.*?workout_sessions_collection = db\[\'workout_sessions\'\]'
    supabase_conn = '''# Supabase Connection
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)'''
    
    content = re.sub(mongo_conn_pattern, supabase_conn, content, flags=re.DOTALL)
    
    # 3. Replace get_current_user function
    old_get_user = r'def get_current_user\(credentials.*?\n    return user'
    new_get_user = '''def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_jwt_token(token)
    result = supabase.table('users').select('*').eq('user_id', payload["user_id"]).execute()
    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=401, detail="User not found")
    return result.data[0]'''
    
    content = re.sub(old_get_user, new_get_user, content, flags=re.DOTALL)
    
    # 4. Convert collection operations - specific patterns
    
    # find_one patterns
    replacements = [
        # users_collection.find_one({"email": email})
        (r'users_collection\.find_one\(\{"email": ([^}]+)\}\)',
         r'supabase.table(\'users\').select(\'*\').eq(\'email\', \1).execute()'),
        
        # users_collection.find_one({"user_id": user_id})
        (r'users_collection\.find_one\(\{"user_id": ([^}]+)\}\)',
         r'supabase.table(\'users\').select(\'*\').eq(\'user_id\', \1).execute()'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    return content


def manual_conversions():
    """Return manual conversion instructions for complex queries"""
    return """
    Manual conversions needed for:
    1. Aggregation queries
    2. Complex find() with sort and limit
    3. Update operations with $set
    4. Delete operations
    5. Insert operations
    """

if __name__ == "__main__":
    # Read original file
    with open('server_mongodb_backup.py', 'r') as f:
        original = f.read()
    
    # Convert
    converted = convert_mongodb_to_supabase(original)
    
    # Write
    with open('server_auto_converted.py', 'w') as f:
        f.write(converted)
    
    print("✅ Automatic conversion completed!")
    print("⚠️  Manual review and fixes required")
    print(manual_conversions())
