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
  
  // Chatbot state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);
  
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
          <div className="user-avatar">👤</div>
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
  const renderMealPlan = () => (
    <div className="meal-plan-container">
      <div className="page-header">
        <h2>Meal Plan</h2>
        <button className="icon-btn">+</button>
      </div>

      <div className="coming-soon">
        <h3>🍽️</h3>
        <p>Meal planning feature coming soon!</p>
        <p className="subtitle">Create weekly meal plans with AI-recommended recipes</p>
      </div>
    </div>
  );

  // Render Profile Page
  const renderProfile = () => (
    <div className="profile-container">
      <div className="page-header">
        <h2>Profile</h2>
        <button className="icon-btn" onClick={handleLogout}>⚙️</button>
      </div>

      <div className="profile-card">
        <div className="profile-avatar">👤</div>
        <h3>{user?.name}</h3>
        <p>{user?.email}</p>
      </div>

      <div className="profile-stats">
        {user?.age && <div className="profile-stat"><span>Age:</span> {user.age} years</div>}
        {user?.gender && <div className="profile-stat"><span>Gender:</span> {user.gender}</div>}
        {user?.height && <div className="profile-stat"><span>Height:</span> {user.height} cm</div>}
        {user?.weight && <div className="profile-stat"><span>Weight:</span> {user.weight} kg</div>}
        {user?.goal_weight && <div className="profile-stat"><span>Goal Weight:</span> {user.goal_weight} kg</div>}
        {user?.activity_level && <div className="profile-stat"><span>Activity:</span> {user.activity_level}</div>}
      </div>

      <button className="btn-primary" onClick={handleLogout}>
        Logout
      </button>
    </div>
  );

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
    </div>
  );
}

export default App;