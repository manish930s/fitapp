#!/usr/bin/env python3
"""
Comprehensive MongoDB to Supabase conversion script
Converts server.py from MongoDB operations to Supabase with proper .eq() chaining
"""

import re

def convert_mongodb_to_supabase(content):
    """Convert MongoDB operations to Supabase operations with proper .eq() chaining"""
    
    # Step 1: Replace imports
    content = content.replace(
        'from pymongo import MongoClient',
        'from supabase import create_client, Client'
    )
    
    # Step 2: Replace connection setup
    mongo_conn_pattern = r'# MongoDB Connection.*?workout_sessions_collection = db\[\'workout_sessions\'\]'
    supabase_conn = '''# Supabase Connection
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)'''
    
    content = re.sub(mongo_conn_pattern, supabase_conn, content, flags=re.DOTALL)
    
    # Step 3: Convert find_one operations with proper .eq() chaining
    # Pattern: collection.find_one({"field": value})
    # Replace with: supabase.table('table').select('*').eq('field', value).execute()
    
    # Users collection queries
    content = re.sub(
        r'users_collection\.find_one\(\{"email":\s*([^}]+)\}\)',
        r"supabase.table('users').select('*').eq('email', \1).execute()",
        content
    )
    
    content = re.sub(
        r'users_collection\.find_one\(\{"user_id":\s*([^}]+)\}\)',
        r"supabase.table('users').select('*').eq('user_id', \1).execute()",
        content
    )
    
    # Food scans queries
    content = re.sub(
        r'food_scans_collection\.find_one\(\{"scan_id":\s*([^}]+)\}\)',
        r"supabase.table('food_scans').select('*').eq('scan_id', \1).execute()",
        content
    )
    
    # Goals queries
    content = re.sub(
        r'goals_collection\.find_one\(\{"goal_id":\s*([^}]+)\}\)',
        r"supabase.table('goals').select('*').eq('goal_id', \1).execute()",
        content
    )
    
    # Meal plans queries
    content = re.sub(
        r'meal_plans_collection\.find_one\(\{"plan_id":\s*([^}]+)\}\)',
        r"supabase.table('meal_plans').select('*').eq('plan_id', \1).execute()",
        content
    )
    
    # Exercises queries
    content = re.sub(
        r'exercises_collection\.find_one\(\{"exercise_id":\s*([^}]+)\}\)',
        r"supabase.table('exercises').select('*').eq('exercise_id', \1).execute()",
        content
    )
    
    # Workout sessions queries
    content = re.sub(
        r'workout_sessions_collection\.find_one\(\{"session_id":\s*([^}]+)\}\)',
        r"supabase.table('workout_sessions').select('*').eq('session_id', \1).execute()",
        content
    )
    
    # Step 4: Convert insert_one operations
    # Pattern: collection.insert_one(data)
    # Replace with: supabase.table('table').insert(data).execute()
    
    content = re.sub(
        r'users_collection\.insert_one\(([^)]+)\)',
        r"supabase.table('users').insert(\1).execute()",
        content
    )
    
    content = re.sub(
        r'food_scans_collection\.insert_one\(([^)]+)\)',
        r"supabase.table('food_scans').insert(\1).execute()",
        content
    )
    
    content = re.sub(
        r'user_stats_collection\.insert_one\(([^)]+)\)',
        r"supabase.table('user_stats').insert(\1).execute()",
        content
    )
    
    content = re.sub(
        r'goals_collection\.insert_one\(([^)]+)\)',
        r"supabase.table('goals').insert(\1).execute()",
        content
    )
    
    content = re.sub(
        r'measurements_collection\.insert_one\(([^)]+)\)',
        r"supabase.table('measurements').insert(\1).execute()",
        content
    )
    
    content = re.sub(
        r'chat_history_collection\.insert_one\(([^)]+)\)',
        r"supabase.table('chat_history').insert(\1).execute()",
        content
    )
    
    content = re.sub(
        r'meal_plans_collection\.insert_one\(([^)]+)\)',
        r"supabase.table('meal_plans').insert(\1).execute()",
        content
    )
    
    content = re.sub(
        r'exercises_collection\.insert_one\(([^)]+)\)',
        r"supabase.table('exercises').insert(\1).execute()",
        content
    )
    
    content = re.sub(
        r'workout_sessions_collection\.insert_one\(([^)]+)\)',
        r"supabase.table('workout_sessions').insert(\1).execute()",
        content
    )
    
    # Step 5: Convert update_one operations with proper .eq() chaining
    # Pattern: collection.update_one({"field": value}, {"$set": data})
    # Replace with: supabase.table('table').update(data).eq('field', value).execute()
    
    content = re.sub(
        r'users_collection\.update_one\(\{"user_id":\s*([^}]+)\},\s*\{"\$set":\s*([^}]+)\}\)',
        r"supabase.table('users').update(\2).eq('user_id', \1).execute()",
        content
    )
    
    content = re.sub(
        r'user_stats_collection\.update_one\(\{"user_id":\s*([^}]+),\s*"date":\s*([^}]+)\},\s*\{"\$set":\s*([^}]+)\},\s*upsert=True\)',
        r"supabase.table('user_stats').upsert({'user_id': \1, 'date': \2, **\3}).execute()",
        content
    )
    
    content = re.sub(
        r'goals_collection\.update_one\(\{"goal_id":\s*([^}]+)\},\s*\{"\$set":\s*([^}]+)\}\)',
        r"supabase.table('goals').update(\2).eq('goal_id', \1).execute()",
        content
    )
    
    content = re.sub(
        r'meal_plans_collection\.update_one\(\{"plan_id":\s*([^}]+)\},\s*\{"\$set":\s*([^}]+)\}\)',
        r"supabase.table('meal_plans').update(\2).eq('plan_id', \1).execute()",
        content
    )
    
    content = re.sub(
        r'workout_sessions_collection\.update_one\(\{"session_id":\s*([^}]+)\},\s*\{"\$set":\s*([^}]+)\}\)',
        r"supabase.table('workout_sessions').update(\2).eq('session_id', \1).execute()",
        content
    )
    
    # Step 6: Convert delete_one operations with proper .eq() chaining
    # Pattern: collection.delete_one({"field": value})
    # Replace with: supabase.table('table').delete().eq('field', value).execute()
    
    content = re.sub(
        r'food_scans_collection\.delete_one\(\{"scan_id":\s*([^}]+)\}\)',
        r"supabase.table('food_scans').delete().eq('scan_id', \1).execute()",
        content
    )
    
    content = re.sub(
        r'meal_plans_collection\.delete_one\(\{"plan_id":\s*([^}]+)\}\)',
        r"supabase.table('meal_plans').delete().eq('plan_id', \1).execute()",
        content
    )
    
    content = re.sub(
        r'workout_sessions_collection\.delete_one\(\{"session_id":\s*([^}]+)\}\)',
        r"supabase.table('workout_sessions').delete().eq('session_id', \1).execute()",
        content
    )
    
    content = re.sub(
        r'users_collection\.delete_one\(\{"user_id":\s*([^}]+)\}\)',
        r"supabase.table('users').delete().eq('user_id', \1).execute()",
        content
    )
    
    # Step 7: Convert find() operations (list queries) with proper .eq() chaining
    # Pattern: list(collection.find({"field": value}))
    # Replace with: supabase.table('table').select('*').eq('field', value).execute()
    
    content = re.sub(
        r'list\(food_scans_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("created_at",\s*-1\)\.limit\((\d+)\)\)',
        r"supabase.table('food_scans').select('*').eq('user_id', \1).order('created_at', desc=True).limit(\2).execute()",
        content
    )
    
    content = re.sub(
        r'list\(food_scans_collection\.find\(\{"user_id":\s*([^}]+)\}\)\)',
        r"supabase.table('food_scans').select('*').eq('user_id', \1).execute()",
        content
    )
    
    content = re.sub(
        r'list\(goals_collection\.find\(\{"user_id":\s*([^}]+)\}\)\)',
        r"supabase.table('goals').select('*').eq('user_id', \1).execute()",
        content
    )
    
    content = re.sub(
        r'list\(measurements_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("measured_at",\s*-1\)\)',
        r"supabase.table('measurements').select('*').eq('user_id', \1).order('measured_at', desc=True).execute()",
        content
    )
    
    content = re.sub(
        r'list\(chat_history_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("created_at",\s*1\)\)',
        r"supabase.table('chat_history').select('*').eq('user_id', \1).order('created_at', desc=False).execute()",
        content
    )
    
    content = re.sub(
        r'list\(meal_plans_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("created_at",\s*-1\)\)',
        r"supabase.table('meal_plans').select('*').eq('user_id', \1).order('created_at', desc=True).execute()",
        content
    )
    
    content = re.sub(
        r'list\(exercises_collection\.find\(\{\}\)\)',
        r"supabase.table('exercises').select('*').execute()",
        content
    )
    
    content = re.sub(
        r'list\(workout_sessions_collection\.find\(\{"user_id":\s*([^}]+)\}\)\.sort\("created_at",\s*-1\)\)',
        r"supabase.table('workout_sessions').select('*').eq('user_id', \1).order('created_at', desc=True).execute()",
        content
    )
    
    return content


def main():
    # Read the original MongoDB server.py
    with open('/app/backend/server.py', 'r') as f:
        original_content = f.read()
    
    print("🔄 Converting MongoDB operations to Supabase...")
    
    # Convert the content
    converted_content = convert_mongodb_to_supabase(original_content)
    
    # Write the converted file
    with open('/app/backend/server_supabase.py', 'w') as f:
        f.write(converted_content)
    
    print("✅ Conversion complete! File saved to server_supabase.py")
    print("📝 Review the file before replacing server.py")

if __name__ == "__main__":
    main()
