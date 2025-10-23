#!/usr/bin/env python3
"""
Fix remaining MongoDB references in the converted Supabase file
This handles all the edge cases that the automated script missed
"""

import re

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

# Read the partially converted file
content = read_file('/app/backend/server_supabase_converted.py')

# Fix complex patterns that were missed

# Fix multi-line update_one operations
content = re.sub(
    r'users_collection\.update_one\(\s*\{"user_id":\s*current_user\["user_id"\]\},\s*\{"\$set":\s*update_data\}\s*\)',
    r'supabase.table(\'users\').update(update_data).eq(\'user_id\', current_user["user_id"]).execute()',
    content,
    flags=re.MULTILINE
)

content = re.sub(
    r'users_collection\.update_one\(\s*\{"user_id":\s*current_user\["user_id"\]\},\s*\{"\$set":\s*\{"password":\s*hashed_password\}\}\s*\)',
    r'supabase.table(\'users\').update({"password": hashed_password}).eq(\'user_id\', current_user["user_id"]).execute()',
    content,
    flags=re.MULTILINE
)

# Fix user_stats find_one with multiline
content = re.sub(
    r'stats\s*=\s*user_stats_collection\.find_one\(\{\s*"user_id":\s*current_user\["user_id"\],\s*"date":\s*today\s*\}\)',
    r'stats = get_supabase_data(supabase.table(\'user_stats\').select(\'*\').eq(\'user_id\', current_user["user_id"]).eq(\'date\', today).execute())',
    content,
    flags=re.MULTILINE
)

content = re.sub(
    r'stats\s*=\s*user_stats_collection\.find_one\(\{\s*"user_id":\s*current_user\["user_id"\],\s*"date":\s*date_str\s*\}\)',
    r'stats = get_supabase_data(supabase.table(\'user_stats\').select(\'*\').eq(\'user_id\', current_user["user_id"]).eq(\'date\', date_str).execute())',
    content,
    flags=re.MULTILINE
)

# Fix user_stats update_one with new_calories
content = re.sub(
    r'user_stats_collection\.update_one\(\s*\{"user_id":\s*current_user\["user_id"\],\s*"date":\s*today\},\s*\{"\$set":\s*\{"calories_consumed":\s*new_calories,\s*"updated_at":\s*datetime\.utcnow\(\)\.isoformat\(\)\}\}\s*\)',
    r'supabase.table(\'user_stats\').update({"calories_consumed": new_calories, "updated_at": datetime.utcnow().isoformat()}).eq(\'user_id\', current_user["user_id"]).eq(\'date\', today).execute()',
    content,
    flags=re.MULTILINE
)

# Fix food_scans find with limit
content = re.sub(
    r'scans\s*=\s*list\(food_scans_collection\.find\(\s*\{"user_id":\s*current_user\["user_id"\]\}\s*\)\.sort\("scanned_at",\s*-1\)\.limit\(limit\)\)',
    r'scans = get_supabase_list(supabase.table(\'food_scans\').select(\'*\').eq(\'user_id\', current_user["user_id"]).order(\'scanned_at\', desc=True).limit(limit).execute())',
    content,
    flags=re.MULTILINE
)

# Fix food_scans find with date filter
content = re.sub(
    r'scans\s*=\s*list\(food_scans_collection\.find\(\{[^}]*"user_id":\s*current_user\["user_id"\],[^}]*"created_at":\s*\{"\$gte":\s*start_of_day\}[^}]*\}\)\.sort\("created_at",\s*1\)\)',
    r'scans = get_supabase_list(supabase.table(\'food_scans\').select(\'*\').eq(\'user_id\', current_user["user_id"]).gte(\'created_at\', start_of_day).order(\'created_at\', desc=False).execute())',
    content,
    flags=re.MULTILINE
)

# Fix food_scans delete_one
content = re.sub(
    r'result\s*=\s*food_scans_collection\.delete_one\(\{\s*"scan_id":\s*scan_id,\s*"user_id":\s*current_user\["user_id"\]\s*\}\)',
    r'result = supabase.table(\'food_scans\').delete().eq(\'scan_id\', scan_id).eq(\'user_id\', current_user["user_id"]).execute()',
    content,
    flags=re.MULTILINE
)

