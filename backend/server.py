from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from pymongo import MongoClient
import os
import jwt
import bcrypt
import uuid
import base64
import json
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

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

# MongoDB Connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
db = client['fitflow_db']
users_collection = db['users']
food_scans_collection = db['food_scans']
user_stats_collection = db['user_stats']
goals_collection = db['goals']
measurements_collection = db['measurements']
chat_history_collection = db['chat_history']
meal_plans_collection = db['meal_plans']

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# OpenAI API Configuration (using Emergent LLM Key)
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

security = HTTPBearer()

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
    user = users_collection.find_one({"user_id": payload["user_id"]})
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

# Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "FitFlow API"}

@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    # Check if user already exists
    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user_data.password)
    
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
        "created_at": datetime.utcnow().isoformat()
    }
    
    users_collection.insert_one(user)
    
    # Calculate daily calorie requirements if profile is complete
    daily_calories = None
    if all([user_data.weight, user_data.height, user_data.age, user_data.gender]):
        daily_calories = calculate_daily_calories(
            user_data.weight, user_data.height, user_data.age,
            user_data.gender, user_data.activity_level, user_data.goal_weight
        )
    
    token = create_jwt_token(user_id, user_data.email)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "user_id": user_id,
            "name": user_data.name,
            "email": user_data.email
        },
        "daily_calories": daily_calories
    }

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    user = users_collection.find_one({"email": credentials.email})
    
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
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
        "profile_picture": current_user.get("profile_picture")
    }

@app.put("/api/user/profile")
async def update_profile(profile_data: UserProfile, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
    
    if update_data:
        users_collection.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": update_data}
        )
    
    return {"message": "Profile updated successfully"}

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@app.put("/api/user/password")
async def change_password(password_data: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Change user password"""
    # Verify current password
    user = users_collection.find_one({"user_id": current_user["user_id"]})
    if not user or not bcrypt.checkpw(password_data.current_password.encode('utf-8'), user['password'].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash new password
    hashed_password = bcrypt.hashpw(password_data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update password
    users_collection.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"password": hashed_password}}
    )
    
    return {"message": "Password changed successfully"}

@app.delete("/api/user/account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Delete user account and all associated data"""
    user_id = current_user["user_id"]
    
    # Delete user data from all collections
    users_collection.delete_one({"user_id": user_id})
    food_scans_collection.delete_many({"user_id": user_id})
    user_stats_collection.delete_many({"user_id": user_id})
    goals_collection.delete_many({"user_id": user_id})
    measurements_collection.delete_many({"user_id": user_id})
    chat_history_collection.delete_many({"user_id": user_id})
    
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
        
        food_scans_collection.insert_one(scan_data)
        
        return {
            "scan_id": scan_id,
            "food_name": analysis_result["food_name"],
            "calories": analysis_result["calories"],
            "protein": analysis_result["protein"],
            "carbs": analysis_result["carbs"],
            "fat": analysis_result["fat"],
            "portion_size": analysis_result["portion_size"]
        }
    except Exception as e:
        print(f"Error in scan_food: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/food/history")
async def get_food_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    scans = list(food_scans_collection.find(
        {"user_id": current_user["user_id"]}
    ).sort("scanned_at", -1).limit(limit))
    
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
    
    scans = list(food_scans_collection.find({
        "user_id": current_user["user_id"],
        "scanned_at": {"$gte": today_start.isoformat()}
    }).sort("scanned_at", -1))
    
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

@app.post("/api/stats/daily")
async def update_daily_stats(stats: DailyStats, current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().date().isoformat()
    
    stats_data = {
        "user_id": current_user["user_id"],
        "date": today,
        "steps": stats.steps,
        "calories_burned": stats.calories_burned,
        "active_minutes": stats.active_minutes,
        "water_intake": stats.water_intake,
        "sleep_hours": stats.sleep_hours,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    user_stats_collection.update_one(
        {"user_id": current_user["user_id"], "date": today},
        {"$set": stats_data},
        upsert=True
    )
    
    return {"message": "Daily stats updated successfully"}

@app.get("/api/stats/daily")
async def get_daily_stats(current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().date().isoformat()
    
    stats = user_stats_collection.find_one({
        "user_id": current_user["user_id"],
        "date": today
    })
    
    if not stats:
        return {
            "steps": 0,
            "calories_burned": 0,
            "active_minutes": 0,
            "water_intake": 0,
            "sleep_hours": 0
        }
    
    return {
        "steps": stats.get("steps", 0),
        "calories_burned": stats.get("calories_burned", 0),
        "active_minutes": stats.get("active_minutes", 0),
        "water_intake": stats.get("water_intake", 0),
        "sleep_hours": stats.get("sleep_hours", 0)
    }

@app.get("/api/stats/streak")
async def get_streak(current_user: dict = Depends(get_current_user)):
    # Get user's activity history
    stats = list(user_stats_collection.find(
        {"user_id": current_user["user_id"]}
    ).sort("date", -1))
    
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
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    goals_collection.insert_one(goal_data)
    return {"message": "Goal created successfully", "goal_id": goal_id}

@app.get("/api/goals")
async def get_goals(current_user: dict = Depends(get_current_user)):
    goals = list(goals_collection.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0}
    ))
    return {"goals": goals}

@app.put("/api/goals/{goal_id}")
async def update_goal(goal_id: str, goal: Goal, current_user: dict = Depends(get_current_user)):
    result = goals_collection.update_one(
        {"goal_id": goal_id, "user_id": current_user["user_id"]},
        {"$set": {
            "current_progress": goal.current_progress,
            "target_value": goal.target_value,
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    if result.modified_count == 0:
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
    measurements_collection.insert_one(measurement_data)
    return {"message": "Measurement added successfully", "measurement_id": measurement_id}

@app.get("/api/measurements/latest")
async def get_latest_measurement(current_user: dict = Depends(get_current_user)):
    measurement = measurements_collection.find_one(
        {"user_id": current_user["user_id"]},
        {"_id": 0},
        sort=[("date", -1)]
    )
    if not measurement:
        return {"measurement": None}
    return {"measurement": measurement}

@app.get("/api/measurements/history")
async def get_measurements_history(limit: int = 30, current_user: dict = Depends(get_current_user)):
    measurements = list(measurements_collection.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0}
    ).sort("date", -1).limit(limit))
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
        chat_history_collection.insert_one({
            "chat_id": str(uuid.uuid4()),
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
    chats = list(chat_history_collection.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit))
    return {"chats": list(reversed(chats))}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)