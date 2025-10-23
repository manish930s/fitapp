"""
Initialize Supabase tables for FitFlow application
Run this script once to create all necessary tables
"""
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL statements to create all tables
CREATE_TABLES_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    height FLOAT,
    weight FLOAT,
    activity_level TEXT DEFAULT 'moderate',
    goal_weight FLOAT,
    theme TEXT DEFAULT 'system',
    profile_picture TEXT,
    weight_unit TEXT DEFAULT 'kg',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Food scans table
CREATE TABLE IF NOT EXISTS food_scans (
    scan_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    food_name TEXT NOT NULL,
    calories FLOAT NOT NULL,
    protein FLOAT NOT NULL,
    carbs FLOAT NOT NULL,
    fat FLOAT NOT NULL,
    portion_size TEXT,
    image_base64 TEXT,
    scanned_at TIMESTAMP DEFAULT NOW()
);

-- User stats table
CREATE TABLE IF NOT EXISTS user_stats (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    steps INTEGER DEFAULT 0,
    calories_burned INTEGER DEFAULT 0,
    calories_consumed INTEGER DEFAULT 0,
    active_minutes INTEGER DEFAULT 0,
    water_intake INTEGER DEFAULT 0,
    sleep_hours FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Goals table
CREATE TABLE IF NOT EXISTS goals (
    goal_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    goal_type TEXT NOT NULL,
    target_value FLOAT NOT NULL,
    current_progress FLOAT DEFAULT 0,
    unit TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Measurements table
CREATE TABLE IF NOT EXISTS measurements (
    measurement_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    weight FLOAT,
    body_fat FLOAT,
    bmi FLOAT,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Chat history table
CREATE TABLE IF NOT EXISTS chat_history (
    message_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    language TEXT DEFAULT 'english',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Meal plans table
CREATE TABLE IF NOT EXISTS meal_plans (
    plan_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    duration INTEGER NOT NULL,
    start_date TEXT,
    dietary_preferences TEXT,
    allergies TEXT,
    calorie_target INTEGER,
    days JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Exercises table
CREATE TABLE IF NOT EXISTS exercises (
    exercise_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    target_muscles JSONB,
    instructions JSONB,
    tips JSONB,
    safety_tips JSONB,
    image_url TEXT
);

-- Workout sessions table
CREATE TABLE IF NOT EXISTS workout_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL REFERENCES exercises(exercise_id),
    sets JSONB NOT NULL,
    notes TEXT,
    duration_minutes INTEGER,
    total_volume FLOAT,
    max_weight FLOAT,
    max_reps INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_food_scans_user_id ON food_scans(user_id);
CREATE INDEX IF NOT EXISTS idx_food_scans_scanned_at ON food_scans(scanned_at);
CREATE INDEX IF NOT EXISTS idx_user_stats_user_id ON user_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_user_stats_date ON user_stats(date);
CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id);
CREATE INDEX IF NOT EXISTS idx_measurements_user_id ON measurements(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON meal_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id ON workout_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_exercise_id ON workout_sessions(exercise_id);
"""

def init_tables():
    """Initialize all Supabase tables"""
    try:
        print("🚀 Creating Supabase tables...")
        
        # Execute the SQL to create tables
        # Note: Supabase Python client doesn't directly support raw SQL execution
        # Tables should be created via Supabase Dashboard SQL Editor or via RPC
        
        print("✅ Tables creation SQL prepared.")
        print("\n⚠️  IMPORTANT: Please run the following SQL in your Supabase Dashboard:")
        print("    Go to: Dashboard → SQL Editor → New Query")
        print("    Copy and paste the SQL from CREATE_TABLES_SQL\n")
        print(CREATE_TABLES_SQL)
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    init_tables()
