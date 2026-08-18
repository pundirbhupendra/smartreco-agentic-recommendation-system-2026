# SmartReco: Agentic AI Recommendation System 🚀

**An intelligent, behavioral AI recommendation engine for online learning platforms.**

Watch how users behave, understand their interests, and intelligently recommend the right products with AI-generated, persuasive messaging that actually motivates action.

This is **not** a simple "related products" widget — it's a fully agentic system with behavioral tracking, semantic retrieval, and personalized narrative generation.

---

## 🎯 Project Overview

SmartReco is a complete recommendation platform built for the **SmartReco Build Challenge 2026**, combining:
- **Behavioral Event Tracking** - non-blocking, batched user activity capture
- **Dual-Write Product System** - products sync between SQL and Vector DB
- **LangGraph Agentic Engine** - structured reasoning workflow
- **Semantic Retrieval** - RAG-based product matching via Pinecone
- **Mesh API Integration** - all LLM calls routed through Mesh (mandatory)
- **Personalized Generation** - compelling narratives tailored to user interests
- **Scheduled Delivery** - daily email digests with recommendations (bonus)
- **Observability** - LangSmith tracing for every agent workflow (bonus)

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                  SMARTRECO SYSTEM ARCHITECTURE                    │
└──────────────────────────────────────────────────────────────────┘

1. BEHAVIORAL EVENT TRACKING (Frontend)
   └─→ Page views, searches, clicks, time spent
       Batched & non-blocking to prevent UI lag

2. DUAL-WRITE PRODUCT MANAGEMENT (Admin)
   Product Added/Updated
   └─→ Write to PostgreSQL Database
   └─→ Simultaneously sync to Pinecone Vector DB
       (Kept in sync with validation checks)

3. EVENT INGESTION & AGGREGATION (Backend)
   Events collected → Stored in user_events table
   → Aggregated for user profile analysis

4. USER STATE IDENTIFICATION
   ├─ NEW/COLD USER (no activity history)
   │  └─→ Popular/Trending Products (hardcoded or top-rated)
   │
   └─ ACTIVE USER (behavioral history exists)
      └─→ Analyze recent activity, search history, time spent
          └─→ Build interest profile

5. AGENTIC RECOMMENDATION ENGINE (LangGraph)
   ┌─────────────────────────────────────────┐
   │  Node 1: Analyze User Activity          │
   │  - Aggregate recent events              │
   │  - Extract interests & learning goals   │
   └──────────────┬──────────────────────────┘
                  │
   ┌──────────────▼──────────────────────────┐
   │  Node 2: Build Search Query             │
   │  - LLM generates semantic search query  │
   │  - Via Mesh API (openai/gpt-4o)        │
   └──────────────┬──────────────────────────┘
                  │
   ┌──────────────▼──────────────────────────┐
   │  Node 3: Semantic Retrieval             │
   │  - Query Pinecone Vector DB             │
   │  - Fetch top-K relevant products        │
   │  - Apply metadata filters if needed     │
   └──────────────┬──────────────────────────┘
                  │
   ┌──────────────▼──────────────────────────┐
   │  Node 4: Re-rank & Evaluate             │
   │  - Score results based on user fit      │
   │  - Optionally refine query if poor fit  │
   │  - Check cache to avoid redundancy      │
   └──────────────┬──────────────────────────┘
                  │
   ┌──────────────▼──────────────────────────┐
   │  Node 5: Generate Recommendation        │
   │  - Build persuasive narrative           │
   │  - Reflect user's journey & interests   │
   │  - Via Mesh API LLM                     │
   │  - Include specific product recommendations
   └──────────────┬──────────────────────────┘
                  │
   ┌──────────────▼──────────────────────────┐
   │  Node 6: Evaluate & Store               │
   │  - Persist to recommendations table     │
   │  - Log reasoning & confidence scores    │
   │  - Trace via LangSmith                  │
   └─────────────────────────────────────────┘

6. CACHING & EFFICIENCY LAYER
   ├─ Cache recommendations per user
   ├─ Track last refresh timestamp
   ├─ Trigger only on significant behavior change
   └─ Avoid redundant LLM calls (cost + latency)

7. SCHEDULED PROACTIVE DELIVERY (APScheduler)
   Daily at 9 AM
   └─→ Fetch yesterday's activities
   └─→ Generate daily digest recommendations
   └─→ Send via email with persuasive narrative

