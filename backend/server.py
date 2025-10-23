from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
import jwt
import bcrypt
import uuid
import base64
import json
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from email_service import email_service
from utils import generate_verification_token, verify_token, get_token_expiry_time

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase Connection
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# OpenAI API Configuration (using Emergent LLM Key)
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

security = HTTPBearer()

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


# Models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None  # in cm
    weight: Optional[float] = None  # in kg
    activity_level: Optional[str] = "moderate"  # sedentary, light, moderate, active, very_active
    goal_weight: Optional[float] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[str] = None
    goal_weight: Optional[float] = None
    theme: Optional[str] = "system"  # system, dark, light
    profile_picture: Optional[str] = None  # base64 encoded image
    weight_unit: Optional[str] = None  # kg or lbs

class FoodScanResult(BaseModel):
    food_name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    portion_size: str
    image_base64: str

class DailyStats(BaseModel):
    steps: int
    calories_burned: int
    calories_consumed: int
    active_minutes: int
    water_intake: int
    sleep_hours: float

class Goal(BaseModel):
    goal_type: str  # "weight_loss", "muscle_gain", "endurance", etc.
    target_value: float
    current_progress: float
    unit: str  # "kg", "lbs", "%", etc.

class Measurement(BaseModel):
    weight: Optional[float] = None
    body_fat: Optional[float] = None
    bmi: Optional[float] = None

class ChatMessage(BaseModel):
    message: str
    language: Optional[str] = "english"  # Language for response (english, hindi, marathi, etc.)

class MealPlanGenerate(BaseModel):
    duration: int  # 1, 3, 7, or 14 days
    dietary_preferences: Optional[str] = None  # "vegetarian", "vegan", "keto", etc.
    allergies: Optional[str] = None
    calorie_target: Optional[int] = None  # If None, use user's daily target

class MealPlanCreate(BaseModel):
    name: str
    duration: int
    start_date: str  # ISO format date
    days: List[dict]  # List of day objects with meals

class MealUpdate(BaseModel):
    name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None


class WorkoutSet(BaseModel):
    reps: int
    weight: float
    rpe: Optional[int] = None  # Rate of Perceived Exertion 1-10
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None

class WorkoutSessionCreate(BaseModel):
    exercise_id: str
    sets: List[WorkoutSet]
    notes: Optional[str] = None
    duration_minutes: Optional[int] = None  # Auto-tracked workout duration

class WorkoutSetUpdate(BaseModel):
    reps: Optional[int] = None
    weight: Optional[float] = None
    rpe: Optional[int] = None
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str) -> str:
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_jwt_token(token)
    user = get_supabase_data(supabase.table('users').select('*').eq('user_id', payload["user_id"]).execute())
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def calculate_daily_calories(weight: float, height: float, age: int, gender: str, activity_level: str, goal_weight: float = None) -> dict:
    """
    Calculate daily calorie requirements using Mifflin-St Jeor Equation
    BMR (men) = 10 × weight(kg) + 6.25 × height(cm) - 5 × age(years) + 5
    BMR (women) = 10 × weight(kg) + 6.25 × height(cm) - 5 × age(years) - 161
    """
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    # Activity multipliers
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)
    
    # Adjust for weight goal
    if goal_weight:
        if goal_weight < weight:  # Weight loss
            daily_calories = tdee - 500  # 500 calorie deficit
        elif goal_weight > weight:  # Weight gain
            daily_calories = tdee + 300  # 300 calorie surplus
        else:
            daily_calories = tdee  # Maintenance
    else:
        daily_calories = tdee
    
    return {
        "bmr": round(bmr, 2),
        "tdee": round(tdee, 2),
        "daily_target": round(daily_calories, 2)
    }

async def analyze_food_with_ai(image_base64: str) -> dict:
    """
    Analyze food image using OpenAI GPT-4o vision with Emergent LLM Key
    """
    try:
        # Create chat instance with Emergent LLM Key
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"food_analysis_{uuid.uuid4()}",
            system_message="You are a nutrition expert AI. Analyze food images and provide accurate nutritional information."
        ).with_model("openai", "gpt-4o")
        
        prompt = '''Analyze this food image and provide ONLY a JSON response with the following structure:
{
  "food_name": "name of the food",
  "calories": estimated total calories (number),
  "protein": grams of protein (number),
  "carbs": grams of carbohydrates (number),
  "fat": grams of fat (number),
  "portion_size": "description of portion size (e.g., '1 bowl', '2 slices')"
}

Provide realistic estimates based on the visible portion. Return ONLY valid JSON, no additional text.'''
        
        # Create image content from base64
        image_content = ImageContent(image_base64=image_base64)
        
        # Create user message with text and image
        user_message = UserMessage(
            text=prompt,
            file_contents=[image_content]
        )
        
        # Send message and get response
        response = await chat.send_message(user_message)
        
        # Debug: Print the raw response
        print(f"Raw AI response: '{response}'")
        print(f"Response type: {type(response)}")
        print(f"Response length: {len(response) if response else 0}")
        
        # Check if response is empty
        if not response or not response.strip():
            print("Empty response from AI - using fallback")
            return {
                "food_name": "Unknown Food Item",
                "calories": 150.0,
                "protein": 3.0,
                "carbs": 20.0,
                "fat": 5.0,
                "portion_size": "1 serving"
            }
        
        # Parse the JSON response
        content = response.strip()
        
        # Try to extract JSON from the response
        # Sometimes the model wraps JSON in markdown code blocks
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        # Parse the JSON response
        try:
            food_data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Content that failed to parse: '{content}'")
            # Return fallback data if JSON parsing fails
            return {
                "food_name": "Food Item",
                "calories": 100.0,
                "protein": 2.0,
                "carbs": 15.0,
                "fat": 3.0,
                "portion_size": "1 serving"
            }
        
        return {
            "food_name": food_data.get("food_name", "Unknown Food"),
            "calories": float(food_data.get("calories", 0)),
            "protein": float(food_data.get("protein", 0)),
            "carbs": float(food_data.get("carbs", 0)),
            "fat": float(food_data.get("fat", 0)),
            "portion_size": food_data.get("portion_size", "1 serving")
        }
    except Exception as e:
        print(f"Error analyzing food: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze food image: {str(e)}")


