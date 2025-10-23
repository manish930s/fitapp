#!/usr/bin/env python3
"""
Create a clean Supabase-based server.py from scratch
This script reads the MongoDB version and creates a properly converted Supabase version
handling all the response.data patterns correctly
"""

import re

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

# Read the original MongoDB server
original = read_file('/app/backend/server.py')

# Step 1: Replace imports
original = original.replace(
    'from pymongo import MongoClient',
    'from supabase import create_client, Client'
)

# Step 2: Replace MongoDB connection with Supabase connection
mongo_pattern = r'# MongoDB Connection\nMONGO_URL.*?workout_sessions_collection = db\[\'workout_sessions\'\]'
supabase_conn = '''# Supabase Connection
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)'''

original = re.sub(mongo_pattern, supabase_conn, original, flags=re.DOTALL)

# Step 3: Helper function to get data from Supabase response
helper_functions = '''
def get_supabase_data(response):
    """Helper to extract data from Supabase response"""
    if hasattr(response, 'data'):
        if isinstance(response.data, list):
            return response.data[0] if response.data else None
        return response.data
    return None

def get_supabase_list(response):
    """Helper to extract list from Supabase response"""
    if hasattr(response, 'data'):
        return response.data if isinstance(response.data, list) else []
    return []
'''

# Insert helper functions after the security = HTTPBearer() line
original = original.replace(
    'security = HTTPBearer()',
    'security = HTTPBearer()' + '\n' + helper_functions
)

# Step 4: Convert all MongoDB operations systematically

# Convert find_one with users_collection
original = re.sub(
    r'users_collection\.find_one\(\{"user_id":\s*([^}]+)\}\)',
    r"get_supabase_data(supabase.table('users').select('*').eq('user_id', \1).execute())",
    original
)

original = re.sub(
    r'users_collection\.find_one\(\{"email":\s*([^}]+)\}\)',
    r"get_supabase_data(supabase.table('users').select('*').eq('email', \1).execute())",
    original
)

# Convert food_scans find_one
original = re.sub(
    r'food_scans_collection\.find_one\(\{"scan_id":\s*([^}]+),\s*"user_id":\s*([^}]+)\}\)',
    r"get_supabase_data(supabase.table('food_scans').select('*').eq('scan_id', \1).eq('user_id', \2).execute())",
    original
)

# Convert exercises find_one  
original = re.sub(
    r'exercises_collection\.find_one\(\{"exercise_id":\s*([^}]+)\}\)',
    r"get_supabase_data(supabase.table('exercises').select('*').eq('exercise_id', \1).execute())",
    original
)

# Convert goals find_one
original = re.sub(
    r'goals_collection\.find_one\(\{"goal_id":\s*([^}]+),\s*"user_id":\s*([^}]+)\}\)',
    r"get_supabase_data(supabase.table('goals').select('*').eq('goal_id', \1).eq('user_id', \2).execute())",
    original
)

# Convert meal_plans find_one
original = re.sub(
    r'meal_plans_collection\.find_one\(\{"plan_id":\s*([^}]+),\s*"user_id":\s*([^}]+)\}\)',
    r"get_supabase_data(supabase.table('meal_plans').select('*').eq('plan_id', \1).eq('user_id', \2).execute())",
    original
)

# Convert workout_sessions find_one
original = re.sub(
    r'workout_sessions_collection\.find_one\(\{"session_id":\s*([^}]+),\s*"user_id":\s*([^}]+)\}\)',
    r"get_supabase_data(supabase.table('workout_sessions').select('*').eq('session_id', \1).eq('user_id', \2).execute())",
    original
)

# Convert user_stats find_one
original = re.sub(
    r'user_stats_collection\.find_one\(\{"user_id":\s*([^}]+),\s*"date":\s*([^}]+)\}\)',
    r"get_supabase_data(supabase.table('user_stats').select('*').eq('user_id', \1).eq('date', \2).execute())",
    original
)

# Convert insert_one operations
original = re.sub(
    r'users_collection\.insert_one\(([^)]+)\)',
    r"supabase.table('users').insert(\1).execute()",
    original
)

original = re.sub(
    r'food_scans_collection\.insert_one\(([^)]+)\)',
    r"supabase.table('food_scans').insert(\1).execute()",
    original
)

