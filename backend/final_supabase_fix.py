#!/usr/bin/env python3
"""
Final pass to convert ALL remaining MongoDB references to Supabase
"""

import re

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

content = read_file('/app/backend/server_supabase_final.py')

# Replace all remaining _collection patterns manually

# Line 1441-1444: food_scans with date filter
content = content.replace(
    '''    scans = list(food_scans_collection.find({
        "user_id": current_user["user_id"],
        "scanned_at": {"$gte": today_start.isoformat()}
    }).sort("scanned_at", -1))''',
    '''    scans = get_supabase_list(supabase.table('food_scans').select('*').eq('user_id', current_user["user_id"]).gte('scanned_at', today_start.isoformat()).order('scanned_at', desc=True).execute())'''
)

# Line 1554: user_stats update
content = content.replace(
    '''            user_stats_collection.update_one(
                {"user_id": current_user["user_id"], "date": date_str},
                {"$set": {"active_minutes": new_active_minutes, "updated_at": datetime.utcnow().isoformat()}},
                upsert=True
            )''',
    '''            supabase.table('user_stats').upsert({'user_id': current_user["user_id"], 'date': date_str, 'active_minutes': new_active_minutes, 'updated_at': datetime.utcnow().isoformat()}).execute()'''
)

# Line 1607: goals find
content = content.replace(
    '''    goals = list(goals_collection.find(
        {"user_id": current_user["user_id"]}
    ))''',
    '''    goals = get_supabase_list(supabase.table('goals').select('*').eq('user_id', current_user["user_id"]).execute())'''
)

# Line 1615: goals update_one
content = content.replace(
    '''    result = goals_collection.update_one(
        {"goal_id": goal_id, "user_id": current_user["user_id"]},
        {"$set": {"current_progress": goal_data.current_progress}}
    )''',
    '''    result = supabase.table('goals').update({"current_progress": goal_data.current_progress}).eq('goal_id', goal_id).eq('user_id', current_user["user_id"]).execute()'''
)

# Line 1644: measurements find_one
content = content.replace(
    '''    measurement = measurements_collection.find_one(
        {"user_id": current_user["user_id"]},
        sort=[("measured_at", -1)]
    )''',
    '''    measurement_list = get_supabase_list(supabase.table('measurements').select('*').eq('user_id', current_user["user_id"]).order('measured_at', desc=True).limit(1).execute())
    measurement = measurement_list[0] if measurement_list else None'''
)

# Line 1655: measurements find
content = content.replace(
    '''    measurements = list(measurements_collection.find(
        {"user_id": current_user["user_id"]}
    ).sort("measured_at", -1))''',
    '''    measurements = get_supabase_list(supabase.table('measurements').select('*').eq('user_id', current_user["user_id"]).order('measured_at', desc=True).execute())'''
)

# Line 1735: chat_history find
content = content.replace(
    '''    chats = list(chat_history_collection.find(
        {"user_id": current_user["user_id"]}
    ).sort("created_at", 1))''',
    '''    chats = get_supabase_list(supabase.table('chat_history').select('*').eq('user_id', current_user["user_id"]).order('created_at', desc=False).execute())'''
)

# Line 1922: meal_plans find
content = content.replace(
    '''        plans = list(meal_plans_collection.find(
            {"user_id": current_user["user_id"]}
        ).sort("created_at", -1))''',
    '''        plans = get_supabase_list(supabase.table('meal_plans').select('*').eq('user_id', current_user["user_id"]).order('created_at', desc=True).execute())'''
)

# Line 1949: meal_plans find_one
content = content.replace(
    '''        plan = meal_plans_collection.find_one(
            {"plan_id": plan_id, "user_id": current_user["user_id"]}
        )''',
    '''        plan = get_supabase_data(supabase.table('meal_plans').select('*').eq('plan_id', plan_id).eq('user_id', current_user["user_id"]).execute())'''
)

# Line 1996: meal_plans find_one (second occurrence)
content = content.replace(
    '''        plan = meal_plans_collection.find_one(
            {"plan_id": plan_id, "user_id": current_user["user_id"]}
        )''',
    '''        plan = get_supabase_data(supabase.table('meal_plans').select('*').eq('plan_id', plan_id).eq('user_id', current_user["user_id"]).execute())'''
)