# Initialize workout exercises in database
def initialize_exercises():
    """Initialize predefined workout exercises if not already present"""
    exercises = [
        # CHEST EXERCISES
        {
            "exercise_id": "bench-press",
            "name": "Bench Press",
            "category": "Chest",
            "description": "A compound exercise that targets the chest, triceps, and shoulders",
            "target_muscles": ["Chest", "Triceps", "Shoulders"],
            "instructions": [
                "Lie flat on a bench with your feet firmly on the ground",
                "Grip the barbell slightly wider than shoulder-width",
                "Lower the bar to your mid-chest in a controlled manner",
                "Press the bar back up to the starting position"
            ],
            "tips": [
                "Keep your shoulder blades retracted and depressed",
                "Maintain a slight arch in your lower back",
                "Control the descent - don't bounce the bar off your chest"
            ],
            "safety_tips": [
                "Always use a spotter for heavy weights",
                "Warm up properly before lifting",
                "Don't lock out your elbows completely at the top"
            ],
            "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "incline-bench-press",
            "name": "Incline Bench Press",
            "category": "Chest",
            "description": "Targets the upper chest with an angled pressing motion",
            "target_muscles": ["Upper Chest", "Shoulders", "Triceps"],
            "instructions": [
                "Set bench to 30-45 degree incline",
                "Grip barbell slightly wider than shoulders",
                "Lower bar to upper chest",
                "Press back up to starting position"
            ],
            "tips": [
                "Keep elbows at 45-degree angle",
                "Press in slight arc toward face",
                "Maintain tight core throughout"
            ],
            "safety_tips": [
                "Don't set incline too steep (max 45 degrees)",
                "Keep feet flat on ground for stability",
                "Use spotter for heavy sets"
            ],
            "image_url": "https://images.unsplash.com/photo-1532029837206-abbe2b7620e3?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "dumbbell-fly",
            "name": "Dumbbell Fly",
            "category": "Chest",
            "description": "Isolation exercise for chest with full stretch and contraction",
            "target_muscles": ["Chest", "Shoulders"],
            "instructions": [
                "Lie on flat bench with dumbbells above chest",
                "Lower weights out to sides in wide arc",
                "Keep slight bend in elbows",
                "Bring weights back together above chest"
            ],
            "tips": [
                "Focus on chest stretch at bottom",
                "Control the weight - don't drop arms",
                "Squeeze chest at top of movement"
            ],
            "safety_tips": [
                "Don't go too heavy - focus on form",
                "Maintain slight elbow bend throughout",
                "Stop if you feel shoulder pain"
            ],
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "push-ups",
            "name": "Push-Ups",
            "category": "Chest",
            "description": "Bodyweight exercise building chest, triceps, and core strength",
            "target_muscles": ["Chest", "Triceps", "Shoulders", "Core"],
            "instructions": [
                "Start in plank position with hands shoulder-width",
                "Lower body until chest nearly touches floor",
                "Keep elbows at 45-degree angle",
                "Push back up to starting position"
            ],
            "tips": [
                "Keep body in straight line",
                "Engage core throughout movement",
                "Full range of motion for best results"
            ],
            "safety_tips": [
                "Don't let hips sag",
                "Keep neck neutral",
                "Modify on knees if needed"
            ],
            "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "cable-crossover",
            "name": "Cable Crossover",
            "category": "Chest",
            "description": "Cable exercise for complete chest development and peak contraction",
            "target_muscles": ["Chest", "Front Shoulders"],
            "instructions": [
                "Set pulleys to high position",
                "Grab handles and step forward",
                "Pull handles down and across body",
                "Squeeze chest at center"
            ],
            "tips": [
                "Lean forward slightly",
                "Focus on squeezing chest at peak",
                "Control the return motion"
            ],
            "safety_tips": [
                "Start with lighter weight",
                "Don't overstretch shoulders",
                "Maintain stable stance"
            ],
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=400&fit=crop"
        },
        
        # BACK EXERCISES
        {
            "exercise_id": "deadlift",
            "name": "Deadlift",
            "category": "Back",
            "description": "A full-body compound exercise emphasizing the posterior chain",
            "target_muscles": ["Lower Back", "Hamstrings", "Glutes", "Traps", "Forearms"],
            "instructions": [
                "Stand with feet hip-width apart, bar over mid-foot",
                "Bend down and grip the bar just outside your legs",
                "Keep your back straight and chest up",
                "Drive through your heels and extend your hips",
                "Stand up fully, then lower the bar with control"
            ],
            "tips": [
                "Keep the bar close to your body throughout",
                "Engage your lats to protect your lower back",
                "Think about pushing the floor away, not pulling the bar up"
            ],
            "safety_tips": [
                "Never round your lower back",
                "Don't jerk the weight off the floor",
                "Use proper form over heavy weight"
            ],
            "image_url": "https://images.unsplash.com/photo-1566241440091-ec10de8db2e1?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "barbell-row",
            "name": "Barbell Row",
            "category": "Back",
            "description": "A horizontal pulling exercise that builds back thickness",
            "target_muscles": ["Lats", "Rhomboids", "Traps", "Biceps"],
            "instructions": [
                "Bend forward at the hips with a flat back",
                "Grip the barbell with hands shoulder-width apart",
                "Pull the bar to your lower chest/upper abdomen",
                "Squeeze your shoulder blades together at the top",
                "Lower the bar with control"
            ],
            "tips": [
                "Keep your torso at about 45 degrees",
                "Lead with your elbows, not your hands",
                "Don't use momentum - control the weight"
            ],
            "safety_tips": [
                "Maintain a neutral spine throughout",
                "Don't round your lower back",
                "Avoid using too much body English"
            ],
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "pull-ups",
            "name": "Pull Ups",
            "category": "Back",
            "description": "A bodyweight exercise that builds back width and arm strength",
            "target_muscles": ["Lats", "Biceps", "Upper Back", "Core"],
            "instructions": [
                "Hang from a pull-up bar with hands shoulder-width apart",
                "Pull yourself up until your chin clears the bar",
                "Lower yourself back down with control",
                "Repeat for desired reps"
            ],
            "tips": [
                "Engage your core to prevent swinging",
                "Pull your elbows down and back",
                "Focus on using your back, not just your arms"
            ],
            "safety_tips": [
                "Don't kip or swing excessively",
                "Lower yourself fully for complete range of motion",
                "Use assistance bands if needed"
            ],
            "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "lat-pulldown",
            "name": "Lat Pulldown",
            "category": "Back",
            "description": "Machine exercise for building lat width and upper back strength",
            "target_muscles": ["Lats", "Biceps", "Rear Delts", "Traps"],
            "instructions": [
                "Sit at lat pulldown machine with knees secured",
                "Grab bar with wide overhand grip",
                "Pull bar down to upper chest",
                "Squeeze shoulder blades together",
                "Return to starting position with control"
            ],
            "tips": [
                "Lean back slightly during pull",
                "Focus on pulling elbows down and back",
                "Don't use momentum or body swing"
            ],
            "safety_tips": [
                "Don't pull bar behind neck",
                "Keep core engaged",
                "Use weight you can control"
            ],
            "image_url": "https://images.unsplash.com/photo-1584380931214-dbb5b72e7fd0?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "seated-cable-row",
            "name": "Seated Cable Row",
            "category": "Back",
            "description": "Horizontal pulling exercise for mid-back development",
            "target_muscles": ["Mid Back", "Lats", "Biceps", "Rear Delts"],
            "instructions": [
                "Sit at cable row machine with feet on platform",
                "Grab handle with both hands",
                "Pull handle to lower chest",
                "Squeeze shoulder blades together",
                "Return arms to extended position"
            ],
            "tips": [
                "Keep torso upright and stable",
                "Drive elbows back past body",
                "Maintain neutral spine"
            ],
            "safety_tips": [
                "Don't round lower back",
                "Control the weight on return",
                "Keep chest up throughout"
            ],
            "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "t-bar-row",
            "name": "T-Bar Row",
            "category": "Back",
            "description": "Angled rowing movement for overall back thickness",
            "target_muscles": ["Mid Back", "Lats", "Traps", "Biceps"],
            "instructions": [
                "Straddle T-bar with bent knees",
                "Grab handles with overhand grip",
                "Pull weight toward chest",
                "Squeeze back at top",
                "Lower with control"
            ],
            "tips": [
                "Keep back flat and chest up",
                "Pull with elbows, not hands",
                "Use full range of motion"
            ],
            "safety_tips": [
                "Don't round spine",
                "Start light to learn form",
                "Brace core throughout"
            ],
            "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400&h=400&fit=crop"
        },
        
        # LEG EXERCISES
        {
            "exercise_id": "squat",
            "name": "Squat",
            "category": "Legs",
            "description": "A fundamental lower body compound exercise targeting quads, hamstrings, and glutes",
            "target_muscles": ["Quadriceps", "Hamstrings", "Glutes", "Core"],
            "instructions": [
                "Stand with feet shoulder-width apart",
                "Keep your chest up and core tight",
                "Lower yourself by bending at the hips and knees",
                "Descend until thighs are parallel to the ground",
                "Push through your heels to return to standing"
            ],
            "tips": [
                "Keep your knees tracking over your toes",
                "Maintain a neutral spine throughout the movement",
                "Drive through your heels, not your toes"
            ],
            "safety_tips": [
                "Never let your knees cave inward",
                "Don't round your lower back",
                "Use a weight appropriate for your strength level"
            ],
            "image_url": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "leg-press",
            "name": "Leg Press",
            "category": "Legs",
            "description": "Machine exercise for overall leg development with back support",
            "target_muscles": ["Quadriceps", "Glutes", "Hamstrings"],
            "instructions": [
                "Sit in leg press machine with feet shoulder-width on platform",
                "Release safety locks",
                "Lower platform by bending knees to 90 degrees",
                "Press back up to starting position",
                "Don't lock knees at top"
            ],
            "tips": [
                "Keep lower back pressed against pad",
                "Push through entire foot, not just toes",
                "Control descent for better results"
            ],
            "safety_tips": [
                "Never lock knees fully",
                "Don't let lower back lift off pad",
                "Use appropriate weight"
            ],
            "image_url": "https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "leg-curl",
            "name": "Leg Curl",
            "category": "Legs",
            "description": "Isolation exercise targeting the hamstrings",
            "target_muscles": ["Hamstrings", "Calves"],
            "instructions": [
                "Lie face down on leg curl machine",
                "Place ankles under padded lever",
                "Curl legs up toward glutes",
                "Squeeze hamstrings at top",
                "Lower with control"
            ],
            "tips": [
                "Keep hips pressed down",
                "Full range of motion",
                "Don't use momentum"
            ],
            "safety_tips": [
                "Don't hyperextend knees",
                "Keep movement controlled",
                "Adjust pad to fit properly"
            ],
            "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "leg-extension",
            "name": "Leg Extension",
            "category": "Legs",
            "description": "Isolation exercise for quadriceps development",
            "target_muscles": ["Quadriceps"],
            "instructions": [
                "Sit in leg extension machine",
                "Place ankles under padded lever",
                "Extend legs until fully straight",
                "Squeeze quads at top",
                "Lower with control"
            ],
            "tips": [
                "Keep back against pad",
                "Control both up and down phases",
                "Squeeze at full extension"
            ],
            "safety_tips": [
                "Don't hyperextend knees",
                "Use moderate weight",
                "Stop if knee pain occurs"
            ],
            "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "lunges",
            "name": "Lunges",
            "category": "Legs",
            "description": "Unilateral leg exercise for balance and strength",
            "target_muscles": ["Quadriceps", "Glutes", "Hamstrings"],
            "instructions": [
                "Stand with feet hip-width apart",
                "Step forward with one leg",
                "Lower hips until both knees at 90 degrees",
                "Push back to starting position",
                "Alternate legs"
            ],
            "tips": [
                "Keep front knee over ankle",
                "Maintain upright torso",
                "Push through front heel"
            ],
            "safety_tips": [
                "Don't let front knee pass toes",
                "Keep core engaged",
                "Start with bodyweight"
            ],
            "image_url": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "bulgarian-split-squat",
            "name": "Bulgarian Split Squat",
            "category": "Legs",
            "description": "Single-leg exercise for quad and glute development",
            "target_muscles": ["Quadriceps", "Glutes", "Hamstrings"],
            "instructions": [
                "Place rear foot on bench behind you",
                "Front foot forward in lunge position",
                "Lower body by bending front knee",
                "Push back up through front heel",
                "Complete reps then switch legs"
            ],
            "tips": [
                "Keep torso upright",
                "Front knee tracks over toes",
                "Control the descent"
            ],
            "safety_tips": [
                "Start with bodyweight first",
                "Use bench at knee height",
                "Keep front knee stable"
            ],
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "calf-raises",
            "name": "Calf Raises",
            "category": "Legs",
            "description": "Isolation exercise for calf muscle development",
            "target_muscles": ["Calves"],
            "instructions": [
                "Stand with balls of feet on raised surface",
                "Lower heels below platform",
                "Rise up onto toes as high as possible",
                "Squeeze calves at top",
                "Lower with control"
            ],
            "tips": [
                "Full range of motion",
                "Pause at top for squeeze",
                "Keep knees slightly bent"
            ],
            "safety_tips": [
                "Hold onto support for balance",
                "Don't bounce at bottom",
                "Control the movement"
            ],
            "image_url": "https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400&h=400&fit=crop"
        },
        
        # SHOULDER EXERCISES
        {
            "exercise_id": "overhead-press",
            "name": "Overhead Press",
            "category": "Shoulders",
            "description": "A vertical pressing movement targeting the shoulders and triceps",
            "target_muscles": ["Shoulders", "Triceps", "Upper Chest", "Core"],
            "instructions": [
                "Stand with feet shoulder-width apart",
                "Hold the barbell at shoulder height",
                "Press the bar overhead until arms are fully extended",
                "Lower the bar back to shoulder height with control"
            ],
            "tips": [
                "Keep your core tight and glutes engaged",
                "Press the bar in a slight arc, not straight up",
                "Don't lean back excessively"
            ],
            "safety_tips": [
                "Avoid excessive lower back arching",
                "Start with lighter weights to master form",
                "Ensure full shoulder mobility before heavy pressing"
            ],
            "image_url": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "lateral-raise",
            "name": "Lateral Raise",
            "category": "Shoulders",
            "description": "Isolation exercise for side deltoid development",
            "target_muscles": ["Side Deltoids", "Traps"],
            "instructions": [
                "Stand with dumbbells at sides",
                "Raise arms out to sides until shoulder height",
                "Keep slight bend in elbows",
                "Lower with control"
            ],
            "tips": [
                "Lead with elbows, not hands",
                "Don't swing or use momentum",
                "Keep shoulders down"
            ],
            "safety_tips": [
                "Use lighter weight for proper form",
                "Don't raise above shoulder height",
                "Control the descent"
            ],
            "image_url": "https://images.unsplash.com/photo-1532029837206-abbe2b7620e3?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "front-raise",
            "name": "Front Raise",
            "category": "Shoulders",
            "description": "Isolation for front deltoid development",
            "target_muscles": ["Front Deltoids", "Upper Chest"],
            "instructions": [
                "Stand with dumbbells in front of thighs",
                "Raise arms straight in front to shoulder height",
                "Keep slight bend in elbows",
                "Lower back down with control"
            ],
            "tips": [
                "Keep core tight",
                "Don't swing weights up",
                "Maintain neutral wrist position"
            ],
            "safety_tips": [
                "Start light",
                "Don't raise above shoulder level",
                "Keep shoulders down"
            ],
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "rear-delt-fly",
            "name": "Rear Delt Fly",
            "category": "Shoulders",
            "description": "Isolation exercise for rear deltoid and upper back",
            "target_muscles": ["Rear Deltoids", "Upper Back"],
            "instructions": [
                "Bend forward at hips with dumbbells",
                "Raise arms out to sides in reverse fly motion",
                "Squeeze shoulder blades together",
                "Lower with control"
            ],
            "tips": [
                "Keep back flat",
                "Focus on rear delts, not traps",
                "Don't use momentum"
            ],
            "safety_tips": [
                "Maintain neutral spine",
                "Use lighter weights",
                "Keep slight elbow bend"
            ],
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "shrugs",
            "name": "Shrugs",
            "category": "Shoulders",
            "description": "Isolation exercise for trapezius development",
            "target_muscles": ["Traps", "Upper Back"],
            "instructions": [
                "Stand holding dumbbells or barbell",
                "Raise shoulders straight up toward ears",
                "Hold briefly at top",
                "Lower back down slowly"
            ],
            "tips": [
                "Don't roll shoulders",
                "Lift straight up and down",
                "Squeeze traps at top"
            ],
            "safety_tips": [
                "Don't use excessive weight",
                "Keep arms straight",
                "Control the movement"
            ],
            "image_url": "https://images.unsplash.com/photo-1566241440091-ec10de8db2e1?w=400&h=400&fit=crop"
        },
        
        # ARM EXERCISES
        {
            "exercise_id": "bicep-curl",
            "name": "Bicep Curl",
            "category": "Arms",
            "description": "Classic isolation exercise for biceps development",
            "target_muscles": ["Biceps", "Forearms"],
            "instructions": [
                "Stand with dumbbells at sides, palms forward",
                "Curl weights up toward shoulders",
                "Keep elbows stationary at sides",
                "Lower with control"
            ],
            "tips": [
                "Don't swing or use momentum",
                "Keep elbows pinned to sides",
                "Squeeze biceps at top"
            ],
            "safety_tips": [
                "Control the weight throughout",
                "Don't arch lower back",
                "Use full range of motion"
            ],
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "hammer-curl",
            "name": "Hammer Curl",
            "category": "Arms",
            "description": "Bicep curl variation targeting brachialis and forearms",
            "target_muscles": ["Biceps", "Brachialis", "Forearms"],
            "instructions": [
                "Stand with dumbbells at sides, palms facing in",
                "Curl weights up keeping neutral grip",
                "Keep elbows at sides",
                "Lower with control"
            ],
            "tips": [
                "Maintain neutral wrist throughout",
                "Don't swing weights",
                "Focus on controlled movement"
            ],
            "safety_tips": [
                "Keep elbows stationary",
                "Use appropriate weight",
                "Full range of motion"
            ],
            "image_url": "https://images.unsplash.com/photo-1532029837206-abbe2b7620e3?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "tricep-pushdown",
            "name": "Tricep Pushdown",
            "category": "Arms",
            "description": "Cable isolation exercise for triceps development",
            "target_muscles": ["Triceps"],
            "instructions": [
                "Stand at cable machine with rope or bar attachment",
                "Start with elbows at 90 degrees",
                "Push down until arms fully extended",
                "Return to starting position with control"
            ],
            "tips": [
                "Keep elbows pinned to sides",
                "Squeeze triceps at bottom",
                "Don't lean forward"
            ],
            "safety_tips": [
                "Keep core engaged",
                "Don't use too much weight",
                "Control the return phase"
            ],
            "image_url": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "dips",
            "name": "Dips",
            "category": "Arms",
            "description": "Bodyweight or weighted exercise for triceps and chest",
            "target_muscles": ["Triceps", "Chest", "Shoulders"],
            "instructions": [
                "Grip parallel bars with arms extended",
                "Lower body by bending elbows",
                "Descend until upper arms parallel to ground",
                "Push back up to starting position"
            ],
            "tips": [
                "Lean forward for more chest, upright for triceps",
                "Keep shoulders down",
                "Control the descent"
            ],
            "safety_tips": [
                "Don't go too deep if shoulder hurts",
                "Build up to weighted dips gradually",
                "Warm up shoulders first"
            ],
            "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "skull-crushers",
            "name": "Skull Crushers",
            "category": "Arms",
            "description": "Lying tricep extension for mass building",
            "target_muscles": ["Triceps"],
            "instructions": [
                "Lie on bench with barbell extended above chest",
                "Lower bar toward forehead by bending elbows",
                "Keep upper arms stationary",
                "Extend arms back to starting position"
            ],
            "tips": [
                "Keep elbows in, don't flare out",
                "Lower slowly and controlled",
                "Full extension at top"
            ],
            "safety_tips": [
                "Use spotter for heavy weight",
                "Don't go too heavy initially",
                "Control the weight"
            ],
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=400&fit=crop"
        },
        
        # CORE EXERCISES
        {
            "exercise_id": "plank",
            "name": "Plank",
            "category": "Core",
            "description": "Isometric core strengthening exercise",
            "target_muscles": ["Core", "Abs", "Lower Back"],
            "instructions": [
                "Start in forearm plank position",
                "Keep body in straight line from head to heels",
                "Hold position maintaining tight core",
                "Breathe normally throughout"
            ],
            "tips": [
                "Don't let hips sag",
                "Keep shoulders over elbows",
                "Squeeze glutes and core"
            ],
            "safety_tips": [
                "Don't hold breath",
                "Stop if lower back hurts",
                "Build up time gradually"
            ],
            "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "crunches",
            "name": "Crunches",
            "category": "Core",
            "description": "Classic abdominal exercise for upper abs",
            "target_muscles": ["Abs", "Core"],
            "instructions": [
                "Lie on back with knees bent, feet flat",
                "Place hands behind head",
                "Lift shoulders off ground using abs",
                "Lower back down with control"
            ],
            "tips": [
                "Focus on abs, not pulling neck",
                "Exhale on the way up",
                "Keep lower back on ground"
            ],
            "safety_tips": [
                "Don't pull on neck",
                "Keep chin away from chest",
                "Control the movement"
            ],
            "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "russian-twists",
            "name": "Russian Twists",
            "category": "Core",
            "description": "Rotational core exercise for obliques",
            "target_muscles": ["Obliques", "Abs", "Core"],
            "instructions": [
                "Sit with knees bent, feet off ground",
                "Lean back slightly maintaining straight back",
                "Rotate torso side to side",
                "Touch ground on each side"
            ],
            "tips": [
                "Keep core engaged throughout",
                "Move with control, not momentum",
                "Keep chest up"
            ],
            "safety_tips": [
                "Don't round spine",
                "Start without weight",
                "Keep movements controlled"
            ],
            "image_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "leg-raises",
            "name": "Leg Raises",
            "category": "Core",
            "description": "Lower ab exercise for core strength",
            "target_muscles": ["Lower Abs", "Hip Flexors"],
            "instructions": [
                "Lie flat on back with legs extended",
                "Place hands under glutes for support",
                "Raise legs up to 90 degrees",
                "Lower with control without touching ground"
            ],
            "tips": [
                "Keep lower back pressed to ground",
                "Control the descent",
                "Don't swing legs"
            ],
            "safety_tips": [
                "Bend knees if too difficult",
                "Keep core engaged",
                "Don't arch lower back"
            ],
            "image_url": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "cable-crunches",
            "name": "Cable Crunches",
            "category": "Core",
            "description": "Weighted ab exercise using cable machine",
            "target_muscles": ["Abs", "Core"],
            "instructions": [
                "Kneel at cable machine with rope attachment",
                "Hold rope at head level",
                "Crunch down bringing elbows toward knees",
                "Return to starting position with control"
            ],
            "tips": [
                "Focus on abs contracting",
                "Keep hips stationary",
                "Full range of motion"
            ],
            "safety_tips": [
                "Don't use excessive weight",
                "Keep movement controlled",
                "Don't pull with arms"
            ],
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=400&fit=crop"
        },
        
        # ADDITIONAL EXERCISES TO REACH 35+
        {
            "exercise_id": "chest-press",
            "name": "Chest Press",
            "category": "Chest",
            "description": "Machine-based chest exercise for controlled pressing motion",
            "target_muscles": ["Chest", "Triceps", "Shoulders"],
            "instructions": [
                "Sit at chest press machine with back against pad",
                "Grip handles at chest level",
                "Press handles forward until arms extended",
                "Return to starting position with control"
            ],
            "tips": [
                "Keep back pressed against pad",
                "Don't lock elbows completely",
                "Control both pressing and return phases"
            ],
            "safety_tips": [
                "Adjust seat height properly",
                "Use appropriate weight",
                "Keep core engaged"
            ],
            "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop"
        },
        {
            "exercise_id": "mountain-climbers",
            "name": "Mountain Climbers",
            "category": "Core",
            "description": "Dynamic core and cardio exercise with alternating leg movements",
            "target_muscles": ["Core", "Shoulders", "Legs"],
            "instructions": [
                "Start in plank position with hands under shoulders",
                "Bring one knee toward chest",
                "Quickly switch legs in running motion",
                "Maintain plank position throughout"
            ],
            "tips": [
                "Keep hips level",
                "Maintain steady rhythm",
                "Keep core tight throughout"
            ],
            "safety_tips": [
                "Don't let hips sag",
                "Keep hands firmly planted",
                "Start slow and build speed"
            ],
            "image_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=400&h=400&fit=crop"
        }
    ]
    
    # Insert exercises if they don't exist
    for exercise in exercises:
        if not get_supabase_data(supabase.table('exercises').select('*').eq('exercise_id', exercise["exercise_id"]).execute()):
            supabase.table('exercises').insert(exercise).execute()
    
    print(f"Initialized {len(exercises)} exercises in database")

