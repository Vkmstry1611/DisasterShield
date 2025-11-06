# DisasterShield Project Structure

## 📁 **Core Files**

### **Backend (Python)**
```
backend/
├── main.py                    # Main FastAPI server with Reddit integration
├── run_server.py             # Server startup script
├── setup_database.py         # MySQL database setup
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (MySQL + Reddit API)
├── .env.example             # Environment template
└── database/
    └── mysql_setup.py       # MySQL database connection & operations
```

### **Frontend (React Native)**
```
frontend/
├── app/
│   ├── _layout.jsx          # Root layout
│   ├── (tabs)/
│   │   ├── _layout.jsx      # Tab navigation layout
│   │   ├── home.jsx         # Dashboard with statistics
│   │   ├── news.jsx         # Classified disaster news (verified/rumors)
│   │   ├── resources.jsx    # Emergency resources
│   │   └── profile.jsx      # User profile
│   └── +not-found.jsx      # 404 page
├── components/
│   ├── TweetCard.jsx        # News post display component
│   └── LoadingSpinner.jsx   # Loading indicator
├── services/
│   └── api.js              # API client for backend communication
├── constants/
│   └── colors.js           # App color scheme
├── mocks/
│   └── newsData.js         # Mock data for development
└── package.json            # Node.js dependencies
```

### **ML Models**
```
models/
├── ensemble_disaster_shield.zip    # Complete ensemble model
├── meta_ensemble_lr.joblib         # Meta learner model
├── LinearSVM.joblib               # SVM classifier
├── tfidf_vectorizer.joblib        # Text vectorizer
└── distilbert_model/              # DistilBERT transformer model
```

### **Utilities (Optional)**
```
backend/
├── manual_refresh.py        # Manual data refresh script
├── quick_refresh.py         # Quick refresh with minimal output
├── refresh.bat             # Windows batch file for refresh
└── enhanced_data_sources.md # Documentation of data sources
```

## 🚀 **How to Run**

### **Backend:**
```bash
cd backend
python setup_database.py    # Setup MySQL database
python run_server.py        # Start API server (localhost:8000)
```

### **Frontend:**
```bash
cd frontend
npm install                 # Install dependencies
npm start                   # Start Expo development server
```

## 🔄 **System Features**

- **Automatic Updates**: Fetches Reddit data every hour
- **AI Classification**: Classifies posts as verified/rumor
- **MySQL Storage**: Persistent data storage
- **REST API**: Backend serves data to frontend
- **Mobile App**: React Native interface for iOS/Android/Web

## 📊 **Data Sources**

- **9 Reddit Communities**: news, worldnews, weather, earthquakes, NaturalDisasters, naturesfury, Preparedness, preppers, EmergencyManagement
- **26 Disaster Keywords**: earthquake, tsunami, flood, wildfire, hurricane, etc.
- **Real-time Classification**: AI-powered verification system