# Fix user_stats update with inc_data
content = re.sub(
    r'user_stats_collection\.update_one\(\s*\{"user_id":\s*current_user\["user_id"\],\s*"date":\s*date_str\},\s*\{"\$set":\s*inc_data\},\s*upsert=True\s*\)',
    r'supabase.table(\'user_stats\').upsert({\'user_id\': current_user["user_id"], \'date\': date_str, **inc_data}).execute()',
    content,
    flags=re.MULTILINE
)

# Fix user_stats find for streak
content = re.sub(
    r'stats\s*=\s*list\(user_stats_collection\.find\(\s*\{"user_id":\s*current_user\["user_id"\]\}\s*\)\.sort\("date",\s*-1\)\)',
    r'stats = get_supabase_list(supabase.table(\'user_stats\').select(\'*\').eq(\'user_id\', current_user["user_id"]).order(\'date\', desc=True).execute())',
    content,
    flags=re.MULTILINE
)

# Fix goals find
content = re.sub(
    r'goals\s*=\s*list\(goals_collection\.find\(\s*\{"user_id":\s*current_user\["user_id"\]\}\s*\)\)',
    r'goals = get_supabase_list(supabase.table(\'goals\').select(\'*\').eq(\'user_id\', current_user["user_id"]).execute())',
    content,
    flags=re.MULTILINE
)

# Fix goals update_one
content = re.sub(
    r'result\s*=\s*goals_collection\.update_one\(\s*\{"goal_id":\s*goal_id,\s*"user_id":\s*current_user\["user_id"\]\},\s*\{"\$set":\s*\{"current_progress":\s*goal_data\.current_progress\}\}\s*\)',
    r'result = supabase.table(\'goals\').update({"current_progress": goal_data.current_progress}).eq(\'goal_id\', goal_id).eq(\'user_id\', current_user["user_id"]).execute()',
    content,
    flags=re.MULTILINE
)

# Fix measurements find_one for latest
content = re.sub(
    r'measurement\s*=\s*measurements_collection\.find_one\(\s*\{"user_id":\s*current_user\["user_id"\]\},\s*sort=\[\("measured_at",\s*-1\)\]\s*\)',
    r'measurement_list = get_supabase_list(supabase.table(\'measurements\').select(\'*\').eq(\'user_id\', current_user["user_id"]).order(\'measured_at\', desc=True).limit(1).execute())\n    measurement = measurement_list[0] if measurement_list else None',
    content,
    flags=re.MULTILINE
)

# Fix measurements find for history
content = re.sub(
    r'measurements\s*=\s*list\(measurements_collection\.find\(\s*\{"user_id":\s*current_user\["user_id"\]\}\s*\)\.sort\("measured_at",\s*-1\)\)',
    r'measurements = get_supabase_list(supabase.table(\'measurements\').select(\'*\').eq(\'user_id\', current_user["user_id"]).order(\'measured_at\', desc=True).execute())',
    content,
    flags=re.MULTILINE
)

# Fix chat_history find
content = re.sub(
    r'chats\s*=\s*list\(chat_history_collection\.find\(\s*\{"user_id":\s*current_user\["user_id"\]\}\s*\)\.sort\("created_at",\s*1\)\)',
    r'chats = get_supabase_list(supabase.table(\'chat_history\').select(\'*\').eq(\'user_id\', current_user["user_id"]).order(\'created_at\', desc=False).execute())',
    content,
    flags=re.MULTILINE
)

# Fix users find_one with projection
content = re.sub(
    r'user\s*=\s*users_collection\.find_one\(\{"user_id":\s*current_user\["user_id"\]\},\s*\{"_id":\s*0\}\)',
    r'user = get_supabase_data(supabase.table(\'users\').select(\'*\').eq(\'user_id\', current_user["user_id"]).execute())',
    content,
    flags=re.MULTILINE
)

# Fix meal_plans find
content = re.sub(
    r'plans\s*=\s*list\(meal_plans_collection\.find\(\s*\{"user_id":\s*current_user\["user_id"\]\}\s*\)\.sort\("created_at",\s*-1\)\)',
    r'plans = get_supabase_list(supabase.table(\'meal_plans\').select(\'*\').eq(\'user_id\', current_user["user_id"]).order(\'created_at\', desc=True).execute())',
    content,
    flags=re.MULTILINE
)