8. API ENDPOINTS
   POST   /auth/register                - User registration
   POST   /auth/login                   - User login (JWT)
   GET    /products                     - Browse products
   GET    /recommendations/{user_id}    - Get recommendations
   POST   /events/batch                 - Track user activity
   POST   /admin/products               - Create product (dual-write)
   PUT    /admin/products/{id}          - Update product (sync)
   DELETE /admin/products/{id}          - Delete product (sync)
```

---

## ✨ Key Features

### Core Features
- ✅ **User Authentication** - JWT-based login with user/admin roles
- ✅ **Product Management** - Admin CRUD with dual-write (SQL + Vector DB)
- ✅ **Behavioral Event Tracking** - Non-blocking, batched event ingestion
- ✅ **Recommendation Engine** - LangGraph-based agentic workflow
- ✅ **Semantic Retrieval** - RAG via Pinecone Vector DB
- ✅ **Mesh API Integration** - All LLM calls routed through Mesh (mandatory)

### Bonus Features (Implemented ⭐)
- ⭐ **LangGraph Agent** - Explicit reasoning workflow with multiple nodes
- ⭐ **APScheduler** - Scheduled daily email digest delivery
- ⭐ **LangSmith Observability** - Full tracing of agent workflows
- ⭐ **Smart Re-ranking** - Evaluate and refine retrieval results
- ⭐ **Caching Layer** - Avoid redundant LLM calls

---

## 📋 Requirements

- Python 3.11+
- PostgreSQL (or SQLite for development)
- Pinecone API account (vector database)
- Mesh API key (mandatory for LLM access)
- GitHub account (for Actions secrets)

---

## 🚀 Quick Start

### 1. Clone & Setup Environment
```bash
git clone https://github.com/yourusername/smartreco-agentic-recommendation-system-2026.git
cd smartreco-agentic-recommendation-system-2026

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file (add to `.gitignore`):
```env
# Mesh API (Mandatory)
MESH_API_KEY=rsk_your_mesh_api_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/smartreco
# or for SQLite: DATABASE_URL=sqlite:///./smartreco.db

# Pinecone Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENV=your_pinecone_environment
PINECONE_INDEX_NAME=smartreco-products

# JWT Secret
JWT_SECRET_KEY=your_super_secret_jwt_key_here
JWT_ALGORITHM=HS256

# Email Configuration (for APScheduler digest)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# LangSmith Tracing (Optional - for observability bonus)
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=smartreco-2026
```

### 3. Initialize Database
```bash
# Create tables
python -m alembic upgrade head

# Or for SQLite (dev):
python src/database/db.py
```

### 4. Run Locally
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API available at: **http://localhost:8000**

Swagger docs: **http://localhost:8000/docs**

### 5. Run with Docker
```bash
docker build -t smartreco .
docker run -p 8000:8000 --env-file .env smartreco
```

---

## 📁 Project Structure

```
smartreco-agentic-recommendation-system-2026/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config/
│   │   └── settings.py            # Environment configuration
│   ├── database/
│   │   ├── db.py                  # SQLAlchemy setup
│   │   └── models/
│   │       ├── user.py            # User model
│   │       ├── product.py         # Product model
│   │       ├── recommendation.py  # Recommendation model
│   │       ├── user_activity.py   # User activity tracking
│   │       └── user_event.py      # User events (page views, clicks, etc.)
│   ├── routes/
│   │   ├── auth.py                # Login/register endpoints
│   │   ├── products.py            # Product CRUD (admin)
│   │   ├── recommendations.py     # Recommendation retrieval
│   │   └── events.py              # Event tracking endpoint
│   ├── services/
│   │   ├── auth_service.py        # JWT & password hashing
│   │   ├── product_service.py     # Product dual-write logic
│   │   ├── event_service.py       # Event ingestion & aggregation
│   │   ├── llm_service.py         # Mesh API LLM calls
│   │   ├── vector_service.py      # Pinecone semantic retrieval
│   │   └── recommendation_service.py # Core recommendation logic
│   ├── agent/
│   │   └── recommendation_agent.py # LangGraph agentic workflow
│   ├── scheduler/
│   │   └── tasks.py               # APScheduler jobs (email digests)
│   ├── infrastructure/
│   │   ├── cache/
│   │   │   └── redis_cache.py     # Caching layer
│   │   ├── email/
│   │   │   └── email_service.py   # Email delivery
│   │   ├── llm/
│   │   │   └── mesh_client.py     # Mesh API wrapper
│   │   ├── vector_store/
│   │   │   └── pinecone_client.py # Pinecone integration
│   │   └── logging_config/
│   │       └── config.py          # Logging setup
│   ├── middleware/
│   │   └── request_logging.py     # Request/response logging
│   └── logging_config/
│       └── config.py              # Application logging
├── frontend/
│   ├── templates/
│   │   ├── base.html              # Base Jinja2 template
│   │   ├── dashboard.html         # User dashboard
│   │   ├── products.html          # Product browse page
│   │   └── admin.html             # Admin panel
│   ├── static/
│   │   ├── js/
│   │   │   └── event_tracker.js   # Non-blocking event tracking
│   │   └── css/
│   │       └── styles.css         # Styling
│   └── index.py                   # Frontend routes
├── .github/
│   └── workflows/
│       └── smartreco-checks.yml   # GitHub Actions CI/CD
├── tests/
│   ├── test_auth.py
│   ├── test_products.py
│   ├── test_recommendations.py
│   └── test_events.py
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker configuration
├── .gitignore                     # Git ignore (includes .env)
└── README.md                      # This file
```