original = re.sub(
    r'user_stats_collection\.insert_one\(([^)]+)\)',
    r"supabase.table('user_stats').insert(\1).execute()",
    original
)

original = re.sub(
    r'goals_collection\.insert_one\(([^)]+)\)',
    r"supabase.table('goals').insert(\1).execute()",
    original
)

original = re.sub(
    r'measurements_collection\.insert_one\(([^)]+)\)',
    r"supabase.table('measurements').insert(\1).execute()",
    original
)

original = re.sub(
    r'chat_history_collection\.insert_one\(([^)]+)\)',
    r"supabase.table('chat_history').insert(\1).execute()",
    original
)

original = re.sub(
    r'meal_plans_collection\.insert_one\(([^)]+)\)',
    r"supabase.table('meal_plans').insert(\1).execute()",
    original
)

original = re.sub(
    r'exercises_collection\.insert_one\(([^)]+)\)',
    r"supabase.table('exercises').insert(\1).execute()",
    original
)

original = re.sub(
    r'workout_sessions_collection\.insert_one\(([^)]+)\)',
    r"supabase.table('workout_sessions').insert(\1).execute()",
    original
)

# Convert update_one with $set
original = re.sub(
    r'users_collection\.update_one\(\{"user_id":\s*([^}]+)\},\s*\{"\$set":\s*([^}]+)\}\)',
    r"supabase.table('users').update(\2).eq('user_id', \1).execute()",
    original
)

original = re.sub(
    r'goals_collection\.update_one\(\{"goal_id":\s*([^}]+)\},\s*\{"\$set":\s*([^}]+)\}\)',
    r"supabase.table('goals').update(\2).eq('goal_id', \1).execute()",
    original
)

original = re.sub(
    r'workout_sessions_collection\.update_one\(\{"session_id":\s*([^}]+)\},\s*\{"\$set":\s*([^}]+)\}\)',
    r"supabase.table('workout_sessions').update(\2).eq('session_id', \1).execute()",
    original
)

# Convert delete_one
original = re.sub(
    r'food_scans_collection\.delete_one\(\{"scan_id":\s*([^}]+),\s*"user_id":\s*([^}]+)\}\)',
    r"supabase.table('food_scans').delete().eq('scan_id', \1).eq('user_id', \2).execute()",
    original
)

original = re.sub(
    r'meal_plans_collection\.delete_one\(\{"plan_id":\s*([^}]+),\s*"user_id":\s*([^}]+)\}\)',
    r"supabase.table('meal_plans').delete().eq('plan_id', \1).eq('user_id', \2).execute()",
    original
)

original = re.sub(
    r'workout_sessions_collection\.delete_one\(\{"session_id":\s*([^}]+),\s*"user_id":\s*([^}]+)\}\)',
    r"supabase.table('workout_sessions').delete().eq('session_id', \1).eq('user_id', \2).execute()",
    original
)

# Delete from all collections (user account deletion)
original = re.sub(
    r'food_scans_collection\.delete_many\(\{"user_id":\s*([^}]+)\}\)',
    r"supabase.table('food_scans').delete().eq('user_id', \1).execute()",
    original
)

original = re.sub(
    r'user_stats_collection\.delete_many\(\{"user_id":\s*([^}]+)\}\)',
    r"supabase.table('user_stats').delete().eq('user_id', \1).execute()",
    original
)

original = re.sub(
    r'goals_collection\.delete_many\(\{"user_id":\s*([^}]+)\}\)',
    r"supabase.table('goals').delete().eq('user_id', \1).execute()",
    original
)

original = re.sub(
    r'measurements_collection\.delete_many\(\{"user_id":\s*([^}]+)\}\)',
    r"supabase.table('measurements').delete().eq('user_id', \1).execute()",
    original
)

original = re.sub(
    r'chat_history_collection\.delete_many\(\{"user_id":\s*([^}]+)\}\)',
    r"supabase.table('chat_history').delete().eq('user_id', \1).execute()",
    original
)

original = re.sub(
    r'meal_plans_collection\.delete_many\(\{"user_id":\s*([^}]+)\}\)',
    r"supabase.table('meal_plans').delete().eq('user_id', \1).execute()",
    original
)

