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
import requests
import json
from io import BytesIO
from dotenv import load_dotenv

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

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemma-3-27b-it:free"

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
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[str] = None
    goal_weight: Optional[float] = None

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
    Analyze food image using OpenRouter API with Google Gemma 3 27B
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://fitflow.app",
        "X-Title": "FitFlow"
    }
    
    prompt = """Analyze this food image and provide ONLY a JSON response with the following structure:
{
  "food_name": "name of the food",
  "calories": estimated total calories (number),
  "protein": grams of protein (number),
  "carbs": grams of carbohydrates (number),
  "fat": grams of fat (number),
  "portion_size": "description of portion size (e.g., '1 bowl', '2 slices')"
}

Provide realistic estimates based on the visible portion. Return ONLY valid JSON, no additional text."""
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Try to extract JSON from the response
        # Sometimes the model wraps JSON in markdown code blocks
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        # Parse the JSON response
        food_data = json.loads(content)
        
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
        "daily_calories": daily_calories
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)