# Line 2035: meal_plans update_one
content = content.replace(
    '''        meal_plans_collection.update_one(
            {"plan_id": plan_id, "user_id": current_user["user_id"]},
            {"$set": {"days": plan["days"]}}
        )''',
    '''        supabase.table('meal_plans').update({"days": plan["days"]}).eq('plan_id', plan_id).eq('user_id', current_user["user_id"]).execute()'''
)

# Line 2085: workout_sessions find_one for last_session
content = content.replace(
    '''        last_session_raw = workout_sessions_collection.find_one(
            {"user_id": current_user["user_id"], "exercise_id": exercise_id},
            sort=[("created_at", -1)]
        )''',
    '''        last_session_list = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user["user_id"]).eq('exercise_id', exercise_id).order('created_at', desc=True).limit(1).execute())
        last_session_raw = last_session_list[0] if last_session_list else None'''
)

# Line 2163: user_stats update for active_minutes
content = content.replace(
    '''                user_stats_collection.update_one(
                    {"user_id": current_user["user_id"], "date": today},
                    {"$set": {"active_minutes": new_active_minutes, "updated_at": datetime.utcnow().isoformat()}},
                    upsert=True
                )''',
    '''                supabase.table('user_stats').upsert({'user_id': current_user["user_id"], 'date': today, 'active_minutes': new_active_minutes, 'updated_at': datetime.utcnow().isoformat()}).execute()'''
)

# Line 2209: workout_sessions find with query
content = content.replace(
    '''        sessions = list(workout_sessions_collection.find(
            query
        ).sort("created_at", -1))''',
    '''        if "exercise_id" in query:
            sessions = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user["user_id"]).eq('exercise_id', query["exercise_id"]).order('created_at', desc=True).execute())
        else:
            sessions = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user["user_id"]).order('created_at', desc=True).execute())'''
)

# Line 2230: workout_sessions find_one
content = content.replace(
    '''        session = workout_sessions_collection.find_one(
            {"session_id": session_id, "user_id": current_user["user_id"]}
        )''',
    '''        session = get_supabase_data(supabase.table('workout_sessions').select('*').eq('session_id', session_id).eq('user_id', current_user["user_id"]).execute())'''
)

# Line 2310: workout_sessions update_one
content = content.replace(
    '''        workout_sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )''',
    '''        supabase.table('workout_sessions').update(update_data).eq('session_id', session_id).execute()'''
)

# Line 2316: workout_sessions find_one for updated_session
content = content.replace(
    '''        updated_session = workout_sessions_collection.find_one({"session_id": session_id})''',
    '''        updated_session = get_supabase_data(supabase.table('workout_sessions').select('*').eq('session_id', session_id).execute())'''
)

# Line 2338: workout_sessions find for history (limit 10)
content = content.replace(
    '''        sessions = list(workout_sessions_collection.find(
            {"user_id": current_user["user_id"], "exercise_id": exercise_id}
        ).sort("created_at", -1).limit(10))''',
    '''        sessions = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user["user_id"]).eq('exercise_id', exercise_id).order('created_at', desc=True).limit(10).execute())'''
)

# Line 2379: workout_sessions find for stats
content = content.replace(
    '''        sessions = list(workout_sessions_collection.find(
            {"user_id": current_user["user_id"], "exercise_id": exercise_id}
        ))''',
    '''        sessions = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user["user_id"]).eq('exercise_id', exercise_id).execute())'''
)

# Line 2461: workout_sessions find all
content = content.replace(
    '''        all_sessions = list(workout_sessions_collection.find(
            {"user_id": current_user["user_id"]}
        ))''',
    '''        all_sessions = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user["user_id"]).execute())'''
)

# Write the final file
write_file('/app/backend/server.py', content)

print("✅ Final Supabase conversion complete!")
print("📁 MongoDB backup: /app/backend/server_mongodb_backup_original.py")
print("📁 Active file: /app/backend/server.py (now using Supabase)")

# Verify
remaining = content.count('_collection.')
if remaining > 0:
    print(f"\n⚠️  WARNING: {remaining} '_collection.' references still remain!")
    print("   Please check manually")
else:
    print("\n✅ SUCCESS: No MongoDB references found!")
    print("   All operations now use Supabase with .eq() chaining")

print("\n📋 Next step: Restart backend")
print("   sudo supervisorctl restart backend")