original = re.sub(
    r'workout_sessions_collection\.delete_many\(\{"user_id":\s*([^}]+)\}\)',
    r"supabase.table('workout_sessions').delete().eq('user_id', \1).execute()",
    original
)

original = re.sub(
    r'users_collection\.delete_one\(\{"user_id":\s*([^}]+)\}\)',
    r"supabase.table('users').delete().eq('user_id', \1).execute()",
    original
)

# Convert find() with list()
original = re.sub(
    r'list\(food_scans_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("created_at",\s*-1\)\.limit\((\d+)\)\)',
    r"get_supabase_list(supabase.table('food_scans').select('*').eq('user_id', \1).order('created_at', desc=True).limit(\2).execute())",
    original
)

original = re.sub(
    r'list\(food_scans_collection\.find\(\{"user_id":\s*([^}]+),\s*"created_at":\s*\{"(\$[^"]+)":\s*([^}]+)\}\}\)\.sort\("created_at",\s*1\)\)',
    r"get_supabase_list(supabase.table('food_scans').select('*').eq('user_id', \1).gte('created_at', \3).order('created_at', desc=False).execute())",
    original
)

original = re.sub(
    r'list\(goals_collection\.find\(\{"user_id":\s*([^}]+)\}\)\)',
    r"get_supabase_list(supabase.table('goals').select('*').eq('user_id', \1).execute())",
    original
)

original = re.sub(
    r'list\(measurements_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("measured_at",\s*-1\)\.limit\(1\)\)',
    r"get_supabase_list(supabase.table('measurements').select('*').eq('user_id', \1).order('measured_at', desc=True).limit(1).execute())",
    original
)

original = re.sub(
    r'list\(measurements_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("measured_at",\s*-1\)\)',
    r"get_supabase_list(supabase.table('measurements').select('*').eq('user_id', \1).order('measured_at', desc=True).execute())",
    original
)

original = re.sub(
    r'list\(chat_history_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("created_at",\s*1\)\)',
    r"get_supabase_list(supabase.table('chat_history').select('*').eq('user_id', \1).order('created_at', desc=False).execute())",
    original
)

original = re.sub(
    r'list\(meal_plans_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("created_at",\s*-1\)\)',
    r"get_supabase_list(supabase.table('meal_plans').select('*').eq('user_id', \1).order('created_at', desc=True).execute())",
    original
)

original = re.sub(
    r'list\(exercises_collection\.find\(\{\}\)\)',
    r"get_supabase_list(supabase.table('exercises').select('*').execute())",
    original
)

original = re.sub(
    r'list\(workout_sessions_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("created_at",\s*-1\)\)',
    r"get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', \1).order('created_at', desc=True).execute())",
    original
)

original = re.sub(
    r'list\(workout_sessions_collection\.find\(\{"user_id":\s*([^}]+),\s*"exercise_id":\s*([^}]+)\}\)\.sort\("created_at",\s*-1\)\.limit\((\d+)\)\)',
    r"get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', \1).eq('exercise_id', \2).order('created_at', desc=True).limit(\3).execute())",
    original
)

original = re.sub(
    r'list\(workout_sessions_collection\.find\(\{"user_id":\s*([^}]+),\s*"exercise_id":\s*([^}]+)\}\)\)',
    r"get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', \1).eq('exercise_id', \2).execute())",
    original
)

original = re.sub(
    r'list\(user_stats_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("date",\s*-1\)\)',
    r"get_supabase_list(supabase.table('user_stats').select('*').eq('user_id', \1).order('date', desc=True).execute())",
    original
)

# Convert upsert operations (update with upsert=True)
original = re.sub(
    r'user_stats_collection\.update_one\(\s*\{"user_id":\s*([^,]+),\s*"date":\s*([^}]+)\},\s*\{"\$set":\s*([^}]+)\},\s*upsert=True\s*\)',
    r"supabase.table('user_stats').upsert({'user_id': \1, 'date': \2, **\3}).execute()",
    original
)

# Write the converted file
write_file('/app/backend/server_supabase_converted.py', original)

print("✅ Supabase conversion complete!")
print("📁 Saved to: /app/backend/server_supabase_converted.py")
print("\n🔍 Next steps:")
print("1. Review the converted file")
print("2. Backup server.py: cp server.py server_mongodb_backup.py")
print("3. Replace: cp server_supabase_converted.py server.py")
print("4. Restart backend")