---

## 🔧 Configuration & Setup

### Mesh API Setup (Mandatory)
1. Sign up at [Mesh API Dashboard](https://developers.meshapi.ai)
2. Create API key (starts with `rsk_`)
3. Add to `.env` as `MESH_API_KEY`

All LLM calls use this wrapper:
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.meshapi.ai/v1",
    api_key=os.getenv("MESH_API_KEY")
)

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Your prompt"}],
    temperature=0.7
)
```

### Pinecone Setup (Vector Database)
1. Create account at [Pinecone](https://www.pinecone.io/)
2. Create index: `smartreco-products` (dimension: 1536 for OpenAI embeddings)
3. Add API keys to `.env`

When admin adds a product, it's automatically:
1. Embedded via Mesh API
2. Indexed in Pinecone
3. Stored in PostgreSQL (dual-write)

### APScheduler Setup (Bonus - Daily Digests)
Runs scheduled jobs:
- **Time**: 9:00 AM daily
- **Action**: Generate digest recommendations for active users
- **Delivery**: Email via SMTP

---

## 📊 API Documentation

### Authentication
```bash
# Register
POST /auth/register
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123"
}

# Login
POST /auth/login
{
  "email": "john@example.com",
  "password": "securepassword123"
}
Response: { "access_token": "eyJ0eXAi...", "token_type": "bearer" }
```

### Event Tracking
```bash
# Batch submit events (non-blocking)
POST /events/batch
Authorization: Bearer {token}
{
  "events": [
    {
      "user_id": 1,
      "event_type": "product_view",
      "product_id": 5,
      "timestamp": "2026-08-10T14:30:00Z"
    },
    {
      "user_id": 1,
      "event_type": "search",
      "query": "machine learning",
      "timestamp": "2026-08-10T14:35:00Z"
    }
  ]
}
```

### Get Recommendations
```bash
GET /recommendations/1?limit=5
Authorization: Bearer {token}

Response:
{
  "user_id": 1,
  "narrative": "You've been diving deep into AI and machine learning courses...",
  "products": [
    {
      "id": 12,
      "name": "Advanced LangGraph Patterns",
      "score": 0.94
    },
    ...
  ],
  "generated_at": "2026-08-10T14:40:00Z",
  "refresh_reason": "significant_interest_shift"
}
```

### Admin: Create Product (Dual-Write)
```bash
POST /admin/products
Authorization: Bearer {admin_token}
{
  "name": "Deep Learning Fundamentals",
  "description": "Master neural networks from scratch...",
  "category": "AI/ML",
  "price": 99.99,
  "difficulty_level": "intermediate"
}