# Initialize exercises on startup
initialize_exercises()

# Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "FitFlow API"}

@app.post("/api/auth/register")
async def register(user_data: UserRegister, background_tasks: BackgroundTasks, request: Request):
    # Check if user already exists
    existing_user = get_supabase_data(supabase.table('users').select('*').eq('email', user_data.email).execute())
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user_data.password)
    
    # Generate verification token
    verification_token = generate_verification_token(user_data.email)
    
    user = {
        "user_id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "password": hashed_pw,
        "age": user_data.age,
        "gender": user_data.gender,
        "height": user_data.height,
        "weight": user_data.weight,
        "activity_level": user_data.activity_level,
        "goal_weight": user_data.goal_weight,
        "email_verified": False,
        "verification_token": verification_token,
        "token_created_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        supabase.table('users').insert(user).execute()
    except Exception as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create user account")
    
    # Build verification link
    # Get base URL from request
    base_url = str(request.base_url).rstrip('/')
    verification_link = f"{base_url}/api/auth/verify-email?token={verification_token}"
    
    # Send verification email in background
    background_tasks.add_task(
        email_service.send_verification_email,
        user_email=user_data.email,
        verification_link=verification_link,
        user_name=user_data.name
    )
    
    return {
        "message": "Registration successful! Please check your email to verify your account.",
        "email": user_data.email,
        "requires_verification": True,
        "user_id": user_id
    }

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    user = get_supabase_data(supabase.table('users').select('*').eq('email', credentials.email).execute())
    
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if email is verified
    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=403, 
            detail="Please verify your email before logging in. Check your inbox for the verification link."
        )
    
    token = create_jwt_token(user["user_id"], user["email"])
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"]
        }
    }

