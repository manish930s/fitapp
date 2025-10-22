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
  const chatMessagesContainerRef = useRef(null);
  
  // Manual meal plan single-day entry state
  const [currentManualDay, setCurrentManualDay] = useState(0);
  const [showAddMealForm, setShowAddMealForm] = useState({ show: false, mealType: '', dayIndex: 0 });
  const [editingMeal, setEditingMeal] = useState({ show: false, mealType: '', dayIndex: 0, meal: null });
  const [tempMealData, setTempMealData] = useState({
    name: '',
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0
  });
  
  // Workout state
  const [exercises, setExercises] = useState([]);
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [workoutSessions, setWorkoutSessions] = useState([]);
  const [currentWorkoutSets, setCurrentWorkoutSets] = useState([]);
  const [exerciseHistory, setExerciseHistory] = useState(null);
  const [exerciseStats, setExerciseStats] = useState(null);
  const [workoutDashboardStats, setWorkoutDashboardStats] = useState(null);
  const [showWorkoutDetail, setShowWorkoutDetail] = useState(false);
  const [workoutNotes, setWorkoutNotes] = useState('');
  const [restTimer, setRestTimer] = useState(0);
  const [showExerciseSearch, setShowExerciseSearch] = useState(false);
  const [exerciseSearchQuery, setExerciseSearchQuery] = useState('');
  const [restTimerActive, setRestTimerActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [showQuickStartModal, setShowQuickStartModal] = useState(false);
  const [progressTimePeriod, setProgressTimePeriod] = useState('all'); // 1month, 3months, 6months, all
  const restTimerIntervalRef = useRef(null);
  
  // Auto-tracking state
  const [workoutStartTime, setWorkoutStartTime] = useState(null);
  const [workoutDuration, setWorkoutDuration] = useState(0);
  const [toastMessage, setToastMessage] = useState(null);
  const [showStepsModal, setShowStepsModal] = useState(false);
  const [showWaterModal, setShowWaterModal] = useState(false);
  const [manualStepsInput, setManualStepsInput] = useState('');
  const [manualWaterInput, setManualWaterInput] = useState('');
  const workoutTimerIntervalRef = useRef(null);
  
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
      fetchTodayFood();
    }
    if ((currentPage === 'home' || currentPage === 'chatbot') && token) {
      fetchChatHistory();
    }
    if (currentPage === 'profile' && token) {
      fetchGoals();
      fetchMeasurements();
    }
    if (currentPage === 'mealplan' && token) {
      fetchMealPlans();
    }
    if (currentPage === 'workout' && token) {
      fetchExercises(selectedCategory);
      fetchWorkoutDashboardStats();
    }
  }, [currentPage, token, selectedCategory]);

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

  const fetchDailyStats = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/stats/daily`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const stats = await response.json();
        setDailyStats(stats);
      }
    } catch (err) {
      console.error('Error fetching daily stats:', err);
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
        // Scroll to bottom after loading chat history with longer delay
        setTimeout(() => {
          if (chatMessagesContainerRef.current) {
            chatMessagesContainerRef.current.scrollTop = chatMessagesContainerRef.current.scrollHeight;
          }
        }, 300);
      }
    } catch (err) {
      console.error('Error fetching chat history:', err);
    }
  };

  // Auto-scroll chatbot to bottom
  const scrollChatToBottom = () => {
    if (chatMessagesContainerRef.current) {
      // Use requestAnimationFrame for smoother scrolling after DOM updates
      requestAnimationFrame(() => {
        if (chatMessagesContainerRef.current) {
          chatMessagesContainerRef.current.scrollTop = chatMessagesContainerRef.current.scrollHeight;
        }
      });
    }
  };

  // Auto-scroll when messages change or chatbot page opens
  useEffect(() => {
    if (currentPage === 'chatbot') {
      // Delay to ensure DOM is fully rendered
      setTimeout(() => {
        scrollChatToBottom();
      }, 150);
    }
  }, [chatMessages, isChatLoading, currentPage]);

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
    
    // Scroll to bottom after adding user message
    setTimeout(() => {
      if (chatMessagesContainerRef.current) {
        chatMessagesContainerRef.current.scrollTop = chatMessagesContainerRef.current.scrollHeight;
      }
    }, 100);
    
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
        
        // Scroll to bottom after receiving AI response
        setTimeout(() => {
          if (chatMessagesContainerRef.current) {
            chatMessagesContainerRef.current.scrollTop = chatMessagesContainerRef.current.scrollHeight;
          }
        }, 100);
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

      // Check if at least one meal type has at least one entry
      const mealTypes = ['breakfast', 'morning_snack', 'lunch', 'afternoon_snack', 'dinner'];
      const hasMealForAnyType = mealTypes.some(mealType => 
        manualMealPlanData.days.some(day => 
          day.meals[mealType]?.name?.trim()
        )
      );
      
      if (!hasMealForAnyType) {
        setError('Please add at least one meal (any type) to your plan');
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

  // Meal management functions for editing meal plans
  const openAddMealForm = (mealType, dayIndex) => {
    console.log('Opening add meal form:', mealType, dayIndex); // Debug log
    setTempMealData({
      name: '',
      calories: 0,
      protein: 0,
      carbs: 0,
      fat: 0
    });
    setEditingMeal({ show: false, mealType: '', dayIndex: 0, meal: null });
    setShowAddMealForm({ show: true, mealType, dayIndex });
  };

  const openEditMealForm = (mealType, dayIndex, meal) => {
    console.log('Opening edit meal form:', mealType, dayIndex, meal); // Debug log
    setTempMealData({
      name: meal.name || '',
      calories: meal.calories || 0,
      protein: meal.protein || 0,
      carbs: meal.carbs || 0,
      fat: meal.fat || 0
    });
    setShowAddMealForm({ show: false, mealType: '', dayIndex: 0 });
    setEditingMeal({ show: true, mealType, dayIndex, meal });
  };

  const saveMealToSelectedPlan = async (mealType, dayIndex) => {
    console.log('Saving meal:', mealType, dayIndex, tempMealData); // Debug log
    
    if (!tempMealData.name.trim()) {
      setError('Please enter a meal name');
      return;
    }

    try {
      const day = selectedMealPlan.days[dayIndex];
      // Support both 'day' and 'day_number' field names
      const dayNumber = day.day_number || day.day;

      console.log('Day number:', dayNumber, 'Day object:', day); // Debug log

      // Prepare meal data to send to backend
      const mealData = {
        name: tempMealData.name.trim(),
        calories: parseFloat(tempMealData.calories) || 0,
        protein: parseFloat(tempMealData.protein) || 0,
        carbs: parseFloat(tempMealData.carbs) || 0,
        fat: parseFloat(tempMealData.fat) || 0,
        description: '',
        ingredients: []
      };

      console.log('Sending to backend:', mealData); // Debug log

      // Update backend using the correct API format
      const url = `${BACKEND_URL}/api/mealplan/${selectedMealPlan.plan_id}/day/${dayNumber}/meal?meal_category=${mealType}`;
      console.log('API URL:', url); // Debug log
      
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(mealData)
      });

      console.log('Response status:', response.status); // Debug log

      if (response.ok) {
        setSuccess(editingMeal.show ? 'Meal updated successfully' : 'Meal added successfully');
        setShowAddMealForm({ show: false, mealType: '', dayIndex: 0 });
        setEditingMeal({ show: false, mealType: '', dayIndex: 0, meal: null });
        setError('');
        // Refresh meal plan details
        await fetchMealPlanDetails(selectedMealPlan.plan_id);
      } else {
        const errorData = await response.json();
        console.error('Error response:', errorData); // Debug log
        setError(errorData.detail || 'Failed to save meal');
      }
    } catch (err) {
      console.error('Error saving meal:', err);
      setError('Failed to save meal: ' + err.message);
    }
  };

  const deleteMealFromPlan = async (mealType, dayIndex) => {
    if (!window.confirm('Are you sure you want to delete this meal?')) {
      return;
    }

    try {
      const day = selectedMealPlan.days[dayIndex];
      // Support both 'day' and 'day_number' field names
      const dayNumber = day.day_number || day.day;

      // Send empty meal data to backend to clear the meal
      const emptyMealData = {
        name: '',
        calories: 0,
        protein: 0,
        carbs: 0,
        fat: 0,
        description: '',
        ingredients: []
      };

      // Update backend
      const response = await fetch(
        `${BACKEND_URL}/api/mealplan/${selectedMealPlan.plan_id}/day/${dayNumber}/meal?meal_category=${mealType}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(emptyMealData)
        }
      );

      if (response.ok) {
        setSuccess('Meal deleted successfully');
        // Refresh meal plan details
        await fetchMealPlanDetails(selectedMealPlan.plan_id);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to delete meal');
      }
    } catch (err) {
      console.error('Error deleting meal:', err);
      setError('Failed to delete meal');
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

  const deleteFoodScan = async (scanId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/food/scan/${scanId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        showToast('✓ Food scan deleted successfully');
        // Refresh food data
        fetchFoodHistory();
        fetchTodayFood();
        fetchDailyStats();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to delete food scan');
      }
    } catch (err) {
      console.error('Error deleting food scan:', err);
      setError('Failed to delete food scan');
    }
  };

  // Workout functions
  const fetchExercises = async (category = null) => {
    try {
      let url = `${BACKEND_URL}/api/workouts/exercises`;
      if (category && category !== 'All') {
        url += `?category=${category}`;
      }
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setExercises(data.exercises || []);
      }
    } catch (err) {
      console.error('Error fetching exercises:', err);
    }
  };

  const fetchExerciseDetail = async (exerciseId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/workouts/exercises/${exerciseId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedExercise(data);
        setShowWorkoutDetail(true);
        
        // Auto-populate workout sets from last session if available
        if (data.last_session && data.last_session.sets && data.last_session.sets.length > 0) {
          const lastSets = data.last_session.sets.map((set, index) => ({
            set_number: index + 1,
            reps: set.reps || 10,
            weight: set.weight || 0,
            rpe: set.rpe || 5
          }));
          setCurrentWorkoutSets(lastSets);
        } else {
          // Start with one empty set
          setCurrentWorkoutSets([{
            set_number: 1,
            reps: 10,
            weight: 0,
            rpe: 5
          }]);
        }
        
        // Fetch history and stats for this exercise
        await fetchExerciseHistory(exerciseId);
        await fetchExerciseStats(exerciseId);
      }
    } catch (err) {
      console.error('Error fetching exercise detail:', err);
    }
  };

  const fetchExerciseHistory = async (exerciseId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/workouts/exercises/${exerciseId}/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setExerciseHistory(data);
      }
    } catch (err) {
      console.error('Error fetching exercise history:', err);
    }
  };

  const fetchExerciseStats = async (exerciseId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/workouts/exercises/${exerciseId}/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setExerciseStats(data);
      }
    } catch (err) {
      console.error('Error fetching exercise stats:', err);
    }
  };

  const fetchWorkoutDashboardStats = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/workouts/dashboard/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setWorkoutDashboardStats(data);
      }
    } catch (err) {
      console.error('Error fetching workout dashboard stats:', err);
    }
  };

  const addWorkoutSet = () => {
    const lastSet = currentWorkoutSets[currentWorkoutSets.length - 1];
    const newSet = {
      set_number: currentWorkoutSets.length + 1,
      reps: lastSet ? lastSet.reps : 10,
      weight: lastSet ? lastSet.weight : 0,
      rpe: lastSet ? lastSet.rpe : 5
    };
    setCurrentWorkoutSets([...currentWorkoutSets, newSet]);
  };

  const updateWorkoutSet = (index, field, value) => {
    const updatedSets = [...currentWorkoutSets];
    updatedSets[index][field] = parseFloat(value) || 0;
    setCurrentWorkoutSets(updatedSets);
  };

  const removeWorkoutSet = (index) => {
    const updatedSets = currentWorkoutSets.filter((_, i) => i !== index);
    // Renumber sets
    const renumberedSets = updatedSets.map((set, i) => ({ ...set, set_number: i + 1 }));
    setCurrentWorkoutSets(renumberedSets);
  };

  const saveWorkoutSession = async () => {
    if (!selectedExercise || currentWorkoutSets.length === 0) {
      setError('Please add at least one set to save the workout');
      return;
    }

    setLoading(true);
    try {
      // Calculate workout duration in minutes
      const durationMinutes = workoutStartTime 
        ? Math.round((Date.now() - workoutStartTime) / 60000)
        : 0;
      
      const response = await fetch(`${BACKEND_URL}/api/workouts/sessions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          exercise_id: selectedExercise.exercise_id,
          sets: currentWorkoutSets,
          notes: workoutNotes,
          duration_minutes: durationMinutes
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Show auto-track notification
        if (data.auto_tracked && durationMinutes > 0) {
          showToast(`✓ Workout saved! ${durationMinutes} min added to active time`);
        } else {
          setSuccess('Workout saved successfully!');
          setTimeout(() => setSuccess(''), 3000);
        }
        
        setCurrentWorkoutSets([]);
        setWorkoutNotes('');
        
        // Reset workout timer
        setWorkoutStartTime(null);
        setWorkoutDuration(0);
        if (workoutTimerIntervalRef.current) {
          clearInterval(workoutTimerIntervalRef.current);
          workoutTimerIntervalRef.current = null;
        }
        
        // Refresh data
        await fetchExerciseHistory(selectedExercise.exercise_id);
        await fetchExerciseStats(selectedExercise.exercise_id);
        await fetchWorkoutDashboardStats();
        await fetchDailyStats(); // Refresh daily stats to show updated active minutes
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to save workout');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const startRestTimer = (seconds) => {
    setRestTimer(seconds);
    setRestTimerActive(true);
  };

  useEffect(() => {
    if (restTimerActive && restTimer > 0) {
      restTimerIntervalRef.current = setInterval(() => {
        setRestTimer(prev => {
          if (prev <= 1) {
            setRestTimerActive(false);
            clearInterval(restTimerIntervalRef.current);
            // Play sound or vibration
            if ('vibrate' in navigator) {
              navigator.vibrate(500);
            }
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else if (!restTimerActive && restTimerIntervalRef.current) {
      clearInterval(restTimerIntervalRef.current);
    }

    return () => {
      if (restTimerIntervalRef.current) {
        clearInterval(restTimerIntervalRef.current);
      }
    };
  }, [restTimerActive, restTimer]);

  // Workout timer - start when opening workout detail page
  useEffect(() => {
    if (showWorkoutDetail && selectedExercise && !workoutStartTime) {
      // Start workout timer
      setWorkoutStartTime(Date.now());
      
      // Update duration every second
      workoutTimerIntervalRef.current = setInterval(() => {
        setWorkoutDuration(prev => prev + 1);
      }, 1000);
    } else if (!showWorkoutDetail && workoutTimerIntervalRef.current) {
      // Stop timer if leaving workout detail page
      clearInterval(workoutTimerIntervalRef.current);
      workoutTimerIntervalRef.current = null;
      setWorkoutStartTime(null);
      setWorkoutDuration(0);
    }

    return () => {
      if (workoutTimerIntervalRef.current) {
        clearInterval(workoutTimerIntervalRef.current);
      }
    };
  }, [showWorkoutDetail, selectedExercise]);


  const startVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError('Voice input is not supported in your browser');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.toLowerCase();
      // Parse voice input for reps and weight
      // Example: "10 reps 50 kilos" or "8 reps 100 pounds"
      const repsMatch = transcript.match(/(\d+)\s*(rep|reps)/i);
      const weightMatch = transcript.match(/(\d+)\s*(kg|kilo|kilos|pound|pounds|lb|lbs)/i);
      
      if (repsMatch || weightMatch) {
        const lastIndex = currentWorkoutSets.length - 1;
        if (lastIndex >= 0) {
          const updatedSets = [...currentWorkoutSets];
          if (repsMatch) {
            updatedSets[lastIndex].reps = parseInt(repsMatch[1]);
          }
          if (weightMatch) {
            updatedSets[lastIndex].weight = parseFloat(weightMatch[1]);
          }
          setCurrentWorkoutSets(updatedSets);
          setSuccess('Voice input captured!');
          setTimeout(() => setSuccess(''), 2000);
        }
      } else {
        setError('Could not understand. Try saying "10 reps 50 kilos"');
        setTimeout(() => setError(''), 3000);
      }
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      setError('Voice input error: ' + event.error);
      setTimeout(() => setError(''), 3000);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const calculate1RM = (weight, reps) => {
    if (!weight || !reps || reps === 0) return 0;
    // Epley formula: 1RM = weight × (1 + reps/30)
    return Math.round(weight * (1 + reps / 30));
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
        
        // Show auto-track notification
        if (data.auto_tracked) {
          showToast(`✓ ${data.food_name} scanned! ${data.calories} cal added to daily intake`);
        } else {
          setSuccess('Food analyzed successfully!');
        }
        
        setTimeout(() => {
          fetchFoodHistory();
          fetchTodayFood();
          fetchDailyStats(); // Refresh daily stats to show updated calories
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

  // Helper function to calculate progress percentage
  const calculateProgress = (current, target) => {
    if (!current || !target || target === 0) return 0;
    const progress = Math.round((current / target) * 100);
    return Math.min(progress, 100); // Cap at 100%
  };

  // Toast notification helper
  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // Quick increment functions for steps and water
  const incrementSteps = async (amount) => {
    try {
      const formData = new FormData();
      formData.append('field', 'steps');
      formData.append('amount', amount);
      
      const response = await fetch(`${BACKEND_URL}/api/stats/daily/increment`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const data = await response.json();
      
      if (response.ok) {
        await fetchDailyStats();
        showToast(`✓ Added ${amount} steps`);
      }
    } catch (error) {
      console.error('Error incrementing steps:', error);
    }
  };
  
  const incrementWater = async (amount) => {
    try {
      const formData = new FormData();
      formData.append('field', 'water_intake');
      formData.append('amount', amount);
      
      const response = await fetch(`${BACKEND_URL}/api/stats/daily/increment`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const data = await response.json();
      
      if (response.ok) {
        await fetchDailyStats();
        showToast(`✓ Added ${amount}ml water`);
      }
    } catch (error) {
      console.error('Error incrementing water:', error);
    }
  };
  
  // Manual input handlers for steps and water
  const handleManualStepsSubmit = async () => {
    const amount = parseInt(manualStepsInput);
    if (amount > 0) {
      await incrementSteps(amount);
      setShowStepsModal(false);
      setManualStepsInput('');
    }
  };
  
  const handleManualWaterSubmit = async () => {
    const amount = parseInt(manualWaterInput);
    if (amount > 0) {
      await incrementWater(amount);
      setShowWaterModal(false);
      setManualWaterInput('');
    }
  };


  // Render Home/Dashboard Page
  const renderHome = () => {
    // Calculate dynamic progress values
    const STEPS_GOAL = 10000;
    const ACTIVE_MINUTES_GOAL = 60;
    
    const stepsProgress = calculateProgress(dailyStats?.steps || 0, STEPS_GOAL);
    const caloriesProgress = calculateProgress(todayFood?.total_calories || 0, dailyCalories?.daily_target || 2000);
    const activeProgress = calculateProgress(dailyStats?.active_minutes || 0, ACTIVE_MINUTES_GOAL);
    
    return (
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
          <div className="stat-ring" style={{'--progress': stepsProgress}}>
            <span className="stat-value">{dailyStats?.steps || 0}</span>
          </div>
          <p className="stat-label">Steps</p>
        </div>
        
        <div className="stat-card">
          <div className="stat-ring" style={{'--progress': caloriesProgress}}>
            <span className="stat-value">{todayFood?.total_calories || 0}</span>
          </div>
          <p className="stat-label">Calories</p>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">⚡</div>
          <div className="stat-info">
            <p className="stat-value">{streak || 0} days</p>
            <p className="stat-label">Streak</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-ring" style={{'--progress': activeProgress}}>
            <span className="stat-value">{dailyStats?.active_minutes || 0}m</span>
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

      {/* Enhanced Calorie Tracking */}
      {dailyCalories && (
        <div className="calorie-info">
          <h3>Calorie Tracking</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '16px' }}>
            <div style={{ textAlign: 'center', padding: '12px', background: '#0a0a0a', borderRadius: '12px' }}>
              <p style={{ fontSize: '14px', color: '#888', marginBottom: '4px' }}>Consumed</p>
              <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#22c55e' }}>{dailyStats?.calories_consumed || 0}</p>
              <p style={{ fontSize: '12px', color: '#888' }}>kcal</p>
            </div>
            <div style={{ textAlign: 'center', padding: '12px', background: '#0a0a0a', borderRadius: '12px' }}>
              <p style={{ fontSize: '14px', color: '#888', marginBottom: '4px' }}>Burned</p>
              <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#f97316' }}>{dailyStats?.calories_burned || 0}</p>
              <p style={{ fontSize: '12px', color: '#888' }}>kcal</p>
            </div>
            <div style={{ textAlign: 'center', padding: '12px', background: '#0a0a0a', borderRadius: '12px', border: '2px solid #22c55e' }}>
              <p style={{ fontSize: '14px', color: '#888', marginBottom: '4px' }}>Net</p>
              <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#fff' }}>
                {(dailyStats?.calories_consumed || 0) - (dailyStats?.calories_burned || 0)}
              </p>
              <p style={{ fontSize: '12px', color: '#888' }}>kcal</p>
            </div>
          </div>
          <p className="calorie-target" style={{ marginTop: '16px' }}>
            Target: {Math.round(dailyCalories.daily_target)} kcal | BMR: {Math.round(dailyCalories.bmr)}
          </p>
        </div>
      )}
      
      {/* Quick Add Actions for Steps and Water */}
      <div style={{ padding: '20px' }}>
        <h3 style={{ marginBottom: '16px', fontSize: '18px' }}>Quick Actions</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          {/* Steps Quick Add */}
          <div style={{ background: '#0a0a0a', padding: '16px', borderRadius: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '24px' }}>🚶</span>
              <span style={{ fontSize: '18px', fontWeight: 'bold' }}>{dailyStats?.steps || 0}</span>
            </div>
            <p style={{ fontSize: '14px', color: '#888', marginBottom: '12px' }}>Steps</p>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
              <button 
                onClick={() => incrementSteps(500)}
                style={{
                  flex: 1,
                  padding: '8px',
                  background: '#22c55e',
                  color: '#000',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                +500
              </button>
              <button 
                onClick={() => incrementSteps(1000)}
                style={{
                  flex: 1,
                  padding: '8px',
                  background: '#22c55e',
                  color: '#000',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                +1000
              </button>
            </div>
            <button 
              onClick={() => setShowStepsModal(true)}
              style={{
                width: '100%',
                padding: '8px',
                background: 'transparent',
                color: '#22c55e',
                border: '1px solid #22c55e',
                borderRadius: '8px',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              Custom
            </button>
          </div>
          
          {/* Water Quick Add */}
          <div style={{ background: '#0a0a0a', padding: '16px', borderRadius: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '24px' }}>💧</span>
              <span style={{ fontSize: '18px', fontWeight: 'bold' }}>{dailyStats?.water_intake || 0}ml</span>
            </div>
            <p style={{ fontSize: '14px', color: '#888', marginBottom: '12px' }}>Water</p>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
              <button 
                onClick={() => incrementWater(250)}
                style={{
                  flex: 1,
                  padding: '8px',
                  background: '#3b82f6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                +250ml
              </button>
              <button 
                onClick={() => incrementWater(500)}
                style={{
                  flex: 1,
                  padding: '8px',
                  background: '#3b82f6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                +500ml
              </button>
            </div>
            <button 
              onClick={() => setShowWaterModal(true)}
              style={{
                width: '100%',
                padding: '8px',
                background: 'transparent',
                color: '#3b82f6',
                border: '1px solid #3b82f6',
                borderRadius: '8px',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              Custom
            </button>
          </div>
        </div>
      </div>

      {/* Floating Chatbot Button */}
      <button 
        className="floating-chat-btn"
        onClick={() => setCurrentPage('chatbot')}
        title="Chat with AI Fitness Coach"
      >
        <span style={{ fontSize: '28px' }}>💬</span>
      </button>
      
      {/* Custom Steps Modal */}
      {showStepsModal && (
        <div className="modal-overlay" onClick={() => setShowStepsModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '400px' }}>
            <h3>Add Steps</h3>
            <input
              type="number"
              placeholder="Enter number of steps"
              value={manualStepsInput}
              onChange={(e) => setManualStepsInput(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                background: '#0a0a0a',
                border: '1px solid #333',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '16px',
                marginTop: '16px'
              }}
            />
            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <button
                className="secondary-btn"
                onClick={() => setShowStepsModal(false)}
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <button
                className="primary-btn"
                onClick={handleManualStepsSubmit}
                style={{ flex: 1 }}
              >
                Add Steps
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Custom Water Modal */}
      {showWaterModal && (
        <div className="modal-overlay" onClick={() => setShowWaterModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '400px' }}>
            <h3>Add Water</h3>
            <input
              type="number"
              placeholder="Enter amount in ml"
              value={manualWaterInput}
              onChange={(e) => setManualWaterInput(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                background: '#0a0a0a',
                border: '1px solid #333',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '16px',
                marginTop: '16px'
              }}
            />
            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <button
                className="secondary-btn"
                onClick={() => setShowWaterModal(false)}
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <button
                className="primary-btn"
                onClick={handleManualWaterSubmit}
                style={{ flex: 1 }}
              >
                Add Water
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    );
  };

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

        <div className="chatbot-messages-container" ref={chatMessagesContainerRef}>
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
                {/* User Message - Display FIRST */}
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
                
                {/* AI Message - Display SECOND */}
                {msg.assistant_message && (
                  <div className="ai-message-bubble">
                    <div className="ai-avatar">🤖</div>
                    <div className="message-content">
                      <div className="message-header">AI Coach - {new Date(msg.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</div>
                      <div className="message-text">{msg.assistant_message}</div>
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
  const renderWorkout = () => {
    // Show workout detail page if an exercise is selected
    if (showWorkoutDetail && selectedExercise) {
      return (
        <div className="workout-detail-container">
          {/* Header */}
          <div className="page-header">
            <button className="icon-btn" onClick={() => {
              setShowWorkoutDetail(false);
              setSelectedExercise(null);
              setCurrentWorkoutSets([]);
              setWorkoutNotes('');
            }}>
              ←
            </button>
            <h2>{selectedExercise.name}</h2>
            <button className="icon-btn">⋮</button>
          </div>

          <div className="workout-detail-content">
            {/* Exercise Image/Video Placeholder */}
            <div className="exercise-media">
              {selectedExercise.image_url ? (
                <img 
                  src={selectedExercise.image_url} 
                  alt={selectedExercise.name}
                  style={{
                    width: '100%',
                    height: '250px',
                    objectFit: 'cover',
                    borderRadius: '12px'
                  }}
                />
              ) : (
                <div className="exercise-placeholder-large">
                  <span style={{ fontSize: '80px' }}>🏋️</span>
                </div>
              )}
            </div>

            {/* Proper Form Section */}
            <div className="workout-section">
              <h3>✓ Proper Form</h3>
              <div className="form-images">
                <div className="form-image-placeholder">
                  <span>📸 Position 1</span>
                </div>
                <div className="form-image-placeholder">
                  <span>📸 Position 2</span>
                </div>
              </div>
            </div>

            {/* Collapsible Sections */}
            <div className="collapsible-section">
              <div className="collapsible-header">
                <h3>💪 Benefits</h3>
                <span>›</span>
              </div>
              <div className="collapsible-content">
                <p>{selectedExercise.description || 'Builds strength and muscle mass'}</p>
                <p><strong>Target Muscles:</strong> {selectedExercise.target_muscles?.join(', ') || 'Primary muscle groups'}</p>
              </div>
            </div>

            <div className="collapsible-section">
              <div className="collapsible-header">
                <h3>⚠️ Common Mistakes</h3>
                <span>›</span>
              </div>
              <div className="collapsible-content">
                <ul>
                  {selectedExercise.safety_tips?.map((tip, index) => (
                    <li key={index}>{tip}</li>
                  )) || <li>Always warm up before starting</li>}
                </ul>
              </div>
            </div>

            <div className="collapsible-section">
              <div className="collapsible-header">
                <h3>📈 Progression Tips</h3>
                <span>›</span>
              </div>
              <div className="collapsible-content">
                <ul>
                  {selectedExercise.instructions?.map((instruction, index) => (
                    <li key={index}>{instruction}</li>
                  )) || <li>Gradually increase weight over time</li>}
                </ul>
              </div>
            </div>

            {/* Track Your Session */}
            <div className="workout-section">
              <h3>📝 Track Your Session</h3>
              
              {/* Workout Duration Timer */}
              {workoutStartTime && (
                <div style={{
                  backgroundColor: '#1a1a2e',
                  border: '1px solid #22c55e',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '15px',
                  fontSize: '14px',
                  color: '#22c55e',
                  textAlign: 'center'
                }}>
                  <strong>⏱️ Workout Duration:</strong> {Math.floor(workoutDuration / 60)}:{(workoutDuration % 60).toString().padStart(2, '0')}
                  <br />
                  <small style={{color: '#888'}}>
                    Time tracking automatically - will count as active minutes
                  </small>
                </div>
              )}
              
              {/* Progress indicator from last session */}
              {selectedExercise.last_session && selectedExercise.last_session.max_weight > 0 && (
                <div style={{
                  backgroundColor: '#1a3a2a',
                  border: '1px solid #10b981',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '15px',
                  fontSize: '14px',
                  color: '#10b981'
                }}>
                  <strong>💪 Last Session:</strong> {selectedExercise.last_session.max_weight}{user?.weight_unit || 'kg'} × {selectedExercise.last_session.sets?.length || 0} sets
                  <br />
                  <small style={{color: '#888'}}>
                    Total Volume: {selectedExercise.last_session.total_volume}{user?.weight_unit || 'kg'}
                  </small>
                </div>
              )}
              
              {/* Rest Timer */}
              {restTimerActive && (
                <div className="rest-timer-display">
                  <div className="timer-circle">
                    <span className="timer-value">{restTimer}s</span>
                  </div>
                  <button className="btn-secondary" onClick={() => {
                    setRestTimerActive(false);
                    setRestTimer(0);
                  }}>
                    Stop Timer
                  </button>
                </div>
              )}

              {/* Sets Input */}
              {currentWorkoutSets.map((set, index) => (
                <div key={index} className="set-input-row">
                  <span className="set-number">Set {set.set_number}</span>
                  
                  <div className="input-group">
                    <input
                      type="number"
                      value={set.reps}
                      onChange={(e) => updateWorkoutSet(index, 'reps', e.target.value)}
                      placeholder="Reps"
                      min="1"
                    />
                    <label>reps</label>
                  </div>

                  <div className="input-group">
                    <input
                      type="number"
                      value={set.weight}
                      onChange={(e) => updateWorkoutSet(index, 'weight', e.target.value)}
                      placeholder="Weight"
                      min="0"
                      step="0.5"
                    />
                    <label>{user?.weight_unit || 'kg'}</label>
                  </div>

                  <div className="input-group">
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={set.rpe}
                      onChange={(e) => updateWorkoutSet(index, 'rpe', e.target.value)}
                      className="rpe-slider"
                    />
                    <label>RPE {set.rpe}</label>
                  </div>

                  <button 
                    className="icon-btn remove-set-btn"
                    onClick={() => removeWorkoutSet(index)}
                  >
                    🗑️
                  </button>
                </div>
              ))}

              {/* Add Set & Voice Input */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
                <button className="btn-secondary" onClick={addWorkoutSet}>
                  + Add Set
                </button>
                <button 
                  className={`btn-secondary ${isListening ? 'listening' : ''}`}
                  onClick={startVoiceInput}
                  disabled={currentWorkoutSets.length === 0}
                  title="Say something like '10 reps 50 kilos'"
                >
                  {isListening ? '🎤 Listening...' : '🎤 Voice Input'}
                </button>
              </div>

              {/* Rest Timer Presets */}
              {!restTimerActive && (
                <div className="rest-timer-presets">
                  <p>Rest Timer:</p>
                  <button onClick={() => startRestTimer(60)}>60s</button>
                  <button onClick={() => startRestTimer(90)}>90s</button>
                  <button onClick={() => startRestTimer(120)}>120s</button>
                  <button onClick={() => startRestTimer(180)}>3min</button>
                </div>
              )}

              {/* Notes */}
              <textarea
                className="workout-notes"
                placeholder="Add notes (optional)..."
                value={workoutNotes}
                onChange={(e) => setWorkoutNotes(e.target.value)}
                rows="3"
              />

              {/* Save Button */}
              <button 
                className="btn-primary"
                onClick={saveWorkoutSession}
                disabled={loading || currentWorkoutSets.length === 0}
                style={{ marginTop: '15px', width: '100%' }}
              >
                {loading ? 'Saving...' : '✓ Save Workout'}
              </button>
            </div>

            {/* 1RM Calculator */}
            {exerciseStats && (
              <div className="workout-section">
                <h3>💪 Exercise Stats</h3>
                <div className="stats-grid">
                  <div className="stat-item">
                    <span className="stat-label">Personal Best</span>
                    <span className="stat-value">{exerciseStats.personal_best}{user?.weight_unit || 'kg'}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Estimated 1RM</span>
                    <span className="stat-value">{exerciseStats.estimated_1rm}{user?.weight_unit || 'kg'}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Total Sessions</span>
                    <span className="stat-value">{exerciseStats.total_sessions}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Total Volume</span>
                    <span className="stat-value">{exerciseStats.total_volume}{user?.weight_unit || 'kg'}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Personal Records */}
            {exerciseStats && (
              <div className="workout-section">
                <h3>🏆 Personal Records</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                  <div style={{ 
                    padding: '20px', 
                    backgroundColor: '#1a1a1a', 
                    borderRadius: '12px', 
                    border: '2px solid #22c55e',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '13px', color: '#888', marginBottom: '8px' }}>Max Weight</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#22c55e' }}>
                      {exerciseStats.personal_best}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>{user?.weight_unit || 'kg'}</div>
                  </div>
                  <div style={{ 
                    padding: '20px', 
                    backgroundColor: '#1a1a1a', 
                    borderRadius: '12px', 
                    border: '2px solid #22c55e',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '13px', color: '#888', marginBottom: '8px' }}>Max Reps</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#22c55e' }}>
                      {exerciseStats.max_reps || 0}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>reps</div>
                  </div>
                </div>
              </div>
            )}

            {/* Performance History */}
            {exerciseHistory && exerciseHistory.sessions && exerciseHistory.sessions.length > 0 && (
              <div className="workout-section">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                  <h3 style={{ margin: 0 }}>📊 Your Performance</h3>
                  <select 
                    value={progressTimePeriod} 
                    onChange={(e) => setProgressTimePeriod(e.target.value)}
                    style={{
                      padding: '8px 12px',
                      backgroundColor: '#1a1a1a',
                      color: '#fff',
                      border: '1px solid #333',
                      borderRadius: '8px',
                      fontSize: '13px'
                    }}
                  >
                    <option value="1month">Last 1 month</option>
                    <option value="3months">Last 3 months</option>
                    <option value="6months">Last 6 months</option>
                    <option value="all">All time</option>
                  </select>
                </div>
                
                {(() => {
                  // Filter sessions based on time period
                  const now = new Date();
                  const filterDate = progressTimePeriod === 'all' ? null : 
                    progressTimePeriod === '1month' ? new Date(now.setMonth(now.getMonth() - 1)) :
                    progressTimePeriod === '3months' ? new Date(now.setMonth(now.getMonth() - 3)) :
                    new Date(now.setMonth(now.getMonth() - 6));
                  
                  let filteredSessions = exerciseHistory.sessions.filter(session => {
                    if (!filterDate) return true;
                    const sessionDate = new Date(session.workout_date);
                    return sessionDate >= filterDate;
                  });
                  
                  // Sort by date ascending for charts
                  filteredSessions = filteredSessions.sort((a, b) => 
                    new Date(a.workout_date) - new Date(b.workout_date)
                  );
                  
                  if (filteredSessions.length === 0) {
                    return <p style={{ fontSize: '14px', color: '#888', textAlign: 'center', padding: '20px' }}>
                      No workout data for selected time period
                    </p>;
                  }
                  
                  const maxWeightValue = Math.max(...filteredSessions.map(s => s.max_weight || 0));
                  const maxVolumeValue = Math.max(...filteredSessions.map(s => s.total_volume || 0));
                  
                  return (
                    <>
                      {/* Weight Over Time Chart */}
                      <div style={{ marginBottom: '30px' }}>
                        <p style={{ fontSize: '14px', color: '#888', marginBottom: '15px', fontWeight: '500' }}>
                          Weight Over Time ({user?.weight_unit || 'kg'})
                        </p>
                        <div style={{ 
                          position: 'relative', 
                          height: '200px', 
                          backgroundColor: '#0a0a0a',
                          borderRadius: '12px',
                          padding: '20px 15px 40px 15px',
                          border: '1px solid #222'
                        }}>
                          <svg width="100%" height="100%" style={{ overflow: 'visible' }}>
                            {/* Grid lines */}
                            {[0, 25, 50, 75, 100].map((percent) => (
                              <line 
                                key={percent}
                                x1="0" 
                                y1={`${percent}%`} 
                                x2="100%" 
                                y2={`${percent}%`} 
                                stroke="#1a1a1a" 
                                strokeWidth="1"
                              />
                            ))}
                            
                            {/* Line chart */}
                            <polyline
                              fill="none"
                              stroke="#22c55e"
                              strokeWidth="3"
                              points={filteredSessions.map((session, index) => {
                                const x = (index / (filteredSessions.length - 1 || 1)) * 100;
                                const y = 100 - ((session.max_weight / maxWeightValue) * 100);
                                return `${x}%,${y}%`;
                              }).join(' ')}
                            />
                            
                            {/* Data points */}
                            {filteredSessions.map((session, index) => {
                              const x = (index / (filteredSessions.length - 1 || 1)) * 100;
                              const y = 100 - ((session.max_weight / maxWeightValue) * 100);
                              return (
                                <g key={index}>
                                  <circle 
                                    cx={`${x}%`} 
                                    cy={`${y}%`} 
                                    r="5" 
                                    fill="#22c55e" 
                                    stroke="#0a0a0a"
                                    strokeWidth="2"
                                  />
                                  <text 
                                    x={`${x}%`} 
                                    y={`${y - 5}%`} 
                                    fill="#22c55e" 
                                    fontSize="11" 
                                    textAnchor="middle"
                                    dy="-5"
                                  >
                                    {session.max_weight}
                                  </text>
                                </g>
                              );
                            })}
                          </svg>
                          
                          {/* Date labels */}
                          <div style={{ 
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            marginTop: '10px',
                            fontSize: '10px',
                            color: '#666'
                          }}>
                            {filteredSessions.length > 1 && (
                              <>
                                <span>{new Date(filteredSessions[0].workout_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                                <span>{new Date(filteredSessions[filteredSessions.length - 1].workout_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Volume Over Time Chart */}
                      <div style={{ marginBottom: '30px' }}>
                        <p style={{ fontSize: '14px', color: '#888', marginBottom: '15px', fontWeight: '500' }}>
                          Volume Over Time ({user?.weight_unit || 'kg'})
                        </p>
                        <div style={{ 
                          position: 'relative', 
                          height: '200px', 
                          backgroundColor: '#0a0a0a',
                          borderRadius: '12px',
                          padding: '20px 15px 40px 15px',
                          border: '1px solid #222'
                        }}>
                          <svg width="100%" height="100%" style={{ overflow: 'visible' }}>
                            {/* Grid lines */}
                            {[0, 25, 50, 75, 100].map((percent) => (
                              <line 
                                key={percent}
                                x1="0" 
                                y1={`${percent}%`} 
                                x2="100%" 
                                y2={`${percent}%`} 
                                stroke="#1a1a1a" 
                                strokeWidth="1"
                              />
                            ))}
                            
                            {/* Area fill */}
                            <polygon
                              fill="url(#volumeGradient)"
                              opacity="0.3"
                              points={`0,100% ${filteredSessions.map((session, index) => {
                                const x = (index / (filteredSessions.length - 1 || 1)) * 100;
                                const y = 100 - ((session.total_volume / maxVolumeValue) * 100);
                                return `${x}%,${y}%`;
                              }).join(' ')} 100%,100%`}
                            />
                            
                            {/* Gradient definition */}
                            <defs>
                              <linearGradient id="volumeGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stopColor="#3b82f6" stopOpacity="1" />
                                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
                              </linearGradient>
                            </defs>
                            
                            {/* Line chart */}
                            <polyline
                              fill="none"
                              stroke="#3b82f6"
                              strokeWidth="3"
                              points={filteredSessions.map((session, index) => {
                                const x = (index / (filteredSessions.length - 1 || 1)) * 100;
                                const y = 100 - ((session.total_volume / maxVolumeValue) * 100);
                                return `${x}%,${y}%`;
                              }).join(' ')}
                            />
                            
                            {/* Data points */}
                            {filteredSessions.map((session, index) => {
                              const x = (index / (filteredSessions.length - 1 || 1)) * 100;
                              const y = 100 - ((session.total_volume / maxVolumeValue) * 100);
                              return (
                                <g key={index}>
                                  <circle 
                                    cx={`${x}%`} 
                                    cy={`${y}%`} 
                                    r="5" 
                                    fill="#3b82f6" 
                                    stroke="#0a0a0a"
                                    strokeWidth="2"
                                  />
                                  <text 
                                    x={`${x}%`} 
                                    y={`${y - 5}%`} 
                                    fill="#3b82f6" 
                                    fontSize="11" 
                                    textAnchor="middle"
                                    dy="-5"
                                  >
                                    {Math.round(session.total_volume)}
                                  </text>
                                </g>
                              );
                            })}
                          </svg>
                          
                          {/* Date labels */}
                          <div style={{ 
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            marginTop: '10px',
                            fontSize: '10px',
                            color: '#666'
                          }}>
                            {filteredSessions.length > 1 && (
                              <>
                                <span>{new Date(filteredSessions[0].workout_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                                <span>{new Date(filteredSessions[filteredSessions.length - 1].workout_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Progress Summary */}
                      <div style={{ 
                        padding: '15px', 
                        backgroundColor: '#1a1a1a', 
                        borderRadius: '8px',
                        border: '1px solid #333'
                      }}>
                        <h4 style={{ fontSize: '14px', marginBottom: '12px', color: '#22c55e' }}>
                          📈 Progress Summary
                        </h4>
                        {(() => {
                          if (filteredSessions.length < 2) return <p style={{ fontSize: '12px', color: '#888' }}>Complete more sessions to see progress trends</p>;
                          
                          const recent = filteredSessions[filteredSessions.length - 1];
                          const previous = filteredSessions[filteredSessions.length - 2];
                          const weightChange = ((recent.max_weight || 0) - (previous.max_weight || 0));
                          const volumeChange = ((recent.total_volume || 0) - (previous.total_volume || 0));
                          
                          return (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                                <span style={{ color: '#888' }}>Max Weight Change:</span>
                                <span style={{ color: weightChange >= 0 ? '#22c55e' : '#ef4444', fontWeight: '500' }}>
                                  {weightChange >= 0 ? '+' : ''}{weightChange} {user?.weight_unit || 'kg'}
                                </span>
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                                <span style={{ color: '#888' }}>Volume Change:</span>
                                <span style={{ color: volumeChange >= 0 ? '#22c55e' : '#ef4444', fontWeight: '500' }}>
                                  {volumeChange >= 0 ? '+' : ''}{Math.round(volumeChange)} {user?.weight_unit || 'kg'}
                                </span>
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                                <span style={{ color: '#888' }}>Total Sessions:</span>
                                <span style={{ color: '#22c55e', fontWeight: '500' }}>
                                  {filteredSessions.length}
                                </span>
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                    </>
                  );
                })()}
              </div>
            )}
          </div>
        </div>
      );
    }

    // Show exercise library
    return (
      <div className="workout-container">
        <div className="page-header">
          <h2>Exercise Library</h2>
          <button className="icon-btn" onClick={() => setShowExerciseSearch(!showExerciseSearch)}>🔍</button>
        </div>

        {/* Search Input */}
        {showExerciseSearch && (
          <div style={{ padding: '0 20px 10px 20px' }}>
            <input
              type="text"
              placeholder="Search exercises..."
              value={exerciseSearchQuery}
              onChange={(e) => setExerciseSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid #333',
                backgroundColor: '#1a1a1a',
                color: '#fff',
                fontSize: '16px'
              }}
              autoFocus
            />
          </div>
        )}

        <div className="filter-tabs">
          <button 
            className={`filter-tab ${selectedCategory === 'All' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('All')}
          >
            All
          </button>
          <button 
            className={`filter-tab ${selectedCategory === 'Chest' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('Chest')}
          >
            Chest
          </button>
          <button 
            className={`filter-tab ${selectedCategory === 'Back' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('Back')}
          >
            Back
          </button>
          <button 
            className={`filter-tab ${selectedCategory === 'Legs' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('Legs')}
          >
            Legs
          </button>
          <button 
            className={`filter-tab ${selectedCategory === 'Shoulders' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('Shoulders')}
          >
            Shoulders
          </button>
          <button 
            className={`filter-tab ${selectedCategory === 'Arms' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('Arms')}
          >
            Arms
          </button>
          <button 
            className={`filter-tab ${selectedCategory === 'Core' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('Core')}
          >
            Core
          </button>
        </div>

        <button className="btn-primary workout-cta" onClick={() => setShowQuickStartModal(true)}>
          Start Today's Workout
        </button>

        {/* Quick Start Modal */}
        {showQuickStartModal && (
          <div className="modal-overlay" onClick={() => setShowQuickStartModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>Quick Start Workout</h3>
                <button className="icon-btn" onClick={() => setShowQuickStartModal(false)}>✕</button>
              </div>
              <div className="modal-body" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                <p style={{ color: '#888', marginBottom: '20px', fontSize: '14px' }}>
                  Select an exercise below to start tracking your workout
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {exercises.slice(0, 10).map((exercise) => (
                    <button
                      key={exercise.exercise_id}
                      className="quick-start-exercise-btn"
                      onClick={() => {
                        setShowQuickStartModal(false);
                        fetchExerciseDetail(exercise.exercise_id);
                      }}
                      style={{
                        padding: '15px',
                        backgroundColor: '#2a2a2a',
                        border: '1px solid #333',
                        borderRadius: '8px',
                        color: '#fff',
                        textAlign: 'left',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        transition: 'all 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = '#333';
                        e.currentTarget.style.borderColor = '#22c55e';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = '#2a2a2a';
                        e.currentTarget.style.borderColor = '#333';
                      }}
                    >
                      <span style={{ fontSize: '24px' }}>
                        {exercise.category === 'Chest' ? '🏋️' : 
                         exercise.category === 'Legs' ? '🦵' :
                         exercise.category === 'Back' ? '💪' : 
                         exercise.category === 'Shoulders' ? '🤸' :
                         exercise.category === 'Arms' ? '💪' :
                         exercise.category === 'Core' ? '🧘' : '🏋️'}
                      </span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: '500', marginBottom: '4px' }}>{exercise.name}</div>
                        <div style={{ fontSize: '12px', color: '#888' }}>{exercise.category}</div>
                      </div>
                      <span style={{ color: '#22c55e' }}>→</span>
                    </button>
                  ))}
                </div>
                <button 
                  className="btn-secondary" 
                  onClick={() => setShowQuickStartModal(false)}
                  style={{ 
                    marginTop: '20px', 
                    width: '100%',
                    padding: '12px',
                    backgroundColor: 'transparent',
                    border: '1px solid #333',
                    borderRadius: '8px',
                    color: '#fff',
                    cursor: 'pointer'
                  }}
                >
                  Browse All Exercises
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Workout Dashboard Stats */}
        {workoutDashboardStats && (
          <div className="workout-stats-banner">
            <div className="workout-stat-item">
              <span className="stat-value">{workoutDashboardStats.total_workouts}</span>
              <span className="stat-label">Workouts</span>
            </div>
            <div className="workout-stat-item">
              <span className="stat-value">{workoutDashboardStats.total_volume_lifted || 0}</span>
              <span className="stat-label">{user?.weight_unit || 'kg'}</span>
            </div>
            {workoutDashboardStats.recent_workout && (
              <div className="workout-stat-item">
                <span className="stat-value">{workoutDashboardStats.recent_workout.name}</span>
                <span className="stat-label">Recent Workout</span>
              </div>
            )}
          </div>
        )}

        <div className="exercise-grid">
          {(() => {
            const filteredExercises = exercises.filter(exercise => {
              // Filter by search query if active
              if (exerciseSearchQuery.trim()) {
                return exercise.name.toLowerCase().includes(exerciseSearchQuery.toLowerCase()) ||
                       exercise.category.toLowerCase().includes(exerciseSearchQuery.toLowerCase());
              }
              return true;
            });

            if (filteredExercises.length === 0) {
              return (
                <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
                  <p>{exerciseSearchQuery.trim() ? `No exercises found matching "${exerciseSearchQuery}"` : 'No exercises found'}</p>
                </div>
              );
            }

            return filteredExercises.map((exercise) => (
              <div 
                key={exercise.exercise_id} 
                className="exercise-card"
                onClick={() => fetchExerciseDetail(exercise.exercise_id)}
              >
                <div className="exercise-image" style={{
                  backgroundImage: exercise.image_url ? `url(${exercise.image_url})` : 'none',
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                  backgroundColor: exercise.image_url ? 'transparent' : '#2a2a2a'
                }}>
                  {!exercise.image_url && (
                    <span className="exercise-placeholder">
                      {exercise.category === 'Chest' ? '🏋️' : 
                       exercise.category === 'Legs' ? '🦵' :
                       exercise.category === 'Back' ? '💪' : 
                       exercise.category === 'Shoulders' ? '🤸' :
                       exercise.category === 'Arms' ? '💪' :
                       exercise.category === 'Core' ? '🧘' : '🏋️'}
                    </span>
                  )}
                </div>
                <h4>{exercise.name}</h4>
                <p style={{ fontSize: '12px', color: '#888', marginTop: '5px' }}>
                  {exercise.category}
                </p>
              </div>
            ));
          })()}
        </div>
      </div>
    );
  };

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
                {day.meals && Object.entries(day.meals).map(([mealType, meal]) => {
                  const hasMeal = meal && meal.name && meal.name.trim();
                  
                  return (
                    <div key={mealType} style={{ marginBottom: '12px' }}>
                      <div style={{ 
                        color: '#fff', 
                        textTransform: 'capitalize',
                        fontSize: '16px',
                        fontWeight: 'bold',
                        marginBottom: '8px'
                      }}>
                        {mealType.replace('_', ' ')}
                      </div>
                      
                      {!hasMeal ? (
                        <button
                          onClick={() => openAddMealForm(mealType, index)}
                          style={{
                            width: '100%',
                            padding: '14px',
                            background: '#22c55e',
                            color: '#000',
                            border: 'none',
                            borderRadius: '40px',
                            fontSize: '15px',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '8px'
                          }}
                        >
                          + Add {mealType.replace('_', ' ')}
                        </button>
                      ) : (
                        <div style={{
                          background: '#0a0a0a',
                          borderRadius: '12px',
                          padding: '16px'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ color: '#22c55e', fontWeight: 'bold' }}>
                              {meal.calories} kcal
                            </span>
                            <div style={{ display: 'flex', gap: '8px' }}>
                              <button
                                onClick={() => openEditMealForm(mealType, index, meal)}
                                style={{
                                  padding: '6px 12px',
                                  background: '#22c55e',
                                  color: '#000',
                                  border: 'none',
                                  borderRadius: '6px',
                                  fontSize: '13px',
                                  cursor: 'pointer',
                                  fontWeight: 'bold'
                                }}
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => deleteMealFromPlan(mealType, index)}
                                style={{
                                  padding: '6px 12px',
                                  background: '#ef4444',
                                  color: '#fff',
                                  border: 'none',
                                  borderRadius: '6px',
                                  fontSize: '13px',
                                  cursor: 'pointer',
                                  fontWeight: 'bold'
                                }}
                              >
                                Delete
                              </button>
                            </div>
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
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Edit/Add Meal Modal for Meal Plan Details */}
          {(showAddMealForm.show || editingMeal.show) && (
            <div style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0,0,0,0.8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1001
            }}>
              <div style={{
                background: '#0a0a0a',
                borderRadius: '16px',
                padding: '24px',
                maxWidth: '400px',
                width: '90%',
                border: '1px solid #333'
              }}>
                <h3 style={{ color: '#22c55e', marginBottom: '20px' }}>
                  {editingMeal.show ? 'Edit' : 'Add'} {(showAddMealForm.mealType || editingMeal.mealType).replace('_', ' ')}
                </h3>
                
                <input
                  type="text"
                  placeholder="Meal name"
                  value={tempMealData.name}
                  onChange={(e) => setTempMealData({...tempMealData, name: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    marginBottom: '12px',
                    background: '#1a1a1a',
                    border: '1px solid #333',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '14px'
                  }}
                />
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                  <input
                    type="number"
                    placeholder="Calories"
                    value={tempMealData.calories || ''}
                    onChange={(e) => setTempMealData({...tempMealData, calories: e.target.value})}
                    style={{
                      padding: '12px',
                      background: '#1a1a1a',
                      border: '1px solid #333',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '14px'
                    }}
                  />
                  <input
                    type="number"
                    placeholder="Protein (g)"
                    value={tempMealData.protein || ''}
                    onChange={(e) => setTempMealData({...tempMealData, protein: e.target.value})}
                    style={{
                      padding: '12px',
                      background: '#1a1a1a',
                      border: '1px solid #333',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '14px'
                    }}
                  />
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
                  <input
                    type="number"
                    placeholder="Carbs (g)"
                    value={tempMealData.carbs || ''}
                    onChange={(e) => setTempMealData({...tempMealData, carbs: e.target.value})}
                    style={{
                      padding: '12px',
                      background: '#1a1a1a',
                      border: '1px solid #333',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '14px'
                    }}
                  />
                  <input
                    type="number"
                    placeholder="Fat (g)"
                    value={tempMealData.fat || ''}
                    onChange={(e) => setTempMealData({...tempMealData, fat: e.target.value})}
                    style={{
                      padding: '12px',
                      background: '#1a1a1a',
                      border: '1px solid #333',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '14px'
                    }}
                  />
                </div>
                
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button
                    onClick={() => {
                      setShowAddMealForm({ show: false, mealType: '', dayIndex: 0 });
                      setEditingMeal({ show: false, mealType: '', dayIndex: 0, meal: null });
                    }}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: '#333',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '8px',
                      fontSize: '14px',
                      cursor: 'pointer',
                      fontWeight: 'bold'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      const mealType = showAddMealForm.show ? showAddMealForm.mealType : editingMeal.mealType;
                      const dayIndex = showAddMealForm.show ? showAddMealForm.dayIndex : editingMeal.dayIndex;
                      saveMealToSelectedPlan(mealType, dayIndex);
                    }}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: '#22c55e',
                      color: '#000',
                      border: 'none',
                      borderRadius: '8px',
                      fontSize: '14px',
                      cursor: 'pointer',
                      fontWeight: 'bold'
                    }}
                  >
                    {editingMeal.show ? 'Save Changes' : 'Add Meal'}
                  </button>
                </div>
              </div>
            </div>
          )}
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
                      const duration = 7;
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
                        name: '',
                        duration: duration,
                        start_date: new Date().toISOString().split('T')[0],
                        days: days
                      });
                      setCurrentManualDay(0);
                      setMealPlanType('manual');
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
                      <option value="1">1 Day</option>
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
                      placeholder="e.g., 6-d.. Summer Shred"
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
                          duration: duration,
                          days: days
                        });
                        setCurrentManualDay(0);
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
                      <option value="1">1 Day</option>
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

                  {/* Day Navigation */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', marginBottom: '16px', padding: '12px', background: '#1a1a1a', borderRadius: '8px' }}>
                    <button
                      onClick={() => setCurrentManualDay(Math.max(0, currentManualDay - 1))}
                      disabled={currentManualDay === 0}
                      style={{
                        padding: '8px 16px',
                        background: currentManualDay === 0 ? '#333' : '#22c55e',
                        color: currentManualDay === 0 ? '#666' : '#000',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: currentManualDay === 0 ? 'not-allowed' : 'pointer',
                        fontWeight: 'bold'
                      }}
                    >
                      ← Previous
                    </button>
                    <div style={{ color: '#22c55e', fontWeight: 'bold', fontSize: '16px' }}>
                      Day {currentManualDay + 1} of {manualMealPlanData.duration}
                    </div>
                    <button
                      onClick={() => setCurrentManualDay(Math.min(manualMealPlanData.duration - 1, currentManualDay + 1))}
                      disabled={currentManualDay >= manualMealPlanData.duration - 1}
                      style={{
                        padding: '8px 16px',
                        background: currentManualDay >= manualMealPlanData.duration - 1 ? '#333' : '#22c55e',
                        color: currentManualDay >= manualMealPlanData.duration - 1 ? '#666' : '#000',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: currentManualDay >= manualMealPlanData.duration - 1 ? 'not-allowed' : 'pointer',
                        fontWeight: 'bold'
                      }}
                    >
                      Next →
                    </button>
                  </div>

                  {/* Single Day Meal Entry with + Add Buttons */}
                  {manualMealPlanData.days.length > 0 && manualMealPlanData.days[currentManualDay] && (
                    <div style={{ marginTop: '16px' }}>
                      {['breakfast', 'morning_snack', 'lunch', 'afternoon_snack', 'dinner'].map(mealType => {
                        const meal = manualMealPlanData.days[currentManualDay].meals[mealType];
                        const hasMeal = meal && meal.name && meal.name.trim();
                        
                        return (
                          <div key={mealType} style={{ marginBottom: '16px' }}>
                            <div style={{ color: '#fff', fontSize: '16px', fontWeight: 'bold', marginBottom: '12px', textTransform: 'capitalize' }}>
                              {mealType.replace('_', ' ')}
                            </div>
                            
                            {!hasMeal ? (
                              <button
                                onClick={() => {
                                  setShowAddMealForm({ show: true, mealType, dayIndex: currentManualDay });
                                  setTempMealData({ name: '', calories: 0, protein: 0, carbs: 0, fat: 0 });
                                }}
                                style={{
                                  width: '100%',
                                  padding: '16px',
                                  background: '#22c55e',
                                  color: '#000',
                                  border: 'none',
                                  borderRadius: '40px',
                                  fontSize: '16px',
                                  fontWeight: 'bold',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  gap: '8px'
                                }}
                              >
                                + Add {mealType.replace('_', ' ')}
                              </button>
                            ) : (
                              <div style={{
                                background: '#1a1a1a',
                                borderRadius: '12px',
                                padding: '16px',
                                border: '1px solid #333'
                              }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <div style={{ flex: 1 }}>
                                    <div style={{ color: '#22c55e', fontWeight: 'bold', marginBottom: '4px' }}>
                                      {meal.name}
                                    </div>
                                    <div style={{ fontSize: '14px', color: '#888' }}>
                                      {meal.calories} cal | P: {meal.protein}g | C: {meal.carbs}g | F: {meal.fat}g
                                    </div>
                                  </div>
                                  <button
                                    onClick={() => {
                                      const updatedData = {...manualMealPlanData};
                                      updatedData.days[currentManualDay].meals[mealType] = {
                                        name: '',
                                        calories: 0,
                                        protein: 0,
                                        carbs: 0,
                                        fat: 0,
                                        description: '',
                                        ingredients: []
                                      };
                                      
                                      // Recalculate totals
                                      let totalCalories = 0, totalProtein = 0, totalCarbs = 0, totalFat = 0;
                                      Object.values(updatedData.days[currentManualDay].meals).forEach(m => {
                                        if (m && m.name) {
                                          totalCalories += parseFloat(m.calories) || 0;
                                          totalProtein += parseFloat(m.protein) || 0;
                                          totalCarbs += parseFloat(m.carbs) || 0;
                                          totalFat += parseFloat(m.fat) || 0;
                                        }
                                      });
                                      updatedData.days[currentManualDay].totals = {
                                        calories: totalCalories,
                                        protein: totalProtein,
                                        carbs: totalCarbs,
                                        fat: totalFat
                                      };
                                      
                                      setManualMealPlanData(updatedData);
                                    }}
                                    style={{
                                      padding: '8px 12px',
                                      background: '#ef4444',
                                      color: '#fff',
                                      border: 'none',
                                      borderRadius: '6px',
                                      fontSize: '14px',
                                      cursor: 'pointer',
                                      fontWeight: 'bold'
                                    }}
                                  >
                                    Remove
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                      
                      {/* Daily Total */}
                      <div style={{
                        background: 'rgba(34, 197, 94, 0.1)',
                        padding: '16px',
                        borderRadius: '12px',
                        marginTop: '20px',
                        border: '1px solid rgba(34, 197, 94, 0.2)'
                      }}>
                        <div style={{ color: '#22c55e', fontSize: '16px', fontWeight: 'bold', marginBottom: '12px' }}>
                          Daily Total
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', textAlign: 'center' }}>
                          <div>
                            <div style={{ color: '#888', fontSize: '12px' }}>Calories</div>
                            <div style={{ color: '#22c55e', fontWeight: 'bold', fontSize: '18px' }}>
                              {Math.round(manualMealPlanData.days[currentManualDay].totals.calories)}
                            </div>
                          </div>
                          <div>
                            <div style={{ color: '#888', fontSize: '12px' }}>Protein</div>
                            <div style={{ color: '#22c55e', fontWeight: 'bold', fontSize: '18px' }}>
                              {Math.round(manualMealPlanData.days[currentManualDay].totals.protein)}g
                            </div>
                          </div>
                          <div>
                            <div style={{ color: '#888', fontSize: '12px' }}>Carbs</div>
                            <div style={{ color: '#22c55e', fontWeight: 'bold', fontSize: '18px' }}>
                              {Math.round(manualMealPlanData.days[currentManualDay].totals.carbs)}g
                            </div>
                          </div>
                          <div>
                            <div style={{ color: '#888', fontSize: '12px' }}>Fat</div>
                            <div style={{ color: '#22c55e', fontWeight: 'bold', fontSize: '18px' }}>
                              {Math.round(manualMealPlanData.days[currentManualDay].totals.fat)}g
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '12px', marginTop: '24px', position: 'sticky', bottom: 0, background: '#0a0a0a', padding: '16px 0' }}>
                    <button
                      className="secondary-btn"
                      onClick={() => {
                        setMealPlanType('');
                        setCurrentManualDay(0);
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

              {/* Add Meal Form Modal */}
              {showAddMealForm.show && (
                <div style={{
                  position: 'fixed',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'rgba(0,0,0,0.8)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  zIndex: 1001
                }}>
                  <div style={{
                    background: '#0a0a0a',
                    borderRadius: '16px',
                    padding: '24px',
                    maxWidth: '400px',
                    width: '90%',
                    border: '1px solid #333'
                  }}>
                    <h3 style={{ color: '#22c55e', marginBottom: '20px' }}>
                      Add {showAddMealForm.mealType.replace('_', ' ')}
                    </h3>
                    
                    <input
                      type="text"
                      placeholder="Meal name"
                      value={tempMealData.name}
                      onChange={(e) => setTempMealData({...tempMealData, name: e.target.value})}
                      style={{
                        width: '100%',
                        padding: '12px',
                        marginBottom: '12px',
                        background: '#1a1a1a',
                        border: '1px solid #333',
                        borderRadius: '8px',
                        color: '#fff',
                        fontSize: '14px'
                      }}
                    />
                    
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                      <input
                        type="number"
                        placeholder="Calories"
                        value={tempMealData.calories || ''}
                        onChange={(e) => setTempMealData({...tempMealData, calories: e.target.value})}
                        style={{
                          padding: '12px',
                          background: '#1a1a1a',
                          border: '1px solid #333',
                          borderRadius: '8px',
                          color: '#fff',
                          fontSize: '14px'
                        }}
                      />
                      <input
                        type="number"
                        placeholder="Protein (g)"
                        value={tempMealData.protein || ''}
                        onChange={(e) => setTempMealData({...tempMealData, protein: e.target.value})}
                        style={{
                          padding: '12px',
                          background: '#1a1a1a',
                          border: '1px solid #333',
                          borderRadius: '8px',
                          color: '#fff',
                          fontSize: '14px'
                        }}
                      />
                    </div>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
                      <input
                        type="number"
                        placeholder="Carbs (g)"
                        value={tempMealData.carbs || ''}
                        onChange={(e) => setTempMealData({...tempMealData, carbs: e.target.value})}
                        style={{
                          padding: '12px',
                          background: '#1a1a1a',
                          border: '1px solid #333',
                          borderRadius: '8px',
                          color: '#fff',
                          fontSize: '14px'
                        }}
                      />
                      <input
                        type="number"
                        placeholder="Fat (g)"
                        value={tempMealData.fat || ''}
                        onChange={(e) => setTempMealData({...tempMealData, fat: e.target.value})}
                        style={{
                          padding: '12px',
                          background: '#1a1a1a',
                          border: '1px solid #333',
                          borderRadius: '8px',
                          color: '#fff',
                          fontSize: '14px'
                        }}
                      />
                    </div>
                    
                    <div style={{ display: 'flex', gap: '12px' }}>
                      <button
                        onClick={() => setShowAddMealForm({ show: false, mealType: '', dayIndex: 0 })}
                        style={{
                          flex: 1,
                          padding: '12px',
                          background: '#333',
                          color: '#fff',
                          border: 'none',
                          borderRadius: '8px',
                          fontSize: '14px',
                          cursor: 'pointer',
                          fontWeight: 'bold'
                        }}
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => {
                          if (!tempMealData.name.trim()) {
                            setError('Please enter a meal name');
                            return;
                          }
                          
                          const updatedData = {...manualMealPlanData};
                          updatedData.days[showAddMealForm.dayIndex].meals[showAddMealForm.mealType] = {
                            ...tempMealData,
                            calories: parseFloat(tempMealData.calories) || 0,
                            protein: parseFloat(tempMealData.protein) || 0,
                            carbs: parseFloat(tempMealData.carbs) || 0,
                            fat: parseFloat(tempMealData.fat) || 0,
                            description: '',
                            ingredients: []
                          };
                          
                          // Recalculate totals
                          let totalCalories = 0, totalProtein = 0, totalCarbs = 0, totalFat = 0;
                          Object.values(updatedData.days[showAddMealForm.dayIndex].meals).forEach(meal => {
                            if (meal && meal.name) {
                              totalCalories += parseFloat(meal.calories) || 0;
                              totalProtein += parseFloat(meal.protein) || 0;
                              totalCarbs += parseFloat(meal.carbs) || 0;
                              totalFat += parseFloat(meal.fat) || 0;
                            }
                          });
                          updatedData.days[showAddMealForm.dayIndex].totals = {
                            calories: totalCalories,
                            protein: totalProtein,
                            carbs: totalCarbs,
                            fat: totalFat
                          };
                          
                          setManualMealPlanData(updatedData);
                          setShowAddMealForm({ show: false, mealType: '', dayIndex: 0 });
                          setError('');
                        }}
                        style={{
                          flex: 1,
                          padding: '12px',
                          background: '#22c55e',
                          color: '#000',
                          border: 'none',
                          borderRadius: '8px',
                          fontSize: '14px',
                          cursor: 'pointer',
                          fontWeight: 'bold'
                        }}
                      >
                        Add Meal
                      </button>
                    </div>
                  </div>
                </div>
              )}
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
                {currentPage === 'chatbot' && renderChatbot()}
              </div>
              {currentPage !== 'chatbot' && renderBottomNav()}
            </>
          )}
        </>
      )}
      
      {/* Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          bottom: '100px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: '#22c55e',
          color: '#000',
          padding: '16px 24px',
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(34, 197, 94, 0.3)',
          zIndex: 10000,
          fontWeight: 'bold',
          fontSize: '14px',
          animation: 'slideUp 0.3s ease-out',
          maxWidth: '90%',
          textAlign: 'center'
        }}>
          {toastMessage}
        </div>
      )}
    </div>
  );
}

export default App;