# Fix meal_plans find_one
content = re.sub(
    r'plan\s*=\s*meal_plans_collection\.find_one\(\s*\{"plan_id":\s*plan_id,\s*"user_id":\s*current_user\["user_id"\]\}\s*\)',
    r'plan = get_supabase_data(supabase.table(\'meal_plans\').select(\'*\').eq(\'plan_id\', plan_id).eq(\'user_id\', current_user["user_id"]).execute())',
    content,
    flags=re.MULTILINE
)

# Fix meal_plans delete_one
content = re.sub(
    r'result\s*=\s*meal_plans_collection\.delete_one\(\{\s*"plan_id":\s*plan_id,\s*"user_id":\s*current_user\["user_id"\]\s*\}\)',
    r'result = supabase.table(\'meal_plans\').delete().eq(\'plan_id\', plan_id).eq(\'user_id\', current_user["user_id"]).execute()',
    content,
    flags=re.MULTILINE
)

# Fix meal_plans update_one
content = re.sub(
    r'meal_plans_collection\.update_one\(\s*\{"plan_id":\s*plan_id\},\s*\{"\$set":\s*\{f"days\.\{day_index\}\.meals\.\{meal_type\}":\s*meal_dict\}\}\s*\)',
    r'# Supabase update requires fetching the plan, modifying it, and updating\n        plan = get_supabase_data(supabase.table(\'meal_plans\').select(\'*\').eq(\'plan_id\', plan_id).execute())\n        if plan:\n            plan[\'days\'][day_index][\'meals\'][meal_type] = meal_dict\n            supabase.table(\'meal_plans\').update({\'days\': plan[\'days\']}).eq(\'plan_id\', plan_id).execute()',
    content,
    flags=re.MULTILINE
)

# Fix exercises find with query
content = re.sub(
    r'exercises\s*=\s*list\(exercises_collection\.find\(query,\s*\{"_id":\s*0\}\)\)',
    r'exercises = get_supabase_list(supabase.table(\'exercises\').select(\'*\').execute())',
    content,
    flags=re.MULTILINE
)