@app.get("/api/auth/verify-email")
async def verify_email(token: str):
    """
    Verify email address using token from verification link.
    Redirects to frontend after verification.
    """
    # Extract email from token (validates expiry automatically - 24 hours)
    email = verify_token(token, max_age=86400)  # 86400 seconds = 24 hours
    
    if not email:
        # Return HTML response for expired/invalid token
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Verification Failed - Fitsani</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #0a0f1e 0%, #1a1f2e 100%);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        color: #ffffff;
                    }
                    .container {
                        background: #1a1f2e;
                        border-radius: 16px;
                        padding: 40px;
                        max-width: 500px;
                        text-align: center;
                        border: 2px solid #ff5757;
                        box-shadow: 0 8px 32px rgba(255, 87, 87, 0.2);
                    }
                    .icon {
                        font-size: 64px;
                        margin-bottom: 20px;
                    }
                    h1 {
                        color: #ff5757;
                        margin-bottom: 20px;
                        font-size: 28px;
                    }
                    p {
                        color: #b0b0b0;
                        line-height: 1.6;
                        margin-bottom: 30px;
                        font-size: 16px;
                    }
                    .button {
                        display: inline-block;
                        background: linear-gradient(135deg, #2dffc4 0%, #00d9a3 100%);
                        color: #0a0f1e;
                        padding: 14px 32px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 600;
                        transition: all 0.3s ease;
                    }
                    .button:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 6px 24px rgba(45, 255, 196, 0.4);
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">❌</div>
                    <h1>Verification Link Expired</h1>
                    <p>
                        This verification link has expired or is invalid. 
                        Verification links are valid for 24 hours for security reasons.
                    </p>
                    <p>
                        Please log in to your account and request a new verification link.
                    </p>
                    <a href="/" class="button">Go to Login</a>
                </div>
            </body>
            </html>
            """,
            status_code=400
        )
    
    # Find user by email
    user = get_supabase_data(supabase.table('users').select('*').eq('email', email).execute())
    
    if not user:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>User Not Found - Fitsani</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #0a0f1e 0%, #1a1f2e 100%);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        color: #ffffff;
                    }
                    .container {
                        background: #1a1f2e;
                        border-radius: 16px;
                        padding: 40px;
                        max-width: 500px;
                        text-align: center;
                        border: 2px solid #ff5757;
                    }
                    .icon { font-size: 64px; margin-bottom: 20px; }
                    h1 { color: #ff5757; margin-bottom: 20px; }
                    p { color: #b0b0b0; line-height: 1.6; }
                    .button {
                        display: inline-block;
                        background: linear-gradient(135deg, #2dffc4 0%, #00d9a3 100%);
                        color: #0a0f1e;
                        padding: 14px 32px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 600;
                        margin-top: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">⚠️</div>
                    <h1>User Not Found</h1>
                    <p>The account associated with this verification link could not be found.</p>
                    <a href="/" class="button">Go to Home</a>
                </div>
            </body>
            </html>
            """,
            status_code=404
        )
    
    # Check if already verified
    if user.get("email_verified"):
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Already Verified - Fitsani</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #0a0f1e 0%, #1a1f2e 100%);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        color: #ffffff;
                    }
                    .container {
                        background: #1a1f2e;
                        border-radius: 16px;
                        padding: 40px;
                        max-width: 500px;
                        text-align: center;
                        border: 2px solid #2dffc4;
                        box-shadow: 0 8px 32px rgba(45, 255, 196, 0.2);
                    }
                    .icon { font-size: 64px; margin-bottom: 20px; }
                    h1 { color: #2dffc4; margin-bottom: 20px; }
                    p { color: #b0b0b0; line-height: 1.6; margin-bottom: 30px; }
                    .button {
                        display: inline-block;
                        background: linear-gradient(135deg, #2dffc4 0%, #00d9a3 100%);
                        color: #0a0f1e;
                        padding: 14px 32px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 600;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">✅</div>
                    <h1>Already Verified</h1>
                    <p>Your email address has already been verified. You can log in to your account.</p>
                    <a href="/" class="button">Go to Login</a>
                </div>
            </body>
            </html>
            """
        )
    
    # Update user as verified
    try:
        supabase.table('users').update({
            "email_verified": True,
            "verification_token": None  # Clear the token after use
        }).eq('user_id', user['user_id']).execute()
        
        # Return success HTML page
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Email Verified - Fitsani</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #0a0f1e 0%, #1a1f2e 100%);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        color: #ffffff;
                    }}
                    .container {{
                        background: #1a1f2e;
                        border-radius: 16px;
                        padding: 40px;
                        max-width: 500px;
                        text-align: center;
                        border: 2px solid #2dffc4;
                        box-shadow: 0 8px 32px rgba(45, 255, 196, 0.3);
                    }}
                    .icon {{
                        font-size: 80px;
                        margin-bottom: 20px;
                        animation: bounce 1s ease-in-out;
                    }}
                    @keyframes bounce {{
                        0%, 100% {{ transform: translateY(0); }}
                        50% {{ transform: translateY(-20px); }}
                    }}
                    h1 {{
                        color: #2dffc4;
                        margin-bottom: 20px;
                        font-size: 32px;
                    }}
                    p {{
                        color: #b0b0b0;
                        line-height: 1.6;
                        margin-bottom: 30px;
                        font-size: 16px;
                    }}
                    .button {{
                        display: inline-block;
                        background: linear-gradient(135deg, #2dffc4 0%, #00d9a3 100%);
                        color: #0a0f1e;
                        padding: 16px 40px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 700;
                        font-size: 16px;
                        transition: all 0.3s ease;
                        box-shadow: 0 4px 16px rgba(45, 255, 196, 0.3);
                    }}
                    .button:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 6px 24px rgba(45, 255, 196, 0.5);
                    }}
                    .feature-list {{
                        background-color: rgba(45, 255, 196, 0.05);
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                        text-align: left;
                    }}
                    .feature-list li {{
                        margin: 10px 0;
                        color: #b0b0b0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">🎉</div>
                    <h1>Email Verified Successfully!</h1>
                    <p>
                        Welcome to Fitsani, {user['name']}! Your email address has been verified successfully.
                    </p>
                    <p>
                        You can now access all features of your Fitsani account:
                    </p>
                    <ul class="feature-list">
                        <li>🍎 <strong>AI Food Scanner</strong> - Track calories instantly</li>
                        <li>💪 <strong>Workout Tracker</strong> - Log your exercises</li>
                        <li>🤖 <strong>AI Fitness Coach</strong> - Get personalized advice</li>
                        <li>📊 <strong>Progress Dashboard</strong> - Monitor your journey</li>
                        <li>🥗 <strong>AI Meal Planner</strong> - Custom meal plans</li>
                    </ul>
                    <a href="/" class="button">Login to Your Account →</a>
                </div>
                <script>
                    // Auto-redirect to login page after 5 seconds
                    setTimeout(() => {{
                        window.location.href = '/';
                    }}, 5000);
                </script>
            </body>
            </html>
            """
        )
        
    except Exception as e:
        print(f"Error verifying email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify email")

@app.post("/api/auth/resend-verification")
async def resend_verification(email: EmailStr, background_tasks: BackgroundTasks, request: Request):
    """
    Resend verification email for users who didn't receive it.
    """
    # Find user by email
    user = get_supabase_data(supabase.table('users').select('*').eq('email', email).execute())
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already verified
    if user.get("email_verified"):
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate new verification token
    new_token = generate_verification_token(email)
    
    # Update user with new token
    try:
        supabase.table('users').update({
            "verification_token": new_token,
            "token_created_at": datetime.utcnow().isoformat()
        }).eq('user_id', user['user_id']).execute()
    except Exception as e:
        print(f"Error updating verification token: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate new verification link")
    
    # Build verification link
    base_url = str(request.base_url).rstrip('/')
    verification_link = f"{base_url}/api/auth/verify-email?token={new_token}"
    
    # Send verification email in background
    background_tasks.add_task(
        email_service.send_verification_email,
        user_email=email,
        verification_link=verification_link,
        user_name=user['name']
    )
    
    return {
        "message": "Verification email has been resent. Please check your inbox.",
        "email": email
    }


@app.get("/api/user/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    daily_calories = None
    if all([current_user.get('weight'), current_user.get('height'), current_user.get('age'), current_user.get('gender')]):
        daily_calories = calculate_daily_calories(
            current_user['weight'], current_user['height'], current_user['age'],
            current_user['gender'], current_user.get('activity_level', 'moderate'),
            current_user.get('goal_weight')
        )
    
    return {
        "user_id": current_user["user_id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "age": current_user.get("age"),
        "gender": current_user.get("gender"),
        "height": current_user.get("height"),
        "weight": current_user.get("weight"),
        "activity_level": current_user.get("activity_level"),
        "goal_weight": current_user.get("goal_weight"),
        "daily_calories": daily_calories,
        "profile_picture": current_user.get("profile_picture"),
        "weight_unit": current_user.get("weight_unit", "kg")
    }

@app.put("/api/user/profile")
async def update_profile(profile_data: UserProfile, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
    
    if update_data:
        supabase.table('users').update(update_data).eq('user_id', current_user["user_id"]).execute()
    
    return {"message": "Profile updated successfully"}

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@app.put("/api/user/password")
async def change_password(password_data: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Change user password"""
    # Verify current password
    user = get_supabase_data(supabase.table('users').select('*').eq('user_id', current_user["user_id"]).execute())
    if not user or not bcrypt.checkpw(password_data.current_password.encode('utf-8'), user['password'].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash new password
    hashed_password = bcrypt.hashpw(password_data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update password
    supabase.table('users').update({"password": hashed_password}).eq('user_id', current_user["user_id"]).execute()
    
    return {"message": "Password changed successfully"}

@app.delete("/api/user/account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Delete user account and all associated data"""
    user_id = current_user["user_id"]
    
    # Delete user data from all collections
    supabase.table('users').delete().eq('user_id', user_id).execute()
    supabase.table('food_scans').delete().eq('user_id', user_id).execute()
    supabase.table('user_stats').delete().eq('user_id', user_id).execute()
    supabase.table('goals').delete().eq('user_id', user_id).execute()
    supabase.table('measurements').delete().eq('user_id', user_id).execute()
    supabase.table('chat_history').delete().eq('user_id', user_id).execute()
    
    return {"message": "Account deleted successfully"}

@app.post("/api/food/scan")
async def scan_food(image: str = Form(...), current_user: dict = Depends(get_current_user)):
    """
    Scan food image and analyze nutritional content
    Expected format: base64 encoded image string
    """
    try:
        # Remove data URL prefix if present
        if 'base64,' in image:
            image_base64 = image.split('base64,')[1]
        else:
            image_base64 = image
        
        # Analyze food with AI
        analysis_result = await analyze_food_with_ai(image_base64)
        
        # Store the scan result
        scan_id = str(uuid.uuid4())
        scan_data = {
            "scan_id": scan_id,
            "user_id": current_user["user_id"],
            "food_name": analysis_result["food_name"],
            "calories": analysis_result["calories"],
            "protein": analysis_result["protein"],
            "carbs": analysis_result["carbs"],
            "fat": analysis_result["fat"],
            "portion_size": analysis_result["portion_size"],
            "image_base64": image_base64,
            "scanned_at": datetime.utcnow().isoformat()
        }
        
        supabase.table('food_scans').insert(scan_data).execute()
        
        # AUTO-TRACK: Update daily calories consumed
        today = datetime.utcnow().date().isoformat()
        stats = get_supabase_data(supabase.table('user_stats').select('*').eq('user_id', current_user["user_id"]).eq('date', today).execute())
        
        if stats:
            # Increment calories_consumed
            new_calories = stats.get("calories_consumed", 0) + analysis_result["calories"]
            supabase.table('user_stats').update({"calories_consumed": new_calories, "updated_at": datetime.utcnow().isoformat()}).eq('user_id', current_user["user_id"]).eq('date', today).execute()
        else:
            # Create new stats entry
            supabase.table('user_stats').insert({
                "user_id": current_user["user_id"],
                "date": today,
                "steps": 0,
                "calories_burned": 0,
                "calories_consumed": analysis_result["calories"],
                "active_minutes": 0,
                "water_intake": 0,
                "sleep_hours": 0,
                "updated_at": datetime.utcnow().execute().isoformat()
            })
        
        return {
            "scan_id": scan_id,
            "food_name": analysis_result["food_name"],
            "calories": analysis_result["calories"],
            "protein": analysis_result["protein"],
            "carbs": analysis_result["carbs"],
            "fat": analysis_result["fat"],
            "portion_size": analysis_result["portion_size"],
            "auto_tracked": True  # Flag to show toast notification
        }
    except Exception as e:
        print(f"Error in scan_food: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/food/history")
async def get_food_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    scans = get_supabase_list(supabase.table('food_scans').select('*').eq('user_id', current_user["user_id"]).order('scanned_at', desc=True).limit(limit).execute())
    
    # Format the response
    history = []
    for scan in scans:
        history.append({
            "scan_id": scan["scan_id"],
            "food_name": scan["food_name"],
            "calories": scan["calories"],
            "protein": scan["protein"],
            "carbs": scan["carbs"],
            "fat": scan["fat"],
            "portion_size": scan["portion_size"],
            "image_base64": scan["image_base64"],
            "scanned_at": scan["scanned_at"]
        })
    
    return {"history": history}

@app.get("/api/food/today")
async def get_today_food(current_user: dict = Depends(get_current_user)):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    scans = get_supabase_list(supabase.table('food_scans').select('*').eq('user_id', current_user["user_id"]).gte('scanned_at', today_start.isoformat()).order('scanned_at', desc=True).execute())
    
    total_calories = sum(scan["calories"] for scan in scans)
    total_protein = sum(scan["protein"] for scan in scans)
    total_carbs = sum(scan["carbs"] for scan in scans)
    total_fat = sum(scan["fat"] for scan in scans)
    
    return {
        "total_calories": total_calories,
        "total_protein": total_protein,
        "total_carbs": total_carbs,
        "total_fat": total_fat,
        "meal_count": len(scans)
    }

@app.delete("/api/food/scan/{scan_id}")
async def delete_food_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a food scan by scan_id
    """
    result = supabase.table('food_scans').delete().eq('scan_id', scan_id).eq('user_id', current_user["user_id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Food scan not found")
    
    return {"message": "Food scan deleted successfully"}

@app.post("/api/stats/daily")
async def update_daily_stats(stats: DailyStats, current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().date().isoformat()
    
    stats_data = {
        "user_id": current_user["user_id"],
        "date": today,
        "steps": stats.steps,
        "calories_burned": stats.calories_burned,
        "calories_consumed": stats.calories_consumed,
        "active_minutes": stats.active_minutes,
        "water_intake": stats.water_intake,
        "sleep_hours": stats.sleep_hours,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    supabase.table('user_stats').upsert({'user_id': current_user["user_id"], 'date': today, **stats_data}).execute()
    
    return {"message": "Daily stats updated successfully"}

@app.get("/api/stats/daily")
async def get_daily_stats(current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().date().isoformat()
    
    stats = get_supabase_data(supabase.table('user_stats').select('*').eq('user_id', current_user["user_id"]).eq('date', today).execute())
    
    if not stats:
        return {
            "steps": 0,
            "calories_burned": 0,
            "calories_consumed": 0,
            "active_minutes": 0,
            "water_intake": 0,
            "sleep_hours": 0
        }
    
    return {
        "steps": stats.get("steps", 0),
        "calories_burned": stats.get("calories_burned", 0),
        "calories_consumed": stats.get("calories_consumed", 0),
        "active_minutes": stats.get("active_minutes", 0),
        "water_intake": stats.get("water_intake", 0),
        "sleep_hours": stats.get("sleep_hours", 0)
    }


@app.patch("/api/stats/daily/increment")
async def increment_daily_stats(
    field: str = Form(...),
    amount: int = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Increment specific daily stat fields (steps, water_intake)"""
    today = datetime.utcnow().date().isoformat()
    
    # Validate field
    allowed_fields = ["steps", "water_intake"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"Field must be one of: {allowed_fields}")
    
    # Get or create today's stats
    stats = get_supabase_data(supabase.table('user_stats').select('*').eq('user_id', current_user["user_id"]).eq('date', today).execute())
    
    if not stats:
        # Create new stats entry
        stats_data = {
            "user_id": current_user["user_id"],
            "date": today,
            "steps": 0,
            "calories_burned": 0,
            "calories_consumed": 0,
            "active_minutes": 0,
            "water_intake": 0,
            "sleep_hours": 0,
            "updated_at": datetime.utcnow().isoformat()
        }
        stats_data[field] = amount
        supabase.table('user_stats').insert(stats_data).execute()
        new_value = amount
    else:
        # Increment existing value
        current_value = stats.get(field, 0)
        new_value = current_value + amount
        supabase.table('user_stats').update({field: new_value, "updated_at": datetime.utcnow().isoformat()}).eq('user_id', current_user["user_id"]).eq('date', today).execute()
    
    return {
        "message": f"{field} updated successfully",
        "field": field,
        "new_value": new_value
    }

@app.get("/api/stats/streak")
async def get_streak(current_user: dict = Depends(get_current_user)):
    # Get user's activity history
    stats = get_supabase_list(supabase.table('user_stats').select('*').eq('user_id', current_user["user_id"]).order('date', desc=True).execute())
    
    if not stats:
        return {"streak_days": 0}
    
    # Calculate streak
    streak = 0
    today = datetime.utcnow().date()
    
    for stat in stats:
        stat_date = datetime.fromisoformat(stat["date"]).date()
        days_diff = (today - stat_date).days
        
        if days_diff == streak:
            streak += 1
        else:
            break
    
    return {"streak_days": streak}

# Goals Management
@app.post("/api/goals")
async def create_goal(goal: Goal, current_user: dict = Depends(get_current_user)):
    goal_id = str(uuid.uuid4())
    goal_data = {
        "goal_id": goal_id,
        "user_id": current_user["user_id"],
        "goal_type": goal.goal_type,
        "target_value": goal.target_value,
        "current_progress": goal.current_progress,
        "unit": goal.unit,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table('goals').insert(goal_data).execute()
    return {"message": "Goal created successfully", "goal_id": goal_id}

@app.get("/api/goals")
async def get_goals(current_user: dict = Depends(get_current_user)):
    goals = get_supabase_list(supabase.table('goals').select('*').eq('user_id', current_user['user_id']).execute())
    return {"goals": goals}

@app.put("/api/goals/{goal_id}")
async def update_goal(goal_id: str, goal: Goal, current_user: dict = Depends(get_current_user)):
    result = supabase.table('goals').update({'current_progress': goal.current_progress}).eq('goal_id', goal_id).eq('user_id', current_user['user_id']).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Goal updated successfully"}

# Measurements Management
@app.post("/api/measurements")
async def add_measurement(measurement: Measurement, current_user: dict = Depends(get_current_user)):
    measurement_id = str(uuid.uuid4())
    measurement_data = {
        "measurement_id": measurement_id,
        "user_id": current_user["user_id"],
        "weight": measurement.weight,
        "body_fat": measurement.body_fat,
        "bmi": measurement.bmi,
        "date": datetime.utcnow().isoformat()
    }
    supabase.table('measurements').insert(measurement_data).execute()
    return {"message": "Measurement added successfully", "measurement_id": measurement_id}

@app.get("/api/measurements/latest")
async def get_latest_measurement(current_user: dict = Depends(get_current_user)):
    measurement_list = get_supabase_list(supabase.table('measurements').select('*').eq('user_id', current_user['user_id']).order('recorded_at', desc=True).limit(1).execute())
    measurement = measurement_list[0] if measurement_list else None
    if not measurement:
        return {"measurement": None}
    return {"measurement": measurement}

@app.get("/api/measurements/history")
async def get_measurements_history(limit: int = 30, current_user: dict = Depends(get_current_user)):
    measurements = get_supabase_list(supabase.table('measurements').select('*').eq('user_id', current_user['user_id']).order('measured_at', desc=True).execute())
    return {"measurements": measurements}

# AI Fitness Coach Chatbot
@app.post("/api/chat/fitness")
async def chat_with_fitness_coach(chat: ChatMessage, current_user: dict = Depends(get_current_user)):
    """Chat with AI Fitness Coach using OpenAI with multilingual support"""
    try:
        # Get user profile for context
        user = current_user
        user_name = user.get('name', 'Unknown')
        user_age = user.get('age', 'N/A')
        user_gender = user.get('gender', 'N/A')
        user_weight = user.get('weight', 'N/A')
        user_height = user.get('height', 'N/A')
        user_goal_weight = user.get('goal_weight', 'N/A')
        user_activity = user.get('activity_level', 'N/A')
        
        # Build system message
        system_content = "You are FitFlow's AI Fitness Coach. You provide personalized fitness advice, workout recommendations, nutrition guidance, and motivation.\n\n"
        system_content += "User Profile:\n"
        system_content += f"- Name: {user_name}\n"
        system_content += f"- Age: {user_age} years\n"
        system_content += f"- Gender: {user_gender}\n"
        system_content += f"- Weight: {user_weight} kg\n"
        system_content += f"- Height: {user_height} cm\n"
        system_content += f"- Goal Weight: {user_goal_weight} kg\n"
        system_content += f"- Activity Level: {user_activity}\n\n"
        system_content += "Guidelines:\n"
        system_content += "- Provide actionable, science-based fitness advice\n"
        system_content += "- Be encouraging and motivational\n"
        system_content += "- Keep responses concise and easy to understand\n"
        system_content += "- Tailor advice to the user's profile and goals\n"
        system_content += "- Suggest specific exercises, meal ideas, or habits when appropriate\n"
        system_content += "- If asked about medical concerns, recommend consulting a healthcare professional"
        
        # Add language instruction if needed
        if chat.language and chat.language.lower() != "english":
            lang_upper = chat.language.upper()
            system_content += f"\n\nIMPORTANT: Respond in {lang_upper} language. Translate all your responses to {chat.language}."
        
        # Use session_id based on user_id for persistent chat history
        session_id = f"fitness_coach_{user['user_id']}"
        
        # Create chat instance with Emergent LLM Key
        llm_chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_content
        ).with_model("openai", "gpt-4o")
        
        # Create user message
        user_msg = UserMessage(text=chat.message)
        
        # Send message and get response
        assistant_message = await llm_chat.send_message(user_msg)
        
        # Save chat to history
        supabase.table('chat_history').insert({
            "chat_id": str(uuid.uuid4().execute()),
            "user_id": user["user_id"],
            "user_message": chat.message,
            "assistant_message": assistant_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "message": assistant_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.get("/api/chat/history")
async def get_chat_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get chat history"""
    chats = get_supabase_list(supabase.table('chat_history').select('*').eq('user_id', current_user['user_id']).order('created_at', desc=False).execute())
    return {"chats": list(reversed(chats))}

# ===== MEAL PLAN ENDPOINTS =====

@app.post("/api/mealplan/generate")
async def generate_meal_plan(plan_request: MealPlanGenerate, current_user: dict = Depends(get_current_user)):
    """Generate AI-powered meal plan"""
    try:
        user = get_supabase_data(supabase.table('users').select('*').eq('user_id', current_user["user_id"]).execute())
        
        # Calculate calorie target if not provided
        calorie_target = plan_request.calorie_target
        if not calorie_target:
            if all([user.get('weight'), user.get('height'), user.get('age'), user.get('gender')]):
                daily_calories = calculate_daily_calories(
                    user['weight'], user['height'], user['age'],
                    user['gender'], user.get('activity_level', 'moderate'),
                    user.get('goal_weight')
                )
                calorie_target = int(daily_calories['daily_target'])
            else:
                calorie_target = 2000  # Default fallback
        
        # Prepare AI prompt
        prompt = f"""Create a {plan_request.duration}-day meal plan for a person with the following details:
- Daily calorie target: {calorie_target} kcal
- Dietary preferences: {plan_request.dietary_preferences or 'None'}
- Allergies: {plan_request.allergies or 'None'}

For each day, provide meals for these categories:
1. Breakfast
2. Morning Snack
3. Lunch
4. Afternoon Snack
5. Dinner

For each meal, include:
- Meal name
- Calories (kcal)
- Protein (g)
- Carbs (g)
- Fat (g)
- Brief description
- Key ingredients (list)

Return the response in this exact JSON format:
{{
  "days": [
    {{
      "day_number": 1,
      "meals": {{
        "breakfast": {{"name": "...", "calories": 350, "protein": 15, "carbs": 45, "fat": 10, "description": "...", "ingredients": ["..."]}}
        "morning_snack": {{"name": "...", "calories": 150, "protein": 5, "carbs": 20, "fat": 5, "description": "...", "ingredients": ["..."]}},
        "lunch": {{"name": "...", "calories": 450, "protein": 25, "carbs": 50, "fat": 15, "description": "...", "ingredients": ["..."]}},
        "afternoon_snack": {{"name": "...", "calories": 150, "protein": 5, "carbs": 20, "fat": 5, "description": "...", "ingredients": ["..."]}},
        "dinner": {{"name": "...", "calories": 400, "protein": 30, "carbs": 40, "fat": 12, "description": "...", "ingredients": ["..."]}}
      }}
    }}
  ]
}}

Make sure the total daily calories are close to {calorie_target} kcal. Return ONLY the JSON, no additional text."""
        
        # Call AI using Emergent LLM
        llm_chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"meal_plan_{uuid.uuid4()}",
            system_message="You are a nutrition expert AI that creates detailed meal plans based on user requirements."
        ).with_model("openai", "gpt-4o")
        
        user_msg = UserMessage(text=prompt)
        assistant_message = await llm_chat.send_message(user_msg)
        
        # Parse AI response
        try:
            # Try to extract JSON from response
            response_text = assistant_message.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            meal_plan_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            # Fallback: try to find JSON in the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    meal_plan_data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    print(f"Failed to parse AI response: {response_text[:500]}")
                    raise HTTPException(status_code=500, detail=f"Failed to parse AI response as JSON: {str(e)}")
            else:
                print(f"No JSON found in AI response: {response_text[:500]}")
                raise HTTPException(status_code=500, detail="No JSON found in AI response")
        
        # Calculate daily totals for each day
        for day in meal_plan_data["days"]:
            meals = day["meals"]
            day["totals"] = {
                "calories": sum(meal["calories"] for meal in meals.values()),
                "protein": sum(meal["protein"] for meal in meals.values()),
                "carbs": sum(meal["carbs"] for meal in meals.values()),
                "fat": sum(meal["fat"] for meal in meals.values())
            }
        
        # Save meal plan to database
        plan_id = str(uuid.uuid4())
        start_date = datetime.utcnow().isoformat()
        
        meal_plan = {
            "plan_id": plan_id,
            "user_id": current_user["user_id"],
            "name": f"{plan_request.duration}-Day AI Meal Plan",
            "duration": plan_request.duration,
            "start_date": start_date,
            "created_at": datetime.utcnow().isoformat(),
            "type": "ai_generated",
            "dietary_preferences": plan_request.dietary_preferences,
            "allergies": plan_request.allergies,
            "calorie_target": calorie_target,
            "days": meal_plan_data["days"]
        }
        
        supabase.table('meal_plans').insert(meal_plan).execute()
        
        return {
            "plan_id": plan_id,
            "name": meal_plan["name"],
            "duration": plan_request.duration,
            "start_date": start_date,
            "days": meal_plan_data["days"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Meal plan generation error: {str(e)}")

@app.post("/api/mealplan/create")
async def create_meal_plan(plan: MealPlanCreate, current_user: dict = Depends(get_current_user)):
    """Create a manual meal plan"""
    try:
        plan_id = str(uuid.uuid4())
        
        # Calculate daily totals for each day
        for day in plan.days:
            if "meals" in day:
                meals = day["meals"]
                day["totals"] = {
                    "calories": sum(meal.get("calories", 0) for meal in meals.values() if isinstance(meal, dict)),
                    "protein": sum(meal.get("protein", 0) for meal in meals.values() if isinstance(meal, dict)),
                    "carbs": sum(meal.get("carbs", 0) for meal in meals.values() if isinstance(meal, dict)),
                    "fat": sum(meal.get("fat", 0) for meal in meals.values() if isinstance(meal, dict))
                }
        
        meal_plan = {
            "plan_id": plan_id,
            "user_id": current_user["user_id"],
            "name": plan.name,
            "duration": plan.duration,
            "start_date": plan.start_date,
            "created_at": datetime.utcnow().isoformat(),
            "type": "manual",
            "days": plan.days
        }
        
        supabase.table('meal_plans').insert(meal_plan).execute()
        
        return {
            "plan_id": plan_id,
            "name": plan.name,
            "duration": plan.duration,
            "start_date": plan.start_date,
            "days": plan.days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Meal plan creation error: {str(e)}")

@app.get("/api/mealplan/list")
async def get_meal_plans(current_user: dict = Depends(get_current_user)):
    """Get all meal plans for user"""
    try:
        plans = get_supabase_list(supabase.table('meal_plans').select('*').eq('user_id', current_user['user_id']).order('created_at', desc=True).execute())
        
        # Return summary info only (without full day details)
        plans_summary = []
        for plan in plans:
            plans_summary.append({
                "plan_id": plan["plan_id"],
                "name": plan["name"],
                "duration": plan["duration"],
                "start_date": plan["start_date"],
                "created_at": plan["created_at"],
                "type": plan.get("type", "manual"),
                "calorie_target": plan.get("calorie_target")
            })
        
        return {"plans": plans_summary}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching meal plans: {str(e)}")

@app.get("/api/mealplan/{plan_id}")
async def get_meal_plan(plan_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific meal plan with full details"""
    try:
        plan = get_supabase_data(supabase.table('meal_plans').select('*').eq('plan_id', plan_id).eq('user_id', current_user['user_id']).execute())
        
        if not plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        return plan
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching meal plan: {str(e)}")

@app.delete("/api/mealplan/{plan_id}")
async def delete_meal_plan(plan_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a meal plan"""
    try:
        result = supabase.table('meal_plans').delete().eq('plan_id', plan_id).eq('user_id', current_user["user_id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        return {"message": "Meal plan deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting meal plan: {str(e)}")

@app.put("/api/mealplan/{plan_id}/day/{day_number}/meal")
async def update_meal(
    plan_id: str, 
    day_number: int, 
    meal_category: str,
    meal: MealUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a specific meal in a meal plan"""
    try:
        # Validate meal category
        valid_categories = ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner"]
        if meal_category not in valid_categories:
            raise HTTPException(status_code=400, detail=f"Invalid meal category. Must be one of: {', '.join(valid_categories)}")
        
        # Find the meal plan
        plan = get_supabase_data(supabase.table('meal_plans').select('*').eq('plan_id', plan_id).eq('user_id', current_user['user_id']).execute())
        
        if not plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        # Find the day and update the meal
        day_found = False
        for day in plan["days"]:
            # Support both 'day' and 'day_number' field names for compatibility
            current_day_num = day.get("day_number") or day.get("day")
            if current_day_num == day_number:
                day_found = True
                day["meals"][meal_category] = {
                    "name": meal.name,
                    "calories": meal.calories,
                    "protein": meal.protein,
                    "carbs": meal.carbs,
                    "fat": meal.fat,
                    "description": meal.description,
                    "ingredients": meal.ingredients
                }
                
                # Recalculate daily totals
                meals = day["meals"]
                day["totals"] = {
                    "calories": sum(m.get("calories", 0) for m in meals.values() if isinstance(m, dict)),
                    "protein": sum(m.get("protein", 0) for m in meals.values() if isinstance(m, dict)),
                    "carbs": sum(m.get("carbs", 0) for m in meals.values() if isinstance(m, dict)),
                    "fat": sum(m.get("fat", 0) for m in meals.values() if isinstance(m, dict))
                }
                break
        
        if not day_found:
            raise HTTPException(status_code=404, detail=f"Day {day_number} not found in meal plan")
        
        # Update the meal plan in database
        supabase.table('meal_plans').update({"days": plan["days"]}).eq('plan_id', plan_id).eq('user_id', current_user["user_id"]).execute()
        
        return {"message": "Meal updated successfully", "day": day}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating meal: {str(e)}")

# ===== WORKOUT TRACKING ENDPOINTS =====

@app.get("/api/workouts/exercises")
async def get_exercises(
    category: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all workout exercises, optionally filtered by category"""
    try:
        current_user = decode_jwt_token(credentials.credentials)
        
        # Build query
        query = {}
        if category and category.lower() != 'all':
            query["category"] = {"$regex": f"^{category}$", "$options": "i"}
        
        exercises = get_supabase_list(supabase.table('exercises').select('*').execute())
        return {"exercises": exercises}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching exercises: {str(e)}")

@app.get("/api/workouts/exercises/{exercise_id}")
async def get_exercise_detail(
    exercise_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get detailed information about a specific exercise"""
    try:
        current_user = decode_jwt_token(credentials.credentials)
        
        exercise = get_supabase_data(supabase.table('exercises').select('*').eq('exercise_id', exercise_id).execute())
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        # Get user's last workout for this exercise (auto-suggestion feature)
        last_session_list = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user['user_id']).eq('exercise_id', exercise_id).order('created_at', desc=True).limit(1).execute())
        last_session_raw = last_session_list[0] if last_session_list else None
        
        # Format last_session for auto-suggestion (simplified structure)
        if last_session_raw:
            # Calculate max_weight from sets
            sets = last_session_raw.get("sets", [])
            max_weight = max([s.get("weight", 0) for s in sets]) if sets else 0
            
            last_session = {
                "exercise_id": last_session_raw.get("exercise_id"),
                "sets": last_session_raw.get("sets", []),
                "total_volume": last_session_raw.get("total_volume", 0),
                "max_weight": max_weight
            }
        else:
            last_session = None
        
        exercise["last_session"] = last_session
        return exercise
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching exercise: {str(e)}")

@app.post("/api/workouts/sessions")
async def create_workout_session(
    session_data: WorkoutSessionCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new workout session with sets"""
    try:
        current_user = decode_jwt_token(credentials.credentials)
        
        # Verify exercise exists
        exercise = get_supabase_data(supabase.table('exercises').select('*').eq('exercise_id', session_data.exercise_id).execute())
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        # Get user's weight unit preference
        user = get_supabase_data(supabase.table('users').select('*').eq('user_id', current_user["user_id"]).execute())
        weight_unit = user.get("weight_unit", "kg") if user else "kg"
        
        # Calculate total volume (weight * reps * sets)
        total_volume = sum(s.weight * s.reps for s in session_data.sets)
        
        # Create session
        session_id = str(uuid.uuid4())
        duration_minutes = session_data.duration_minutes or 0  # Use provided duration or 0
        session = {
            "session_id": session_id,
            "user_id": current_user["user_id"],
            "exercise_id": session_data.exercise_id,
            "exercise_name": exercise["name"],
            "sets": [s.dict() for s in session_data.sets],
            "total_sets": len(session_data.sets),
            "total_volume": total_volume,
            "duration_minutes": duration_minutes,
            "weight_unit": weight_unit,
            "notes": session_data.notes,
            "created_at": datetime.utcnow().isoformat(),
            "completed": True
        }
        
        supabase.table('workout_sessions').insert(session).execute()
        
        # AUTO-TRACK: Update daily active minutes if duration provided
        if duration_minutes > 0:
            today = datetime.utcnow().date().isoformat()
            stats = get_supabase_data(supabase.table('user_stats').select('*').eq('user_id', current_user["user_id"]).eq('date', today).execute())
            
            if stats:
                # Increment active_minutes
                new_active_minutes = stats.get("active_minutes", 0) + duration_minutes
                supabase.table('user_stats').update({"active_minutes": new_active_minutes, "updated_at": datetime.utcnow().isoformat()}).eq('user_id', current_user["user_id"]).eq('date', today).execute()
            else:
                # Create new stats entry
                supabase.table('user_stats').insert({
                    "user_id": current_user["user_id"],
                    "date": today,
                    "steps": 0,
                    "calories_burned": 0,
                    "calories_consumed": 0,
                    "active_minutes": duration_minutes,
                    "water_intake": 0,
                    "sleep_hours": 0,
                    "updated_at": datetime.utcnow().execute().isoformat()
                })
        
        return {
            "message": "Workout session created successfully",
            "session_id": session_id,
            "total_volume": total_volume,
            "total_sets": len(session_data.sets),
            "duration_minutes": duration_minutes,
            "auto_tracked": duration_minutes > 0  # Flag to show toast notification
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating workout session: {str(e)}")

@app.get("/api/workouts/sessions")
async def get_workout_sessions(
    exercise_id: Optional[str] = None,
    limit: int = 20,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get user's workout sessions, optionally filtered by exercise"""
    try:
        current_user = decode_jwt_token(credentials.credentials)
        
        query = {"user_id": current_user["user_id"]}
        if exercise_id:
            query["exercise_id"] = exercise_id
        
        if 'exercise_id' in query:
            sessions = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user['user_id']).eq('exercise_id', query['exercise_id']).order('created_at', desc=True).execute())
        else:
            sessions = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user['user_id']).order('created_at', desc=True).execute())
        
        return {"sessions": sessions, "count": len(sessions)}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")

@app.get("/api/workouts/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get detailed information about a specific workout session"""
    try:
        current_user = decode_jwt_token(credentials.credentials)
        
        session = get_supabase_data(supabase.table('workout_sessions').select('*').eq('session_id', session_id).eq('user_id', current_user['user_id']).execute())
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")

@app.delete("/api/workouts/sessions/{session_id}")
async def delete_workout_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a workout session"""
    try:
        current_user = decode_jwt_token(credentials.credentials)
        
        result = supabase.table('workout_sessions').delete().eq('session_id', session_id).eq('user_id', current_user["user_id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Workout session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@app.put("/api/workouts/sessions/{session_id}")
async def update_workout_session(
    session_id: str,
    session_data: WorkoutSessionCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update an existing workout session"""
    try:
        current_user = decode_jwt_token(credentials.credentials)
        
        # Verify session exists and belongs to user
        existing_session = get_supabase_data(supabase.table('workout_sessions').select('*').eq('session_id', session_id).eq('user_id', current_user["user_id"]).execute())
        
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify exercise exists
        exercise = get_supabase_data(supabase.table('exercises').select('*').eq('exercise_id', session_data.exercise_id).execute())
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        # Get user's weight unit preference
        user = get_supabase_data(supabase.table('users').select('*').eq('user_id', current_user["user_id"]).execute())
        weight_unit = user.get("weight_unit", "kg") if user else "kg"
        
        # Calculate total volume
        total_volume = sum(s.weight * s.reps for s in session_data.sets)
        
        # Find max weight
        max_weight = max((s.weight for s in session_data.sets), default=0)
        
        # Update session
        update_data = {
            "exercise_id": session_data.exercise_id,
            "exercise_name": exercise["name"],
            "sets": [s.dict() for s in session_data.sets],
            "total_volume": total_volume,
            "max_weight": max_weight,
            "weight_unit": weight_unit,
            "notes": session_data.notes,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase.table('workout_sessions').update(update_data).eq('session_id', session_id).execute()
        
        # Return updated session
        session = get_supabase_data(supabase.table('workout_sessions').select('*').eq('session_id', session_id).eq('user_id', current_user['user_id']).execute())
        
        return updated_session
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating workout session: {str(e)}")

@app.get("/api/workouts/exercises/{exercise_id}/history")
async def get_exercise_history(
    exercise_id: str,
    limit: int = 10,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get workout history for a specific exercise"""
    try:
        current_user = decode_jwt_token(credentials.credentials)
        
        sessions = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user['user_id']).eq('exercise_id', exercise_id).execute())
        
        if not sessions:
            return {"history": [], "count": 0}
        
        # Calculate progress data
        history = []
        for session in sessions:
            # Find max weight and max reps used in this session
            max_weight = max((s["weight"] for s in session["sets"]), default=0)
            max_reps = max((s["reps"] for s in session["sets"]), default=0)
            
            history.append({
                "date": session["created_at"],
                "total_sets": session["total_sets"],
                "total_volume": session["total_volume"],
                "max_weight": max_weight,
                "max_reps": max_reps,
                "weight_unit": session.get("weight_unit", "kg")
            })
        
        return {"history": history, "count": len(history)}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching exercise history: {str(e)}")

@app.get("/api/workouts/exercises/{exercise_id}/stats")
async def get_exercise_stats(
    exercise_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get statistics for a specific exercise (PB, 1RM estimate, etc.)"""
    try:
        current_user = decode_jwt_token(credentials.credentials)
        
        # Get all sessions for this exercise
        sessions = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user['user_id']).eq('exercise_id', exercise_id).execute())
        
        if not sessions:
            return {
                "personal_best": None,
                "max_reps": None,
                "estimated_1rm": None,
                "total_sessions": 0,
                "total_volume": 0,
                "avg_volume_per_session": 0
            }
        
        # Calculate personal best (highest weight used) and max reps
        all_weights = []
        all_reps = []
        all_sets = []
        for session in sessions:
            for set_data in session["sets"]:
                all_weights.append(set_data["weight"])
                all_reps.append(set_data["reps"])
                all_sets.append(set_data)
        
        personal_best = max(all_weights) if all_weights else 0
        max_reps = max(all_reps) if all_reps else 0
        
        # Estimate 1RM using Epley formula: weight * (1 + reps/30)
        # Find the set with highest estimated 1RM
        estimated_1rm = 0
        for set_data in all_sets:
            set_1rm = set_data["weight"] * (1 + set_data["reps"] / 30)
            if set_1rm > estimated_1rm:
                estimated_1rm = set_1rm
        
        # Calculate total volume across all sessions
        total_volume = sum(session["total_volume"] for session in sessions)
        avg_volume = total_volume / len(sessions) if sessions else 0
        
        # Get last session data
        last_session = sessions[0] if sessions else None
        
        # Check if there's progress (compare last session to session before)
        progress = None
        if len(sessions) >= 2:
            last_volume = sessions[0]["total_volume"]
            prev_volume = sessions[1]["total_volume"]
            volume_diff = last_volume - prev_volume
            progress = {
                "volume_change": volume_diff,
                "percent_change": (volume_diff / prev_volume * 100) if prev_volume > 0 else 0
            }
        
        weight_unit = sessions[0].get("weight_unit", "kg") if sessions else "kg"
        
        return {
            "personal_best": personal_best,
            "max_reps": max_reps,
            "estimated_1rm": round(estimated_1rm, 1),
            "total_sessions": len(sessions),
            "total_volume": round(total_volume, 1),
            "avg_volume_per_session": round(avg_volume, 1),
            "last_session": last_session,
            "progress": progress,
            "weight_unit": weight_unit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")

@app.get("/api/workouts/dashboard/stats")
async def get_workout_dashboard_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get overall workout statistics for dashboard"""
    try:
        current_user = decode_jwt_token(credentials.credentials)
        
        # Get all user's workout sessions
        all_sessions = get_supabase_list(supabase.table('workout_sessions').select('*').eq('user_id', current_user['user_id']).execute())
        
        if not all_sessions:
            return {
                "total_workouts": 0,
                "total_volume_lifted": 0,
                "workouts_this_week": 0,
                "workouts_this_month": 0,
                "favorite_exercise": None,
                "recent_workout": None
            }
        
        # Calculate total volume
        total_volume = sum(session["total_volume"] for session in all_sessions)
        
        # Get workouts this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        workouts_this_week = sum(
            1 for session in all_sessions
            if datetime.fromisoformat(session["created_at"]) >= week_ago
        )
        
        # Get workouts this month
        month_ago = datetime.utcnow() - timedelta(days=30)
        workouts_this_month = sum(
            1 for session in all_sessions
            if datetime.fromisoformat(session["created_at"]) >= month_ago
        )
        
        # Find favorite exercise (most frequent)
        exercise_counts = {}
        for session in all_sessions:
            exercise_id = session["exercise_id"]
            exercise_name = session["exercise_name"]
            if exercise_id not in exercise_counts:
                exercise_counts[exercise_id] = {"name": exercise_name, "count": 0}
            exercise_counts[exercise_id]["count"] += 1
        
        favorite_exercise = None
        if exercise_counts:
            fav_id = max(exercise_counts, key=lambda k: exercise_counts[k]["count"])
            favorite_exercise = {
                "exercise_id": fav_id,
                "name": exercise_counts[fav_id]["name"],
                "count": exercise_counts[fav_id]["count"]
            }
        
        # Find most recent workout
        recent_workout = None
        if all_sessions:
            # Sort by created_at to get the most recent
            sorted_sessions = sorted(all_sessions, key=lambda x: x["created_at"], reverse=True)
            most_recent = sorted_sessions[0]
            recent_workout = {
                "exercise_id": most_recent["exercise_id"],
                "name": most_recent["exercise_name"],
                "created_at": most_recent["created_at"]
            }
        
        weight_unit = all_sessions[0].get("weight_unit", "kg") if all_sessions else "kg"
        
        return {
            "total_workouts": len(all_sessions),
            "total_volume_lifted": round(total_volume, 1),
            "workouts_this_week": workouts_this_week,
            "workouts_this_month": workouts_this_month,
            "favorite_exercise": favorite_exercise,
            "recent_workout": recent_workout,
            "weight_unit": weight_unit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)