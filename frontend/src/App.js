import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentPage, setCurrentPage] = useState('login');
  const [token, setToken] = useState(localStorage.getItem('fitflow_token'));
  const [user, setUser] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Food scanner state
  const [scannerMode, setScannerMode] = useState('upload'); // 'upload' or 'camera'
  const [capturedImage, setCapturedImage] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [foodHistory, setFoodHistory] = useState([]);
  const [todayFood, setTodayFood] = useState(null);
  
  // Dashboard state
  const [dailyStats, setDailyStats] = useState(null);
  const [streak, setStreak] = useState(0);
  const [dailyCalories, setDailyCalories] = useState(null);
  
  // Profile state
  const [goals, setGoals] = useState([]);
  const [measurements, setMeasurements] = useState(null);
  const [notifications, setNotifications] = useState(true);
  const [theme, setTheme] = useState(localStorage.getItem('fitflow_theme') || 'system');
  const [showThemeModal, setShowThemeModal] = useState(false);
  const [showEditProfileModal, setShowEditProfileModal] = useState(false);
  const [editProfileData, setEditProfileData] = useState({});
  const [profilePicturePreview, setProfilePicturePreview] = useState(null);
  
  // Meal Plan state
  const [mealPlans, setMealPlans] = useState([]);
  const [selectedMealPlan, setSelectedMealPlan] = useState(null);
  const [showCreateMealPlanModal, setShowCreateMealPlanModal] = useState(false);
  const [showMealPlanDetails, setShowMealPlanDetails] = useState(false);
  const [mealPlanType, setMealPlanType] = useState(''); // 'ai' or 'manual'
  const [aiMealPlanData, setAiMealPlanData] = useState({
    duration: 7,
    dietary_preferences: '',
    allergies: '',
    calorie_target: ''
  });
  const [generatingMealPlan, setGeneratingMealPlan] = useState(false);
  const [manualMealPlanData, setManualMealPlanData] = useState({
    name: '',
    duration: 7,
    start_date: new Date().toISOString().split('T')[0],
    days: []
  });
  const profilePictureInputRef = useRef(null);
  
  // Settings state
  const [showSettingsPage, setShowSettingsPage] = useState(false);
  const [settingsSubPage, setSettingsSubPage] = useState('main'); // main, connected-apps, change-password, help, contact
  const [workoutReminders, setWorkoutReminders] = useState(true);
  const [appUpdates, setAppUpdates] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [contactMessage, setContactMessage] = useState('');
  const [contactSubject, setContactSubject] = useState('');
  
  // Chatbot state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [chatLanguage, setChatLanguage] = useState('english');
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);
  
  // Camera refs
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [isCameraActive, setIsCameraActive] = useState(false);

  useEffect(() => {
    if (token) {
      fetchUserProfile();
    }
  }, [token]);

  useEffect(() => {
    if (currentPage === 'home' && token) {
      fetchDashboardData();
      fetchChatHistory();
    }
    if (currentPage === 'profile' && token) {
      fetchGoals();
      fetchMeasurements();
    }
    if (currentPage === 'mealplan' && token) {
      fetchMealPlans();
    }
  }, [currentPage, token]);

  useEffect(() => {
    if (currentPage === 'scan' && token) {
      fetchFoodHistory();
      fetchTodayFood();
    }
  }, [currentPage, token]);

  // Cleanup camera stream
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  // Theme handling
  useEffect(() => {
    const applyTheme = () => {
      const root = document.documentElement;
      
      if (theme === 'system') {
        // Detect system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        root.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
      } else {
        root.setAttribute('data-theme', theme);
      }
    };

    applyTheme();

    // Listen for system theme changes when theme is set to 'system'
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = () => applyTheme();
      
      // Modern browsers
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
      } 
      // Legacy browsers
      else if (mediaQuery.addListener) {
        mediaQuery.addListener(handleChange);
        return () => mediaQuery.removeListener(handleChange);
      }
    }
  }, [theme]);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/user/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUser(data);
        setDailyCalories(data.daily_calories);
        setCurrentPage('home');
      } else {
        localStorage.removeItem('fitflow_token');
        setToken(null);
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
    }
  };

  const fetchDashboardData = async () => {
    try {
      const [statsRes, streakRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/stats/daily`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${BACKEND_URL}/api/stats/streak`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      
      if (statsRes.ok) {
        const stats = await statsRes.json();
        setDailyStats(stats);
      }
      
      if (streakRes.ok) {
        const streakData = await streakRes.json();
        setStreak(streakData.streak_days);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    }
  };

  const fetchGoals = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/goals`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setGoals(data.goals);
      }
    } catch (err) {
      console.error('Error fetching goals:', err);
    }
  };

  const fetchMeasurements = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/measurements/latest`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setMeasurements(data.measurement);
      }
    } catch (err) {
      console.error('Error fetching measurements:', err);
    }
  };

  const fetchChatHistory = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/chat/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setChatMessages(data.chats);
      }
    } catch (err) {
      console.error('Error fetching chat history:', err);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMessage = chatInput.trim();
    setChatInput('');
    setIsChatLoading(true);
    
    // Add user message to chat
    const tempUserMsg = {
      user_message: userMessage,
      assistant_message: '',
      timestamp: new Date().toISOString()
    };
    setChatMessages(prev => [...prev, tempUserMsg]);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/chat/fitness`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          message: userMessage,
          language: chatLanguage
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        // Update the last message with assistant's response
        setChatMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = {
            user_message: userMessage,
            assistant_message: data.message,
            timestamp: data.timestamp
          };
          return newMessages;
        });
      }
    } catch (err) {
      console.error('Error sending chat message:', err);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Meal Plan Functions
  const fetchMealPlans = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/mealplan/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setMealPlans(data.plans);
      }
    } catch (err) {
      console.error('Error fetching meal plans:', err);
    }
  };

  const fetchMealPlanDetails = async (planId) => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/mealplan/${planId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedMealPlan(data);
        setShowMealPlanDetails(true);
      }
    } catch (err) {
      console.error('Error fetching meal plan details:', err);
      setError('Failed to load meal plan details');
    } finally {
      setLoading(false);
    }
  };

  const generateAIMealPlan = async () => {
    try {
      setGeneratingMealPlan(true);
      setError('');
      
      const requestData = {
        duration: parseInt(aiMealPlanData.duration),
        dietary_preferences: aiMealPlanData.dietary_preferences || null,
        allergies: aiMealPlanData.allergies || null,
        calorie_target: aiMealPlanData.calorie_target ? parseInt(aiMealPlanData.calorie_target) : null
      };

      const response = await fetch(`${BACKEND_URL}/api/mealplan/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestData)
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess('AI Meal Plan generated successfully!');
        setShowCreateMealPlanModal(false);
        setAiMealPlanData({ duration: 7, dietary_preferences: '', allergies: '', calorie_target: '' });
        await fetchMealPlans();
        
        // Show the newly created meal plan
        await fetchMealPlanDetails(data.plan_id);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to generate meal plan');
      }
    } catch (err) {
      console.error('Error generating meal plan:', err);
      setError('Failed to generate meal plan. Please try again.');
    } finally {
      setGeneratingMealPlan(false);
    }
  };

  const initializeManualMealPlan = (duration) => {
    const days = [];
    const mealCategories = ['breakfast', 'morning_snack', 'lunch', 'afternoon_snack', 'dinner'];
    
    for (let i = 1; i <= duration; i++) {
      const dayMeals = {};
      mealCategories.forEach(category => {
        dayMeals[category] = {
          name: '',
          calories: 0,
          protein: 0,
          carbs: 0,
          fat: 0,
          description: '',
          ingredients: []
        };
      });
      
      days.push({
        day: i,
        meals: dayMeals,
        totals: {
          calories: 0,
          protein: 0,
          carbs: 0,
          fat: 0
        }
      });
    }
    
    setManualMealPlanData({
      ...manualMealPlanData,
      duration: parseInt(duration),
      days: days
    });
  };

  const updateManualMeal = (dayIndex, mealType, field, value) => {
    const updatedDays = [...manualMealPlanData.days];
    updatedDays[dayIndex].meals[mealType][field] = field === 'ingredients' ? value : (field === 'name' || field === 'description' ? value : parseFloat(value) || 0);
    
    // Recalculate day totals
    const meals = updatedDays[dayIndex].meals;
    updatedDays[dayIndex].totals = {
      calories: Object.values(meals).reduce((sum, meal) => sum + (meal.calories || 0), 0),
      protein: Object.values(meals).reduce((sum, meal) => sum + (meal.protein || 0), 0),
      carbs: Object.values(meals).reduce((sum, meal) => sum + (meal.carbs || 0), 0),
      fat: Object.values(meals).reduce((sum, meal) => sum + (meal.fat || 0), 0)
    };
    
    setManualMealPlanData({
      ...manualMealPlanData,
      days: updatedDays
    });
  };

  const createManualMealPlan = async () => {
    try {
      // Validate
      if (!manualMealPlanData.name.trim()) {
        setError('Please enter a meal plan name');
        return;
      }

      // Check if at least one meal has content
      const hasContent = manualMealPlanData.days.some(day => 
        Object.values(day.meals).some(meal => meal.name.trim())
      );
      
      if (!hasContent) {
        setError('Please add at least one meal to your plan');
        return;
      }

      setGeneratingMealPlan(true);
      setError('');
      
      const response = await fetch(`${BACKEND_URL}/api/mealplan/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(manualMealPlanData)
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess('Manual Meal Plan created successfully!');
        setShowCreateMealPlanModal(false);
        setMealPlanType('');
        setManualMealPlanData({
          name: '',
          duration: 7,
          start_date: new Date().toISOString().split('T')[0],
          days: []
        });
        await fetchMealPlans();
        
        // Show the newly created meal plan
        await fetchMealPlanDetails(data.plan_id);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create meal plan');
      }
    } catch (err) {
      console.error('Error creating meal plan:', err);
      setError('Failed to create meal plan. Please try again.');
    } finally {
      setGeneratingMealPlan(false);
    }
  };

  const deleteMealPlan = async (planId) => {
    if (!window.confirm('Are you sure you want to delete this meal plan?')) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/mealplan/${planId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setSuccess('Meal plan deleted successfully');
        setShowMealPlanDetails(false);
        setSelectedMealPlan(null);
        await fetchMealPlans();
      } else {
        setError('Failed to delete meal plan');
      }
    } catch (err) {
      console.error('Error deleting meal plan:', err);
      setError('Failed to delete meal plan');
    }
  };

  const fetchFoodHistory = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/food/history?limit=10`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFoodHistory(data.history);
      }
    } catch (err) {
      console.error('Error fetching food history:', err);
    }
  };

  const fetchTodayFood = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/food/today`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTodayFood(data);
      }
    } catch (err) {
      console.error('Error fetching today food:', err);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        localStorage.setItem('fitflow_token', data.token);
        setToken(data.token);
        setUser(data.user);
        setDailyCalories(data.daily_calories);
        setCurrentPage('home');
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        localStorage.setItem('fitflow_token', data.token);
        setToken(data.token);
        setUser(data.user);
        setCurrentPage('home');
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('fitflow_token');
    setToken(null);
    setUser(null);
    setCurrentPage('login');
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };

  const openEditProfileModal = () => {
    setEditProfileData({
      name: user?.name || '',
      age: user?.age || '',
      gender: user?.gender || '',
      height: user?.height || '',
      weight: user?.weight || '',
      activity_level: user?.activity_level || 'moderate',
      goal_weight: user?.goal_weight || ''
    });
    setProfilePicturePreview(user?.profile_picture || null);
    setShowEditProfileModal(true);
  };

  const handleProfilePictureChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError('Image size should be less than 5MB');
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfilePicturePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleEditProfileSubmit = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const profileData = {
        ...editProfileData,
        profile_picture: profilePicturePreview
      };

      // Remove empty values
      Object.keys(profileData).forEach(key => {
        if (profileData[key] === '' || profileData[key] === null) {
          delete profileData[key];
        }
      });

      const response = await fetch(`${BACKEND_URL}/api/user/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(profileData)
      });

      if (response.ok) {
        setSuccess('Profile updated successfully!');
        await fetchUserProfile(); // Refresh user data
        setTimeout(() => {
          setShowEditProfileModal(false);
          setSuccess('');
        }, 1500);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update profile');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
        setIsCameraActive(true);
      }
    } catch (err) {
      console.error('Error accessing camera:', err);
      setError('Unable to access camera. Please check permissions.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setIsCameraActive(false);
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      const imageData = canvas.toDataURL('image/jpeg', 0.8);
      setCapturedImage(imageData);
      stopCamera();
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setCapturedImage(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const analyzeFoodImage = async () => {
    if (!capturedImage) return;
    
    setLoading(true);
    setError('');
    setScanResult(null);
    
    try {
      const formData = new FormData();
      formData.append('image', capturedImage);
      
      const response = await fetch(`${BACKEND_URL}/api/food/scan`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setScanResult(data);
        setSuccess('Food analyzed successfully!');
        setTimeout(() => {
          fetchFoodHistory();
          fetchTodayFood();
        }, 500);
      } else {
        setError(data.detail || 'Failed to analyze food');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error('Error analyzing food:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetScanner = () => {
    setCapturedImage(null);
    setScanResult(null);
    setError('');
    setSuccess('');
  };

  // Render Login Page
  const renderLogin = () => (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="app-logo">FitFlow</h1>
        
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>Username or Email</label>
            <input
              type="email"
              placeholder="Enter your username or email"
              value={formData.email || ''}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              value={formData.password || ''}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Loading...' : 'Login'}
          </button>
          
          <div className="auth-divider">OR</div>
          
          <button type="button" className="btn-secondary" disabled>
            <span>G</span> Continue with Google
          </button>
          
          <p className="auth-footer">
            Don't have an account? <span onClick={() => setCurrentPage('register')}>Create one</span>
          </p>
        </form>
      </div>
    </div>
  );

  // Render Register Page
  const renderRegister = () => (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-icon">🏃</div>
        <h1>Create an Account</h1>
        
        <form onSubmit={handleRegister}>
          <div className="form-group">
            <label>Name</label>
            <input
              type="text"
              placeholder="Enter your name"
              value={formData.name || ''}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              placeholder="Enter your email"
              value={formData.email || ''}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              value={formData.password || ''}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Sign Up'}
          </button>
          
          <div className="auth-divider">OR</div>
          
          <button type="button" className="btn-secondary" disabled>
            <span>G</span> Continue with Google
          </button>
          
          <p className="auth-footer">
            Already have an account? <span onClick={() => setCurrentPage('login')}>Login</span>
          </p>
        </form>
      </div>
    </div>
  );

  // Render Home/Dashboard Page
  const renderHome = () => (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="user-greeting">
          <div className="user-avatar">
            {user?.profile_picture ? (
              <img src={user.profile_picture} alt="User" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
            ) : (
              '👤'
            )}
          </div>
          <h2>Hello, {user?.name?.split(' ')[0] || 'User'}!</h2>
        </div>
        <button className="icon-btn" onClick={handleLogout}>🔔</button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-ring" style={{'--progress': '68'}}>
            <span className="stat-value">{dailyStats?.steps || 8500}</span>
          </div>
          <p className="stat-label">Steps</p>
        </div>
        
        <div className="stat-card">
          <div className="stat-ring" style={{'--progress': '45'}}>
            <span className="stat-value">{todayFood?.total_calories || 1200}</span>
          </div>
          <p className="stat-label">Calories</p>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">⚡</div>
          <div className="stat-info">
            <p className="stat-value">{streak || 12} days</p>
            <p className="stat-label">Streak</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-ring" style={{'--progress': '75'}}>
            <span className="stat-value">{dailyStats?.active_minutes || 45}m</span>
          </div>
          <p className="stat-label">Active</p>
        </div>
      </div>

      <div className="progress-section">
        <div className="section-header">
          <h3>Weight Progress</h3>
          <div className="tab-group">
            <button className="tab active">Week</button>
            <button className="tab">Month</button>
            <button className="tab">Year</button>
          </div>
        </div>
        
        <div className="weight-display">
          <h2>{user?.weight || 65} kg</h2>
          <p className="weight-change">Last 7 days -1.2%</p>
        </div>
        
        <div className="chart-placeholder">
          <svg viewBox="0 0 300 100" className="progress-chart">
            <path d="M 0,60 Q 30,45 50,50 T 100,55 T 150,40 T 200,50 T 250,45 T 300,35" 
                  stroke="var(--brand-primary)" strokeWidth="2" fill="none"/>
          </svg>
        </div>
      </div>

      <div className="quick-stats">
        <div className="quick-stat-item">
          <div className="quick-stat-icon">💧</div>
          <div>
            <p className="quick-stat-label">Water Intake</p>
            <p className="quick-stat-subtitle">Stay hydrated!</p>
          </div>
          <span className="quick-stat-value">{dailyStats?.water_intake || 4}/8 glasses</span>
        </div>
        
        <div className="quick-stat-item">
          <div className="quick-stat-icon">🌙</div>
          <div>
            <p className="quick-stat-label">Last Night's Sleep</p>
            <p className="quick-stat-subtitle">{dailyStats?.sleep_hours || 8}h 15m</p>
          </div>
          <button className="quick-action-btn">📊</button>
        </div>
      </div>

      {dailyCalories && (
        <div className="calorie-info">
          <h3>Daily Calorie Target</h3>
          <p className="calorie-target">{Math.round(dailyCalories.daily_target)} kcal</p>
          <p className="calorie-detail">BMR: {Math.round(dailyCalories.bmr)} | TDEE: {Math.round(dailyCalories.tdee)}</p>
        </div>
      )}

      {/* Floating Chatbot Button */}
      <button 
        className="floating-chat-btn"
        onClick={() => setCurrentPage('chatbot')}
        title="Chat with AI Fitness Coach"
      >
        <span style={{ fontSize: '28px' }}>💬</span>
      </button>
    </div>
  );

  // Render Food Scanner Page
  const renderScanner = () => (
    <div className="scanner-container">
      <div className="scanner-header">
        <button className="back-btn" onClick={() => setCurrentPage('home')}>←</button>
        <h2>Food Scanner</h2>
        <div></div>
      </div>

      {!capturedImage ? (
        <div className="scanner-main">
          <div className="camera-preview">
            <video 
              ref={videoRef} 
              autoPlay 
              playsInline
              style={{ display: isCameraActive ? 'block' : 'none' }}
            />
            {!isCameraActive && (
              <div className="camera-placeholder">
                <div className="camera-icon">📷</div>
                <p>Tap to scan your meal</p>
              </div>
            )}
          </div>
          <canvas ref={canvasRef} style={{ display: 'none' }} />
          
          <div className="scanner-actions">
            {!isCameraActive ? (
              <>
                <button className="btn-primary" onClick={startCamera}>
                  Scan Food
                </button>
                <button className="btn-secondary" onClick={() => fileInputRef.current?.click()}>
                  📁 Upload Image
                </button>
                <input 
                  ref={fileInputRef}
                  type="file" 
                  accept="image/*" 
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                />
              </>
            ) : (
              <>
                <button className="btn-primary" onClick={capturePhoto}>
                  Capture Photo
                </button>
                <button className="btn-secondary" onClick={stopCamera}>
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
      ) : (
        <div className="scanner-result">
          <div className="captured-image">
            <img src={capturedImage} alt="Captured food" />
          </div>
          
          {!scanResult ? (
            <div className="scanner-actions">
              {error && <div className="error-message">{error}</div>}
              <button className="btn-primary" onClick={analyzeFoodImage} disabled={loading}>
                {loading ? 'Analyzing...' : 'Analyze Food'}
              </button>
              <button className="btn-secondary" onClick={resetScanner}>
                Retake
              </button>
            </div>
          ) : (
            <div className="analysis-result">
              <h3>AI Analysis</h3>
              {success && <div className="success-message">{success}</div>}
              
              <div className="result-card">
                <div className="result-header">
                  <h4>{scanResult.food_name}</h4>
                  <span className="calorie-badge">{Math.round(scanResult.calories)} cal</span>
                </div>
                <p className="portion-size">Portion Size: {scanResult.portion_size}</p>
                
                <div className="macros">
                  <h5>Macronutrients</h5>
                  <div className="macro-item">
                    <span>Protein</span>
                    <div className="macro-bar">
                      <div className="macro-fill" style={{width: `${(scanResult.protein/50)*100}%`}}></div>
                    </div>
                    <span>{Math.round(scanResult.protein)}g</span>
                  </div>
                  <div className="macro-item">
                    <span>Carbs</span>
                    <div className="macro-bar">
                      <div className="macro-fill" style={{width: `${(scanResult.carbs/100)*100}%`}}></div>
                    </div>
                    <span>{Math.round(scanResult.carbs)}g</span>
                  </div>
                  <div className="macro-item">
                    <span>Fat</span>
                    <div className="macro-bar">
                      <div className="macro-fill" style={{width: `${(scanResult.fat/50)*100}%`}}></div>
                    </div>
                    <span>{Math.round(scanResult.fat)}g</span>
                  </div>
                </div>
              </div>
              
              <button className="btn-primary" onClick={resetScanner}>
                Scan Another
              </button>
            </div>
          )}
        </div>
      )}

      {foodHistory.length > 0 && !capturedImage && (
        <div className="recent-scans">
          <h3>Your Recent Scans</h3>
          <div className="scan-list">
            {foodHistory.slice(0, 3).map((scan) => (
              <div key={scan.scan_id} className="scan-item">
                <img src={`data:image/jpeg;base64,${scan.image_base64}`} alt={scan.food_name} />
                <div className="scan-info">
                  <h4>{scan.food_name}</h4>
                  <p>{Math.round(scan.calories)} Calories</p>
                </div>
                <span className="scan-time">
                  {new Date(scan.scanned_at).toLocaleDateString() === new Date().toLocaleDateString() 
                    ? 'Today' 
                    : 'Yesterday'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Render Chatbot Page
  const renderChatbot = () => {
    const quickSuggestions = [
      "Suggest a workout",
      "What's a healthy snack?"
    ];

    return (
      <div className="chatbot-page">
        <div className="chatbot-page-header">
          <button className="back-btn" onClick={() => setCurrentPage('home')}>
            <span style={{ fontSize: '24px' }}>←</span>
          </button>
          <h2>AI Fitness Coach</h2>
          <button 
            className="menu-btn"
            onClick={() => setShowLanguageMenu(!showLanguageMenu)}
          >
            <span style={{ fontSize: '24px' }}>⋮</span>
          </button>
        </div>

        {/* Language Menu Dropdown */}
        {showLanguageMenu && (
          <div className="language-dropdown">
            <div className="language-dropdown-header">Select Language</div>
            {['english', 'hindi', 'marathi', 'spanish', 'french', 'german', 'chinese', 'japanese'].map((lang) => (
              <button
                key={lang}
                className={`language-dropdown-item ${chatLanguage === lang ? 'active' : ''}`}
                onClick={() => {
                  setChatLanguage(lang);
                  setShowLanguageMenu(false);
                }}
              >
                {lang.charAt(0).toUpperCase() + lang.slice(1)}
                {chatLanguage === lang && <span style={{ marginLeft: '8px' }}>✓</span>}
              </button>
            ))}
          </div>
        )}

        <div className="chatbot-messages-container">
          {chatMessages.length === 0 ? (
            <div className="chat-welcome-message">
              <div className="ai-message-bubble">
                <div className="ai-avatar">🤖</div>
                <div className="message-content">
                  <div className="message-header">AI Coach - {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</div>
                  <div className="message-text">
                    Hello! I'm your AI Fitness Coach. Ask me anything about fitness, nutrition, or workout plans. Let's get started on your fitness journey!
                  </div>
                </div>
              </div>
            </div>
          ) : (
            chatMessages.map((msg, index) => (
              <div key={index} className="message-group">
                {/* AI Message */}
                <div className="ai-message-bubble">
                  <div className="ai-avatar">🤖</div>
                  <div className="message-content">
                    <div className="message-header">AI Coach - {new Date(msg.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</div>
                    <div className="message-text">{msg.assistant_message || '...'}</div>
                  </div>
                </div>
                
                {/* User Message */}
                {msg.user_message && (
                  <div className="user-message-bubble">
                    <div className="message-content">
                      <div className="message-header">You - {new Date(msg.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</div>
                      <div className="message-text">{msg.user_message}</div>
                    </div>
                    <div className="user-avatar">
                      {user?.profile_picture ? (
                        <img src={user.profile_picture} alt="User" />
                      ) : (
                        '👤'
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
          {isChatLoading && (
            <div className="ai-message-bubble">
              <div className="ai-avatar">🤖</div>
              <div className="message-content">
                <div className="message-text typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="chatbot-input-section">
          {/* Quick Suggestions */}
          <div className="quick-suggestions">
            {quickSuggestions.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-btn"
                onClick={() => {
                  setChatInput(suggestion);
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>

          {/* Chat Input */}
          <div className="chat-input-wrapper">
            <input
              type="text"
              className="chat-input-field"
              placeholder="Type your message..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !isChatLoading && chatInput.trim() && sendChatMessage()}
              disabled={isChatLoading}
            />
            <button 
              className="chat-send-button"
              onClick={sendChatMessage}
              disabled={isChatLoading || !chatInput.trim()}
            >
              <span style={{ fontSize: '20px', transform: 'rotate(-45deg)', display: 'inline-block' }}>➤</span>
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Render Workout Page
  const renderWorkout = () => (
    <div className="workout-container">
      <div className="page-header">
        <h2>Exercise Library</h2>
        <button className="icon-btn">🔍</button>
      </div>

      <div className="filter-tabs">
        <button className="filter-tab active">All</button>
        <button className="filter-tab">Chest</button>
        <button className="filter-tab">Back</button>
        <button className="filter-tab">Legs</button>
      </div>

      <button className="btn-primary workout-cta">
        Start Today's Workout
      </button>

      <div className="exercise-grid">
        <div className="exercise-card">
          <div className="exercise-image" style={{backgroundColor: '#2a2a2a'}}>
            <span className="exercise-placeholder">🏋️</span>
          </div>
          <h4>Bench Press</h4>
        </div>
        
        <div className="exercise-card">
          <div className="exercise-image" style={{backgroundColor: '#f5f5f5'}}>
            <span className="exercise-placeholder">🧘</span>
          </div>
          <h4>Squat</h4>
        </div>
        
        <div className="exercise-card">
          <div className="exercise-image" style={{backgroundColor: '#2a2a2a'}}>
            <span className="exercise-placeholder">💪</span>
          </div>
          <h4>Deadlift</h4>
        </div>
        
        <div className="exercise-card">
          <div className="exercise-image" style={{backgroundColor: '#f5f5f5'}}>
            <span className="exercise-placeholder">🤸</span>
          </div>
          <h4>Overhead Press</h4>
        </div>
      </div>
    </div>
  );

  // Render Meal Plan Page
  const renderMealPlan = () => {
    // Show meal plan details if selected
    if (showMealPlanDetails && selectedMealPlan) {
      return (
        <div className="meal-plan-container">
          <div className="page-header">
            <button className="icon-btn" onClick={() => {
              setShowMealPlanDetails(false);
              setSelectedMealPlan(null);
            }}>
              ←
            </button>
            <h2>{selectedMealPlan.name}</h2>
            <button 
              className="icon-btn" 
              style={{ color: '#ef4444' }}
              onClick={() => deleteMealPlan(selectedMealPlan.plan_id)}
            >
              🗑️
            </button>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <div style={{ 
              background: 'rgba(34, 197, 94, 0.1)', 
              padding: '16px', 
              borderRadius: '12px',
              marginBottom: '16px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: '#888' }}>Duration:</span>
                <span style={{ color: '#22c55e', fontWeight: 'bold' }}>{selectedMealPlan.duration} days</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: '#888' }}>Type:</span>
                <span style={{ color: '#fff' }}>
                  {selectedMealPlan.type === 'ai_generated' ? '🤖 AI Generated' : '✍️ Manual'}
                </span>
              </div>
              {selectedMealPlan.calorie_target && (
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#888' }}>Daily Target:</span>
                  <span style={{ color: '#22c55e', fontWeight: 'bold' }}>
                    {selectedMealPlan.calorie_target} kcal
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Days List */}
          <div>
            {selectedMealPlan.days?.map((day, index) => (
              <div 
                key={index}
                style={{
                  background: '#1a1a1a',
                  borderRadius: '16px',
                  padding: '20px',
                  marginBottom: '16px',
                  border: '1px solid #333'
                }}
              >
                <h3 style={{ color: '#22c55e', marginBottom: '16px', fontSize: '18px' }}>
                  Day {day.day_number}
                </h3>

                {/* Daily Totals */}
                {day.totals && (
                  <div style={{
                    background: 'rgba(34, 197, 94, 0.1)',
                    padding: '12px',
                    borderRadius: '8px',
                    marginBottom: '16px',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: '12px',
                    textAlign: 'center'
                  }}>
                    <div>
                      <div style={{ color: '#888', fontSize: '12px' }}>Calories</div>
                      <div style={{ color: '#22c55e', fontWeight: 'bold' }}>
                        {Math.round(day.totals.calories)}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: '#888', fontSize: '12px' }}>Protein</div>
                      <div style={{ color: '#3b82f6', fontWeight: 'bold' }}>
                        {Math.round(day.totals.protein)}g
                      </div>
                    </div>
                    <div>
                      <div style={{ color: '#888', fontSize: '12px' }}>Carbs</div>
                      <div style={{ color: '#f59e0b', fontWeight: 'bold' }}>
                        {Math.round(day.totals.carbs)}g
                      </div>
                    </div>
                    <div>
                      <div style={{ color: '#888', fontSize: '12px' }}>Fat</div>
                      <div style={{ color: '#ef4444', fontWeight: 'bold' }}>
                        {Math.round(day.totals.fat)}g
                      </div>
                    </div>
                  </div>
                )}

                {/* Meals */}
                {day.meals && Object.entries(day.meals).map(([mealType, meal]) => (
                  <div 
                    key={mealType}
                    style={{
                      background: '#0a0a0a',
                      borderRadius: '12px',
                      padding: '16px',
                      marginBottom: '12px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <h4 style={{ 
                        color: '#fff', 
                        textTransform: 'capitalize',
                        fontSize: '16px',
                        margin: 0
                      }}>
                        {mealType.replace('_', ' ')}
                      </h4>
                      <span style={{ color: '#22c55e', fontWeight: 'bold' }}>
                        {meal.calories} kcal
                      </span>
                    </div>
                    
                    <div style={{ color: '#22c55e', fontWeight: '500', marginBottom: '6px' }}>
                      {meal.name}
                    </div>
                    
                    {meal.description && (
                      <p style={{ color: '#888', fontSize: '14px', marginBottom: '8px' }}>
                        {meal.description}
                      </p>
                    )}
                    
                    <div style={{ display: 'flex', gap: '16px', marginBottom: '8px', fontSize: '14px' }}>
                      <span style={{ color: '#3b82f6' }}>P: {meal.protein}g</span>
                      <span style={{ color: '#f59e0b' }}>C: {meal.carbs}g</span>
                      <span style={{ color: '#ef4444' }}>F: {meal.fat}g</span>
                    </div>
                    
                    {meal.ingredients && meal.ingredients.length > 0 && (
                      <div style={{ marginTop: '8px' }}>
                        <div style={{ color: '#888', fontSize: '12px', marginBottom: '4px' }}>
                          Ingredients:
                        </div>
                        <div style={{ color: '#ccc', fontSize: '13px' }}>
                          {meal.ingredients.join(', ')}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      );
    }

    // Show meal plans list
    return (
      <div className="meal-plan-container">
        <div className="page-header">
          <h2>Meal Plans</h2>
          <button 
            className="icon-btn"
            onClick={() => setShowCreateMealPlanModal(true)}
          >
            +
          </button>
        </div>

        {mealPlans.length === 0 ? (
          <div className="coming-soon">
            <h3>🍽️</h3>
            <p>No meal plans yet</p>
            <p className="subtitle">Create your first meal plan with AI or manually</p>
            <button 
              className="primary-btn"
              onClick={() => setShowCreateMealPlanModal(true)}
              style={{ marginTop: '20px' }}
            >
              Create Meal Plan
            </button>
          </div>
        ) : (
          <div>
            {mealPlans.map(plan => (
              <div 
                key={plan.plan_id}
                onClick={() => fetchMealPlanDetails(plan.plan_id)}
                style={{
                  background: '#1a1a1a',
                  borderRadius: '16px',
                  padding: '20px',
                  marginBottom: '16px',
                  cursor: 'pointer',
                  border: '1px solid #333',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = '#22c55e'}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = '#333'}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h3 style={{ color: '#fff', margin: 0, fontSize: '18px' }}>{plan.name}</h3>
                  <span style={{ color: '#888', fontSize: '14px' }}>
                    {plan.type === 'ai_generated' ? '🤖' : '✍️'}
                  </span>
                </div>
                
                <div style={{ display: 'flex', gap: '20px', color: '#888', fontSize: '14px' }}>
                  <div>
                    <span style={{ color: '#22c55e' }}>{plan.duration}</span> days
                  </div>
                  {plan.calorie_target && (
                    <div>
                      <span style={{ color: '#22c55e' }}>{plan.calorie_target}</span> kcal/day
                    </div>
                  )}
                  <div style={{ marginLeft: 'auto', color: '#666' }}>
                    {new Date(plan.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create Meal Plan Modal */}
        {showCreateMealPlanModal && (
          <div className="modal-overlay" onClick={() => setShowCreateMealPlanModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2 style={{ marginBottom: '24px' }}>Create Meal Plan</h2>

              {!mealPlanType ? (
                <div>
                  <p style={{ color: '#888', marginBottom: '24px' }}>
                    Choose how you want to create your meal plan:
                  </p>
                  
                  <button
                    className="primary-btn"
                    onClick={() => setMealPlanType('ai')}
                    style={{ width: '100%', marginBottom: '16px', padding: '20px' }}
                  >
                    <div style={{ fontSize: '24px', marginBottom: '8px' }}>🤖</div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold' }}>AI Generated</div>
                    <div style={{ fontSize: '14px', color: '#ccc', marginTop: '4px' }}>
                      Let AI create a personalized meal plan for you
                    </div>
                  </button>

                  <button
                    className="secondary-btn"
                    onClick={() => {
                      setMealPlanType('manual');
                      initializeManualMealPlan(7);
                    }}
                    style={{ width: '100%', padding: '20px' }}
                  >
                    <div style={{ fontSize: '24px', marginBottom: '8px' }}>✍️</div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold' }}>Manual</div>
                    <div style={{ fontSize: '14px', color: '#ccc', marginTop: '4px' }}>
                      Build your meal plan from scratch
                    </div>
                  </button>
                </div>
              ) : mealPlanType === 'ai' ? (
                <div>
                  <div className="form-group">
                    <label>Duration (days)</label>
                    <select
                      value={aiMealPlanData.duration}
                      onChange={(e) => setAiMealPlanData({...aiMealPlanData, duration: e.target.value})}
                      style={{
                        width: '100%',
                        padding: '12px',
                        background: '#1a1a1a',
                        border: '1px solid #333',
                        borderRadius: '8px',
                        color: '#fff'
                      }}
                    >
                      <option value="3">3 Days</option>
                      <option value="7">7 Days (1 Week)</option>
                      <option value="14">14 Days (2 Weeks)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Dietary Preferences (optional)</label>
                    <input
                      type="text"
                      placeholder="e.g., Vegetarian, Vegan, Keto, Low-carb"
                      value={aiMealPlanData.dietary_preferences}
                      onChange={(e) => setAiMealPlanData({...aiMealPlanData, dietary_preferences: e.target.value})}
                    />
                  </div>

                  <div className="form-group">
                    <label>Allergies (optional)</label>
                    <input
                      type="text"
                      placeholder="e.g., Nuts, Dairy, Gluten"
                      value={aiMealPlanData.allergies}
                      onChange={(e) => setAiMealPlanData({...aiMealPlanData, allergies: e.target.value})}
                    />
                  </div>

                  <div className="form-group">
                    <label>Daily Calorie Target (optional)</label>
                    <input
                      type="number"
                      placeholder="Leave empty to use your profile's calorie target"
                      value={aiMealPlanData.calorie_target}
                      onChange={(e) => setAiMealPlanData({...aiMealPlanData, calorie_target: e.target.value})}
                    />
                    {user?.daily_calories && (
                      <div style={{ color: '#888', fontSize: '14px', marginTop: '8px' }}>
                        Your profile target: {Math.round(user.daily_calories)} kcal/day
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                    <button
                      className="secondary-btn"
                      onClick={() => {
                        setMealPlanType('');
                        setAiMealPlanData({ duration: 7, dietary_preferences: '', allergies: '', calorie_target: '' });
                      }}
                      disabled={generatingMealPlan}
                      style={{ flex: 1 }}
                    >
                      Back
                    </button>
                    <button
                      className="primary-btn"
                      onClick={generateAIMealPlan}
                      disabled={generatingMealPlan}
                      style={{ flex: 1 }}
                    >
                      {generatingMealPlan ? 'Generating...' : 'Generate Meal Plan'}
                    </button>
                  </div>
                </div>
              ) : mealPlanType === 'manual' ? (
                <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
                  <div className="form-group">
                    <label>Meal Plan Name</label>
                    <input
                      type="text"
                      placeholder="e.g., My Weekly Meal Plan"
                      value={manualMealPlanData.name}
                      onChange={(e) => setManualMealPlanData({...manualMealPlanData, name: e.target.value})}
                    />
                  </div>

                  <div className="form-group">
                    <label>Duration (days)</label>
                    <select
                      value={manualMealPlanData.duration}
                      onChange={(e) => {
                        const duration = parseInt(e.target.value);
                        setManualMealPlanData({...manualMealPlanData, duration});
                        initializeManualMealPlan(duration);
                      }}
                      style={{
                        width: '100%',
                        padding: '12px',
                        background: '#1a1a1a',
                        border: '1px solid #333',
                        borderRadius: '8px',
                        color: '#fff'
                      }}
                    >
                      <option value="3">3 Days</option>
                      <option value="7">7 Days (1 Week)</option>
                      <option value="14">14 Days (2 Weeks)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Start Date</label>
                    <input
                      type="date"
                      value={manualMealPlanData.start_date}
                      onChange={(e) => setManualMealPlanData({...manualMealPlanData, start_date: e.target.value})}
                      style={{
                        width: '100%',
                        padding: '12px',
                        background: '#1a1a1a',
                        border: '1px solid #333',
                        borderRadius: '8px',
                        color: '#fff'
                      }}
                    />
                  </div>

                  <div style={{ marginTop: '20px', color: '#888', fontSize: '14px' }}>
                    Add meals for each day (optional - you can fill in later):
                  </div>

                  {manualMealPlanData.days.map((day, dayIndex) => (
                    <div key={dayIndex} style={{ marginTop: '24px', padding: '16px', background: '#1a1a1a', borderRadius: '8px', border: '1px solid #333' }}>
                      <h4 style={{ color: '#22c55e', marginBottom: '16px' }}>Day {day.day}</h4>
                      
                      {['breakfast', 'morning_snack', 'lunch', 'afternoon_snack', 'dinner'].map(mealType => (
                        <div key={mealType} style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid #222' }}>
                          <div style={{ color: '#fff', fontSize: '14px', fontWeight: 'bold', marginBottom: '8px', textTransform: 'capitalize' }}>
                            {mealType.replace('_', ' ')}
                          </div>
                          
                          <input
                            type="text"
                            placeholder="Meal name"
                            value={day.meals[mealType].name}
                            onChange={(e) => updateManualMeal(dayIndex, mealType, 'name', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '8px',
                              marginBottom: '8px',
                              background: '#0a0a0a',
                              border: '1px solid #333',
                              borderRadius: '4px',
                              color: '#fff',
                              fontSize: '14px'
                            }}
                          />
                          
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '8px' }}>
                            <input
                              type="number"
                              placeholder="Cal"
                              value={day.meals[mealType].calories || ''}
                              onChange={(e) => updateManualMeal(dayIndex, mealType, 'calories', e.target.value)}
                              style={{
                                padding: '8px',
                                background: '#0a0a0a',
                                border: '1px solid #333',
                                borderRadius: '4px',
                                color: '#fff',
                                fontSize: '12px'
                              }}
                            />
                            <input
                              type="number"
                              placeholder="Protein"
                              value={day.meals[mealType].protein || ''}
                              onChange={(e) => updateManualMeal(dayIndex, mealType, 'protein', e.target.value)}
                              style={{
                                padding: '8px',
                                background: '#0a0a0a',
                                border: '1px solid #333',
                                borderRadius: '4px',
                                color: '#fff',
                                fontSize: '12px'
                              }}
                            />
                            <input
                              type="number"
                              placeholder="Carbs"
                              value={day.meals[mealType].carbs || ''}
                              onChange={(e) => updateManualMeal(dayIndex, mealType, 'carbs', e.target.value)}
                              style={{
                                padding: '8px',
                                background: '#0a0a0a',
                                border: '1px solid #333',
                                borderRadius: '4px',
                                color: '#fff',
                                fontSize: '12px'
                              }}
                            />
                            <input
                              type="number"
                              placeholder="Fat"
                              value={day.meals[mealType].fat || ''}
                              onChange={(e) => updateManualMeal(dayIndex, mealType, 'fat', e.target.value)}
                              style={{
                                padding: '8px',
                                background: '#0a0a0a',
                                border: '1px solid #333',
                                borderRadius: '4px',
                                color: '#fff',
                                fontSize: '12px'
                              }}
                            />
                          </div>
                        </div>
                      ))}
                      
                      <div style={{ color: '#22c55e', fontSize: '14px', marginTop: '12px' }}>
                        Daily Total: {Math.round(day.totals.calories)} cal | {Math.round(day.totals.protein)}g protein | {Math.round(day.totals.carbs)}g carbs | {Math.round(day.totals.fat)}g fat
                      </div>
                    </div>
                  ))}

                  <div style={{ display: 'flex', gap: '12px', marginTop: '24px', position: 'sticky', bottom: 0, background: '#0a0a0a', padding: '16px 0' }}>
                    <button
                      className="secondary-btn"
                      onClick={() => {
                        setMealPlanType('');
                        setManualMealPlanData({
                          name: '',
                          duration: 7,
                          start_date: new Date().toISOString().split('T')[0],
                          days: []
                        });
                      }}
                      disabled={generatingMealPlan}
                      style={{ flex: 1 }}
                    >
                      Back
                    </button>
                    <button
                      className="primary-btn"
                      onClick={createManualMealPlan}
                      disabled={generatingMealPlan}
                      style={{ flex: 1 }}
                    >
                      {generatingMealPlan ? 'Creating...' : 'Create Meal Plan'}
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render Profile Page
  const renderProfile = () => {
    const defaultGoals = [
      { goal_type: 'Weight Loss', current_progress: 75, target_value: 100, unit: '%' },
      { goal_type: 'Muscle Gain', current_progress: 50, target_value: 100, unit: '%' }
    ];
    
    const displayGoals = goals.length > 0 ? goals : defaultGoals;
    
    return (
      <div className="profile-container">
        <div className="profile-header">
          <h2 className="profile-title">Profile</h2>
          <button className="icon-btn settings-btn" onClick={() => setShowSettingsPage(true)}>⚙️</button>
        </div>

        <div className="profile-user-card">
          <div className="profile-avatar-large" onClick={openEditProfileModal} style={{ cursor: 'pointer' }}>
            {user?.profile_picture ? (
              <img src={user.profile_picture} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
            ) : (
              '👤'
            )}
          </div>
          <h3 className="profile-name">{user?.name || 'Jane Doe'}</h3>
          <p className="profile-member">Member Since 2023</p>
          <button className="btn-edit-profile" onClick={openEditProfileModal}>Edit Profile</button>
        </div>

        <div className="profile-section">
          <h3 className="section-title">My Goals</h3>
          {displayGoals.map((goal, index) => (
            <div key={index} className="goal-item">
              <div className="goal-header">
                <div className="goal-icon">🎯</div>
                <span className="goal-name">{goal.goal_type}</span>
                <span className="goal-percentage">{goal.current_progress}%</span>
              </div>
              <div className="goal-progress-bar">
                <div 
                  className="goal-progress-fill" 
                  style={{ width: `${goal.current_progress}%` }}
                ></div>
              </div>
            </div>
          ))}
          <button className="btn-manage">Manage Goals</button>
        </div>

        <div className="profile-section">
          <h3 className="section-title">My Measurements</h3>
          <div className="measurements-grid">
            <div className="measurement-item">
              <div className="measurement-value">{measurements?.weight || user?.weight || 150}lbs</div>
              <div className="measurement-label">Weight</div>
            </div>
            <div className="measurement-item">
              <div className="measurement-value">{measurements?.body_fat || 18}%</div>
              <div className="measurement-label">Body Fat</div>
            </div>
            <div className="measurement-item">
              <div className="measurement-value">{measurements?.bmi || 22.1}</div>
              <div className="measurement-label">BMI</div>
            </div>
          </div>
          <button className="btn-manage">View History</button>
        </div>

        <div className="profile-section">
          <h3 className="section-title">General</h3>
          <div className="settings-list">
            <div className="settings-item">
              <span>Notifications</span>
              <label className="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={notifications}
                  onChange={() => setNotifications(!notifications)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
            <div className="settings-item" onClick={() => setShowThemeModal(true)}>
              <span>Theme</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                  {theme.charAt(0).toUpperCase() + theme.slice(1)}
                </span>
                <span className="settings-arrow">›</span>
              </div>
            </div>
            <div className="settings-item">
              <span>Units</span>
              <span className="settings-arrow">›</span>
            </div>
            <div className="settings-item">
              <span>Privacy Policy</span>
              <span className="settings-arrow">›</span>
            </div>
          </div>
        </div>

        <button className="btn-logout" onClick={handleLogout}>
          <span className="logout-icon">🚪</span> Logout
        </button>

        {/* Theme Modal */}
        {showThemeModal && (
          <div className="modal-overlay" onClick={() => setShowThemeModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h3>Select Theme</h3>
              <div className="theme-options">
                {[
                  { value: 'system', icon: '🌓', label: 'System', desc: 'Match your device settings' },
                  { value: 'dark', icon: '🌙', label: 'Dark', desc: 'Dark theme for low light' },
                  { value: 'light', icon: '☀️', label: 'Light', desc: 'Light theme for daytime' }
                ].map((t) => (
                  <button
                    key={t.value}
                    className={`theme-option ${theme === t.value ? 'active' : ''}`}
                    onClick={() => {
                      setTheme(t.value);
                      localStorage.setItem('fitflow_theme', t.value);
                      setShowThemeModal(false);
                    }}
                  >
                    <div className="theme-option-content">
                      <span className="theme-icon">{t.icon}</span>
                      <div className="theme-text">
                        <span className="theme-label">{t.label}</span>
                        <span className="theme-desc">{t.desc}</span>
                      </div>
                    </div>
                    {theme === t.value && <span className="theme-check">✓</span>}
                  </button>
                ))}
              </div>
              <button className="modal-close" onClick={() => setShowThemeModal(false)}>Close</button>
            </div>
          </div>
        )}

        {/* Edit Profile Modal */}
        {showEditProfileModal && (
          <div className="modal-overlay" onClick={() => setShowEditProfileModal(false)}>
            <div className="modal-content edit-profile-modal" onClick={(e) => e.stopPropagation()}>
              <h3>Edit Profile</h3>
              
              {error && <div className="error-message">{error}</div>}
              {success && <div className="success-message">{success}</div>}
              
              <div className="edit-profile-form">
                {/* Profile Picture */}
                <div className="form-group profile-picture-section">
                  <label>Profile Picture</label>
                  <div className="profile-picture-upload">
                    <div 
                      className="profile-picture-preview" 
                      onClick={() => profilePictureInputRef.current?.click()}
                    >
                      {profilePicturePreview ? (
                        <img src={profilePicturePreview} alt="Profile Preview" />
                      ) : (
                        <span className="upload-placeholder">📷<br/>Click to upload</span>
                      )}
                    </div>
                    <input 
                      type="file" 
                      ref={profilePictureInputRef}
                      accept="image/*"
                      onChange={handleProfilePictureChange}
                      style={{ display: 'none' }}
                    />
                  </div>
                </div>

                {/* Name */}
                <div className="form-group">
                  <label>Name</label>
                  <input 
                    type="text" 
                    value={editProfileData.name || ''}
                    onChange={(e) => setEditProfileData({...editProfileData, name: e.target.value})}
                    placeholder="Enter your name"
                  />
                </div>

                {/* Age */}
                <div className="form-group">
                  <label>Age</label>
                  <input 
                    type="number" 
                    value={editProfileData.age || ''}
                    onChange={(e) => setEditProfileData({...editProfileData, age: parseInt(e.target.value) || ''})}
                    placeholder="Enter your age"
                  />
                </div>

                {/* Gender */}
                <div className="form-group">
                  <label>Gender</label>
                  <select 
                    value={editProfileData.gender || ''}
                    onChange={(e) => setEditProfileData({...editProfileData, gender: e.target.value})}
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                {/* Height */}
                <div className="form-group">
                  <label>Height (cm)</label>
                  <input 
                    type="number" 
                    value={editProfileData.height || ''}
                    onChange={(e) => setEditProfileData({...editProfileData, height: parseFloat(e.target.value) || ''})}
                    placeholder="Enter your height"
                  />
                </div>

                {/* Weight */}
                <div className="form-group">
                  <label>Weight (kg)</label>
                  <input 
                    type="number" 
                    value={editProfileData.weight || ''}
                    onChange={(e) => setEditProfileData({...editProfileData, weight: parseFloat(e.target.value) || ''})}
                    placeholder="Enter your weight"
                  />
                </div>

                {/* Goal Weight */}
                <div className="form-group">
                  <label>Goal Weight (kg)</label>
                  <input 
                    type="number" 
                    value={editProfileData.goal_weight || ''}
                    onChange={(e) => setEditProfileData({...editProfileData, goal_weight: parseFloat(e.target.value) || ''})}
                    placeholder="Enter your goal weight"
                  />
                </div>

                {/* Activity Level */}
                <div className="form-group">
                  <label>Activity Level</label>
                  <select 
                    value={editProfileData.activity_level || 'moderate'}
                    onChange={(e) => setEditProfileData({...editProfileData, activity_level: e.target.value})}
                  >
                    <option value="sedentary">Sedentary</option>
                    <option value="light">Light</option>
                    <option value="moderate">Moderate</option>
                    <option value="active">Active</option>
                    <option value="very_active">Very Active</option>
                  </select>
                </div>
              </div>

              <div className="modal-buttons">
                <button 
                  className="btn-save" 
                  onClick={handleEditProfileSubmit}
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
                <button 
                  className="modal-close" 
                  onClick={() => setShowEditProfileModal(false)}
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render Settings Page
  const renderSettings = () => {
    if (settingsSubPage === 'connected-apps') {
      return (
        <div className="settings-page">
          <div className="settings-header">
            <button className="back-btn" onClick={() => setSettingsSubPage('main')}>←</button>
            <h2>Connected Apps</h2>
            <div></div>
          </div>
          <div className="settings-content">
            <p style={{ textAlign: 'center', color: '#888', marginTop: '40px' }}>
              No connected apps yet.<br/>
              Connect third-party apps to sync your fitness data.
            </p>
          </div>
        </div>
      );
    }

    if (settingsSubPage === 'change-password') {
      const handleChangePassword = async () => {
        if (!currentPassword || !newPassword || !confirmPassword) {
          setError('All fields are required');
          return;
        }
        if (newPassword !== confirmPassword) {
          setError('New passwords do not match');
          return;
        }
        if (newPassword.length < 6) {
          setError('Password must be at least 6 characters');
          return;
        }
        
        setLoading(true);
        setError('');
        try {
          const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/user/password`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              current_password: currentPassword,
              new_password: newPassword
            })
          });
          
          if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to change password');
          }
          
          setSuccess('Password changed successfully!');
          setTimeout(() => {
            setSettingsSubPage('main');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
          }, 2000);
        } catch (err) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      
      return (
        <div className="settings-page">
          <div className="settings-header">
            <button className="back-btn" onClick={() => setSettingsSubPage('main')}>←</button>
            <h2>Change Password</h2>
            <div></div>
          </div>
          <div className="settings-content" style={{ padding: '20px' }}>
            {error && <div className="error-message">{error}</div>}
            {success && <div className="success-message">{success}</div>}
            
            <div className="form-group">
              <label>Current Password</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
              />
            </div>
            
            <div className="form-group">
              <label>New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
              />
            </div>
            
            <div className="form-group">
              <label>Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
              />
            </div>
            
            <button 
              className="btn-primary" 
              onClick={handleChangePassword}
              disabled={loading}
              style={{ width: '100%', marginTop: '20px' }}
            >
              {loading ? 'Changing...' : 'Change Password'}
            </button>
          </div>
        </div>
      );
    }

    if (settingsSubPage === 'help') {
      return (
        <div className="settings-page">
          <div className="settings-header">
            <button className="back-btn" onClick={() => setSettingsSubPage('main')}>←</button>
            <h2>Help Center & FAQ</h2>
            <div></div>
          </div>
          <div className="settings-content" style={{ padding: '20px' }}>
            <div className="faq-item" style={{ marginBottom: '20px' }}>
              <h3 style={{ color: '#22c55e', marginBottom: '10px' }}>How do I scan food?</h3>
              <p style={{ color: '#ccc' }}>Go to the Scan tab, then either take a photo or upload an image of your meal. Our AI will analyze it and provide nutritional information.</p>
            </div>
            <div className="faq-item" style={{ marginBottom: '20px' }}>
              <h3 style={{ color: '#22c55e', marginBottom: '10px' }}>How do I track my progress?</h3>
              <p style={{ color: '#ccc' }}>Your daily stats are displayed on the Home page. You can also view your goals and measurements in your Profile.</p>
            </div>
            <div className="faq-item" style={{ marginBottom: '20px' }}>
              <h3 style={{ color: '#22c55e', marginBottom: '10px' }}>Can I change my fitness goals?</h3>
              <p style={{ color: '#ccc' }}>Yes! Go to your Profile page and tap on any goal to update it. You can also add new goals.</p>
            </div>
          </div>
        </div>
      );
    }

    if (settingsSubPage === 'contact') {
      const handleContactSubmit = () => {
        if (!contactSubject || !contactMessage) {
          setError('Please fill in all fields');
          return;
        }
        setSuccess('Message sent! We\'ll get back to you soon.');
        setTimeout(() => {
          setSettingsSubPage('main');
          setContactMessage('');
          setContactSubject('');
        }, 2000);
      };
      
      return (
        <div className="settings-page">
          <div className="settings-header">
            <button className="back-btn" onClick={() => setSettingsSubPage('main')}>←</button>
            <h2>Contact Support</h2>
            <div></div>
          </div>
          <div className="settings-content" style={{ padding: '20px' }}>
            {error && <div className="error-message">{error}</div>}
            {success && <div className="success-message">{success}</div>}
            
            <div className="form-group">
              <label>Subject</label>
              <input
                type="text"
                value={contactSubject}
                onChange={(e) => setContactSubject(e.target.value)}
                placeholder="What can we help you with?"
              />
            </div>
            
            <div className="form-group">
              <label>Message</label>
              <textarea
                value={contactMessage}
                onChange={(e) => setContactMessage(e.target.value)}
                placeholder="Describe your issue or question..."
                rows="6"
                style={{ resize: 'vertical' }}
              />
            </div>
            
            <button 
              className="btn-primary" 
              onClick={handleContactSubmit}
              style={{ width: '100%', marginTop: '20px' }}
            >
              Send Message
            </button>
          </div>
        </div>
      );
    }

    // Main Settings Page
    const handleDeleteAccount = async () => {
      if (!window.confirm('Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently deleted.')) {
        return;
      }
      
      setLoading(true);
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/user/account`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Failed to delete account');
        }
        
        // Logout and clear data
        localStorage.removeItem('fitflow_token');
        setToken(null);
        setUser(null);
        setCurrentPage('login');
      } catch (err) {
        setError('Failed to delete account. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    return (
      <div className="settings-page">
        <div className="settings-header">
          <button className="back-btn" onClick={() => setShowSettingsPage(false)}>←</button>
          <h2>Settings</h2>
          <div></div>
        </div>
        
        <div className="settings-content">
          {/* Notifications Section */}
          <div className="settings-section">
            <h3 className="section-title">Notifications</h3>
            <div className="settings-list">
              <div className="settings-item">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span className="settings-icon">🔔</span>
                  <span>Workout Reminders</span>
                </div>
                <label className="toggle-switch">
                  <input 
                    type="checkbox" 
                    checked={workoutReminders}
                    onChange={() => setWorkoutReminders(!workoutReminders)}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>
              <div className="settings-item">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span className="settings-icon">🔊</span>
                  <span>App Updates</span>
                </div>
                <label className="toggle-switch">
                  <input 
                    type="checkbox" 
                    checked={appUpdates}
                    onChange={() => setAppUpdates(!appUpdates)}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>

          {/* Privacy Section */}
          <div className="settings-section">
            <h3 className="section-title">Privacy</h3>
            <div className="settings-list">
              <div className="settings-item" onClick={() => setSettingsSubPage('connected-apps')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span className="settings-icon">🔗</span>
                  <span>Connected Apps</span>
                </div>
                <span className="settings-arrow">›</span>
              </div>
            </div>
          </div>

          {/* Account Section */}
          <div className="settings-section">
            <h3 className="section-title">Account</h3>
            <div className="settings-list">
              <div className="settings-item" onClick={() => setSettingsSubPage('change-password')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span className="settings-icon">🔒</span>
                  <span>Change Password</span>
                </div>
                <span className="settings-arrow">›</span>
              </div>
              <div className="settings-item" onClick={handleDeleteAccount}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span className="settings-icon">🗑️</span>
                  <span style={{ color: '#ef4444' }}>Delete Account</span>
                </div>
                <span className="settings-arrow">›</span>
              </div>
              <div className="settings-item" onClick={() => setSettingsSubPage('help')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span className="settings-icon">❓</span>
                  <span>Help Center & FAQ</span>
                </div>
                <span className="settings-arrow">›</span>
              </div>
              <div className="settings-item" onClick={() => setSettingsSubPage('contact')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span className="settings-icon">✉️</span>
                  <span>Contact Support</span>
                </div>
                <span className="settings-arrow">›</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Bottom Navigation
  const renderBottomNav = () => (
    <nav className="bottom-nav">
      <button 
        className={currentPage === 'home' ? 'nav-item active' : 'nav-item'}
        onClick={() => setCurrentPage('home')}
      >
        <span className="nav-icon">🏠</span>
        <span className="nav-label">Home</span>
      </button>
      
      <button 
        className={currentPage === 'scan' ? 'nav-item active' : 'nav-item'}
        onClick={() => setCurrentPage('scan')}
      >
        <span className="nav-icon">📷</span>
        <span className="nav-label">Scan</span>
      </button>
      
      <button 
        className={currentPage === 'workout' ? 'nav-item active' : 'nav-item'}
        onClick={() => setCurrentPage('workout')}
      >
        <span className="nav-icon">💪</span>
        <span className="nav-label">Workout</span>
      </button>
      
      <button 
        className={currentPage === 'mealplan' ? 'nav-item active' : 'nav-item'}
        onClick={() => setCurrentPage('mealplan')}
      >
        <span className="nav-icon">🍽️</span>
        <span className="nav-label">Meal Plan</span>
      </button>
      
      <button 
        className={currentPage === 'profile' ? 'nav-item active' : 'nav-item'}
        onClick={() => setCurrentPage('profile')}
      >
        <span className="nav-icon">👤</span>
        <span className="nav-label">Profile</span>
      </button>
    </nav>
  );

  // Main render
  return (
    <div className="App">
      {!token ? (
        currentPage === 'login' ? renderLogin() : renderRegister()
      ) : (
        <>
          {showSettingsPage ? (
            renderSettings()
          ) : (
            <>
              <div className="app-content">
                {currentPage === 'home' && renderHome()}
                {currentPage === 'scan' && renderScanner()}
                {currentPage === 'workout' && renderWorkout()}
                {currentPage === 'mealplan' && renderMealPlan()}
                {currentPage === 'profile' && renderProfile()}
              </div>
              {renderBottomNav()}
            </>
          )}
        </>
      )}
    </div>
  );
}

export default App;