# Automatic actions:
# 1. Stored in PostgreSQL
# 2. Embedded & indexed in Pinecone
# 3. Available for recommendations immediately
```

---

## 🧠 Recommendation Engine Workflow

The LangGraph agent executes this workflow:

1. **Analyze Activity**: Extract user's recent behavior (searches, views, time spent)
2. **Build Query**: LLM generates optimal semantic search query
3. **Retrieve**: Query Pinecone for top products matching user interests
4. **Re-rank**: Score and evaluate retrieval quality
5. **Generate**: LLM creates personalized, persuasive narrative
6. **Store**: Persist recommendation with reasoning & scores
7. **Trace**: LangSmith logs every node execution (observability)

**Smart Triggering** - Recommendations refresh only when:
- User's behavior significantly changes
- Threshold: 5+ new events since last recommendation
- Time-based: Max 24 hours without refresh
- Caching prevents redundant LLM calls

---

## 🎁 Bonus Features Included

### ⭐ LangGraph Agentic Workflow
Explicit, observable reasoning pipeline with nodes for:
- Activity analysis
- Query generation
- Retrieval
- Re-ranking
- Narrative generation
- Evaluation & persistence

### ⭐ APScheduler Scheduled Delivery
Daily digest email at 9 AM with:
- Summary of user's activity from yesterday
- Personalized recommendations
- Click-through links to products
- Persuasive messaging tailored to their journey

### ⭐ LangSmith Observability
Every agent workflow is traced:
- Node execution time & outputs
- LLM call details (tokens, model)
- Retrieval quality metrics
- Full audit trail for debugging

### ⭐ Smart Re-ranking
Post-retrieval evaluation:
- Score products by user fit
- Optionally refine query if results poor
- Confidence scoring
- Metadata filtering

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_recommendations.py -v

# With coverage
pytest tests/ --cov=src
```

---

## 📝 GitHub Actions Setup

### 1. Add Workflow File
Download from challenge dashboard and place at:
```
.github/workflows/smartreco-checks.yml
```

### 2. Add Repository Secrets
Go to **Settings → Secrets and variables → Actions**:
- `MESH_API_KEY` - Your Mesh API key
- `SUBMISSION_TOKEN` - Your challenge submission token

### 3. Push & Verify
```bash
git add .github/workflows/smartreco-checks.yml
git commit -m "Add SmartReco CI/CD checks"
git push
```

Checks run automatically. View results in **Actions** tab.

---

## 🚀 Deployment

### Deploy to Heroku
```bash
heroku login
heroku create smartreco-app
heroku config:set MESH_API_KEY=rsk_...
heroku config:set DATABASE_URL=postgresql://...
heroku config:set PINECONE_API_KEY=...
git push heroku main
heroku logs --tail
```

### Deploy to Railway
```bash
railway up
```

### Deploy to AWS/GCP
See respective cloud provider documentation.

---

## 📚 Technologies Used

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | FastAPI |
| **Database** | PostgreSQL / SQLite |
| **Vector Database** | Pinecone |
| **LLM Gateway** | Mesh API |
| **Agent Framework** | LangGraph |
| **Scheduler** | APScheduler |
| **Observability** | LangSmith |
| **Authentication** | JWT |
| **Frontend** | Jinja2 + JavaScript |
| **ORM** | SQLAlchemy |

---

## 📖 Documentation

- [Mesh API Docs](https://developers.meshapi.ai/docs/introduction/product-overview)
- [LangGraph Docs](https://python.langchain.com/docs/langgraph)
- [Pinecone Docs](https://docs.pinecone.io/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [APScheduler Docs](https://apscheduler.readthedocs.io/)

---

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Submit a pull request

---

## 📄 License

This project is submitted to the **SmartReco Build Challenge 2026**.

---

## ⚠️ Important Notes

- **Never commit `.env`** - use `.gitignore`
- **Mesh API is mandatory** - all LLM calls must go through it
- **Dual-write is critical** - products must sync SQL ↔ Vector DB
- **Event tracking must be non-blocking** - batch & throttle on frontend
- **Cache recommendations** - avoid redundant LLM calls

---

## 🎯 Challenge Checklist

- ✅ Python FastAPI backend
- ✅ User authentication (JWT)
- ✅ Admin role for product management
- ✅ Behavioral event tracking (batched, non-blocking)
- ✅ Dual-write product system (SQL + Vector DB)
- ✅ Mesh API integration (mandatory)
- ✅ Agentic recommendation engine (LangGraph)
- ✅ Semantic retrieval (Pinecone RAG)
- ✅ Personalized narrative generation
- ✅ Recommendation persistence
- ✅ Smart refresh triggers
- ✅ Caching layer for efficiency
- ✅ LangGraph bonus (explicit agent workflow)
- ✅ APScheduler bonus (scheduled delivery)
- ✅ LangSmith bonus (full observability)

---

## 📞 Support

For issues or questions, open a GitHub issue or contact the challenge organizers.

**Built for the SmartReco Build Challenge 2026** 🏆