# Fix exercises find_one
content = re.sub(
    r'exercise\s*=\s*exercises_collection\.find_one\(\{"exercise_id":\s*exercise_id\},\s*\{"_id":\s*0\}\)',
    r'exercise = get_supabase_data(supabase.table(\'exercises\').select(\'*\').eq(\'exercise_id\', exercise_id).execute())',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions find_one for last_session
content = re.sub(
    r'last_session_raw\s*=\s*workout_sessions_collection\.find_one\(\s*\{"user_id":\s*current_user\["user_id"\],\s*"exercise_id":\s*exercise_id\},\s*sort=\[\("created_at",\s*-1\)\]\s*\)',
    r'last_session_list = get_supabase_list(supabase.table(\'workout_sessions\').select(\'*\').eq(\'user_id\', current_user["user_id"]).eq(\'exercise_id\', exercise_id).order(\'created_at\', desc=True).limit(1).execute())\n        last_session_raw = last_session_list[0] if last_session_list else None',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions update for active_minutes
content = re.sub(
    r'user_stats_collection\.update_one\(\s*\{"user_id":\s*current_user\["user_id"\],\s*"date":\s*today\},\s*\{"\$set":\s*\{"active_minutes":\s*new_active_minutes,\s*"updated_at":\s*datetime\.utcnow\(\)\.isoformat\(\)\}\},\s*upsert=True\s*\)',
    r'supabase.table(\'user_stats\').upsert({\'user_id\': current_user["user_id"], \'date\': today, \'active_minutes\': new_active_minutes, \'updated_at\': datetime.utcnow().isoformat()}).execute()',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions find
content = re.sub(
    r'sessions\s*=\s*list\(workout_sessions_collection\.find\(\s*query\s*\)\.sort\("created_at",\s*-1\)\)',
    r'# Handle query for Supabase\n        if "exercise_id" in query:\n            sessions = get_supabase_list(supabase.table(\'workout_sessions\').select(\'*\').eq(\'user_id\', current_user["user_id"]).eq(\'exercise_id\', query["exercise_id"]).order(\'created_at\', desc=True).execute())\n        else:\n            sessions = get_supabase_list(supabase.table(\'workout_sessions\').select(\'*\').eq(\'user_id\', current_user["user_id"]).order(\'created_at\', desc=True).execute())',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions find_one
content = re.sub(
    r'session\s*=\s*workout_sessions_collection\.find_one\(\s*\{"session_id":\s*session_id,\s*"user_id":\s*current_user\["user_id"\]\}\s*\)',
    r'session = get_supabase_data(supabase.table(\'workout_sessions\').select(\'*\').eq(\'session_id\', session_id).eq(\'user_id\', current_user["user_id"]).execute())',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions delete_one
content = re.sub(
    r'result\s*=\s*workout_sessions_collection\.delete_one\(\{\s*"session_id":\s*session_id,\s*"user_id":\s*current_user\["user_id"\]\s*\}\)',
    r'result = supabase.table(\'workout_sessions\').delete().eq(\'session_id\', session_id).eq(\'user_id\', current_user["user_id"]).execute()',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions existing_session
content = re.sub(
    r'existing_session\s*=\s*workout_sessions_collection\.find_one\(\{\s*"session_id":\s*session_id,\s*"user_id":\s*current_user\["user_id"\]\s*\}\)',
    r'existing_session = get_supabase_data(supabase.table(\'workout_sessions\').select(\'*\').eq(\'session_id\', session_id).eq(\'user_id\', current_user["user_id"]).execute())',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions update_one
content = re.sub(
    r'workout_sessions_collection\.update_one\(\s*\{"session_id":\s*session_id\},\s*\{"\$set":\s*update_data\}\s*\)',
    r'supabase.table(\'workout_sessions\').update(update_data).eq(\'session_id\', session_id).execute()',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions updated_session
content = re.sub(
    r'updated_session\s*=\s*workout_sessions_collection\.find_one\(\{"session_id":\s*session_id\}\)',
    r'updated_session = get_supabase_data(supabase.table(\'workout_sessions\').select(\'*\').eq(\'session_id\', session_id).execute())',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions find for history
content = re.sub(
    r'sessions\s*=\s*list\(workout_sessions_collection\.find\(\s*\{"user_id":\s*current_user\["user_id"\],\s*"exercise_id":\s*exercise_id\}\s*\)\.sort\("created_at",\s*-1\)\.limit\(10\)\)',
    r'sessions = get_supabase_list(supabase.table(\'workout_sessions\').select(\'*\').eq(\'user_id\', current_user["user_id"]).eq(\'exercise_id\', exercise_id).order(\'created_at\', desc=True).limit(10).execute())',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions find for stats
content = re.sub(
    r'sessions\s*=\s*list\(workout_sessions_collection\.find\(\s*\{"user_id":\s*current_user\["user_id"\],\s*"exercise_id":\s*exercise_id\}\s*\)\)',
    r'sessions = get_supabase_list(supabase.table(\'workout_sessions\').select(\'*\').eq(\'user_id\', current_user["user_id"]).eq(\'exercise_id\', exercise_id).execute())',
    content,
    flags=re.MULTILINE
)

# Fix workout_sessions find for all sessions
content = re.sub(
    r'all_sessions\s*=\s*list\(workout_sessions_collection\.find\(\s*\{"user_id":\s*current_user\["user_id"\]\}\s*\)\)',
    r'all_sessions = get_supabase_list(supabase.table(\'workout_sessions\').select(\'*\').eq(\'user_id\', current_user["user_id"]).execute())',
    content,
    flags=re.MULTILINE
)

# Write the fully converted file
write_file('/app/backend/server_supabase_final.py', content)

print("✅ All MongoDB references converted to Supabase!")
print("📁 Saved to: /app/backend/server_supabase_final.py")
print("\n🔍 Verifying conversion...")

# Verify no MongoDB references remain
remaining = content.count('_collection.')
if remaining > 0:
    print(f"⚠️  WARNING: Found {remaining} remaining '_collection.' references")
    print("   Manual review may be needed")
else:
    print("✅ No MongoDB references found - conversion complete!")

print("\n📋 Next steps:")
print("1. Backup: cp /app/backend/server.py /app/backend/server_mongodb_original.py")
print("2. Replace: cp /app/backend/server_supabase_final.py /app/backend/server.py")
print("3. Restart backend: sudo supervisorctl restart backend")
