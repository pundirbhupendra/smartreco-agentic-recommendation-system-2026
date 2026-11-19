# SmartReco Learning Plan

This is a section-by-section learning guide for building and understanding SmartReco as a first AI project. Complete one section at a time. Do not move to the next section until the current "Done when" check works.

## How To Use This Guide

- Work on one section only.
- Run the app and test the result after each section.
- Keep AI integrations disabled until Section 6.
- Prefer simple, explainable code before adding agent workflows or cloud services.

## Section 0: Learn the Project Structure

**Goal:** Understand how an HTTP request becomes saved data.

### Learn

- FastAPI creates API endpoints in `src/routes`.
- Services in `src/services` hold business rules.
- Repositories in `src/repositories` read and write the database.
- SQLAlchemy models in `src/database/models` describe database tables.

### Read These Files

- `src/main.py`
- `src/routes/auth.py`
- `src/services/auth_service.py`
- `src/repositories/user_repository.py`
- `src/database/models/user.py`

### Exercise

Trace the `POST /auth/register` flow from the route to the `users` database table. Write down the responsibility of each layer in your own words.

### Done When

You can explain this flow:

```text
Browser or API client -> auth route -> auth service -> user repository -> users table
```

## Section 1: Run and Explore the API

**Goal:** Learn how to run a FastAPI application and test endpoints with Swagger.

### Learn

- Environment variables configure the application.
- Uvicorn runs the FastAPI server.
- FastAPI automatically provides Swagger documentation at `/docs`.
- JWT tokens protect private endpoints.

### Exercise

1. Configure SQLite and JWT settings in `.env`.
2. Run `uvicorn src.main:app --reload`.
3. Open `http://localhost:8000/docs`.
4. Register a user with `POST /auth/register`.
5. Log in with `POST /auth/login`.
6. Use the returned token to call `GET /auth/me`.

### Done When

You can register, log in, and call an authenticated endpoint successfully.

## Section 2: Learn Database CRUD Through Products

**Goal:** Understand how application data is saved, queried, changed, and deleted.

### Learn

- A Pydantic model validates API input and output.
- A SQLAlchemy model maps Python fields to database columns.
- A repository isolates database queries from business logic.
- A service coordinates application rules.

### Read These Files

- `src/database/models/product.py`
- `src/repositories/product_repository.py`
- `src/services/product_service.py`
- `src/routes/products.py`

### Exercise

Using Swagger or the frontend, create several courses with different names and descriptions. List them, search them, update one, and delete one.

### Done When

Products can be created, read, updated, deleted, and still exist after restarting the server.

## Section 3: Learn Behavioural Event Tracking

**Goal:** Capture what a user does, such as viewing or clicking a product.

### Learn

- Events are the raw data used for personalization.
- Batching events reduces browser-to-server requests.
- The backend must validate that a user can only submit their own events.
- Event data should use one consistent schema across frontend and backend.

### Read These Files

- `frontend/static/js/tracking.js`
- `src/routes/events.py`
- `src/services/event_service.py`
- `src/database/models/user_event.py`

### Important Current Gap

The frontend tracker currently posts to `/api/track-events` with fields such as `event_type` and `timestamp`. The backend accepts batches at `/api/events/batch` and expects `user_id`, `product_id`, `score`, and `created_at`.

Before expanding tracking, choose one canonical event format and make both sides use it. Start with the backend's smaller format:

```json
{
  "user_id": 1,
  "product_id": 5,
  "score": 0.85,
  "created_at": "2026-08-18T10:00:00Z"
}
```

### Exercise

Submit a batch of product-view events for the logged-in user. Then call the event summary endpoint and inspect the total events, unique products, and average score.

### Done When

A real product interaction is batched by the frontend and appears in the event summary API response.

## Section 4: Build Recommendations Without AI

**Goal:** Understand recommendation logic before using an LLM.

### Learn

- Cold-start users have no event history, so they need popular products.
- Active users can receive products based on their past interactions.
- Simple scoring rules are easier to test and explain than AI output.
- Recommendations must be stored so the application can display them later.

### Read These Files

- `src/services/recommendation_service.py`
- `src/services/event_service.py`
- `src/repositories/recommendation_repository.py`
- `src/repositories/product_repository.py`
- `src/routes/recommendations.py`

### Exercise

Make the recommendation rules deterministic:

1. A user with no events receives popular products.
2. A user with events receives products related to viewed products.
3. Rank candidates using interaction count and recency.
4. Save the best five products in the recommendations table.
5. Return them from the recommendation feed endpoint.

### Done When

Two users with different product activity receive different, explainable recommendations without any Mesh API key.

## Section 5: Add Automated Tests

**Goal:** Make changes confidently and prevent regressions.

### Learn

- Tests should use a temporary SQLite database.
- Tests should not require the internet or paid services.
- External dependencies should be mocked.

### Add Tests For

- User registration and login
- Protected endpoint access
- Product CRUD and search
- Event batching and authorization
- Cold-start recommendations
- Active-user recommendations
- Recommendation refresh threshold
- Users trying to access another user's recommendations

### Exercise

Add `pytest` and FastAPI test-client fixtures. Ensure every test starts with an isolated database.

### Done When

All core tests run locally with one command and require no Mesh, vector database, email server, or internet connection.

### Current Status

Completed. The isolated suite currently covers:

- Registration and invalid login
- Product create, list, search, update, and delete
- Bearer-token event batches
- Cookie-authenticated activity summaries
- Cross-user event rejection
- Active-user deterministic recommendations
- Cold-start recommendations

Run the suite with:

```powershell
& 'C:\Users\win-10\miniconda3\envs\smartreco-py312\python.exe' -m pytest tests -q
```

The test suite passed with 7 tests and does not call Mesh or Qdrant.

## Section 6: Add LLM Basics With Mesh API

**Goal:** Use an LLM only where it adds value, while preserving a reliable non-AI fallback.

### Learn

- An LLM should be behind one application boundary.
- Model responses are not always valid, so validate them.
- AI should enhance selected recommendations, not be the only source of truth.
- Fallback behavior is required for unavailable AI services.

### Read These Files

- `src/services/llm_service.py`
- `src/services/recommendation_service.py`

### Exercise

Start with one job: generate a short personalized recommendation narrative after deterministic code has selected the products.

Add:

- Mesh API configuration in `.env`
- Request timeouts and useful error logging
- A fake LLM service for tests and local development
- A static fallback narrative if Mesh fails
- Structured validation for JSON evaluation responses

### Done When

The same products are returned whether Mesh is available or not, but a working LLM adds a personalized message.

## Section 7: Learn Semantic Search and Vector Databases

**Goal:** Retrieve relevant products by meaning, not only exact keywords.

### Learn

- Embeddings represent text as numbers.
- A vector database finds nearby embeddings.
- Product creation, updates, and deletion must synchronize SQL and vector data.

### Current State

`ProductService._sync_to_vector_db` is currently a placeholder. The recommender uses SQL text search today.

### Recommended Learning Order

1. Start with local Chroma because its dependencies are already included.
2. Create product text with `ProductService.get_product_embedding_context`.
3. Generate and store embeddings on product creation and update.
4. Remove embeddings when a product is deleted.
5. Compare semantic results with SQL keyword search.
6. Add Pinecone later as a second vector-store implementation.

### Done When

A search with different wording can still retrieve the expected related course.

## Section 8: Learn LangGraph Agent Workflows

**Goal:** Orchestrate multiple recommendation steps in a visible, testable workflow.

### Current State

The `src/agent` folder is currently empty. Build this only after Sections 4 through 7 work.

### Create These Nodes

1. Load user activity.
2. Choose cold-start or active-user path.
3. Retrieve product candidates.
4. Score or rerank candidates.
5. Generate a recommendation narrative.
6. Persist recommendations.

### Design Rule

Keep deterministic logic in normal Python services. Use LangGraph to coordinate steps, not to hide all application rules inside prompts.

### Exercise

Create `src/agent/recommendation_agent.py` with a small explicit graph state. Call it through `RecommendationService`, not directly from a route.

### Done When

One recommendation request logs each node, returns valid results, and stores the recommendation successfully.

## Section 9: Add Optional Production Features

**Goal:** Add operational features without making the core application fragile.

### Learn Next

- Caching for recommendation results
- LangSmith tracing
- APScheduler daily digest jobs
- Email delivery
- Vector synchronization recovery

### Rule

Every external integration must be optional through configuration. A failed email, cache, trace, or vector synchronization must not lose SQL product data or block a normal user request.

### Done When

You can manually run a development digest job and inspect the result without affecting normal requests.

## Section 10: Prepare for Deployment

**Goal:** Make the project reproducible for another developer or deployment environment.

### Add

- `.env.example` without secrets
- Database migration strategy
- Health and readiness endpoints
- Structured logs
- Docker validation
- CI workflow that runs tests
- Documentation that clearly separates implemented features from planned features

### Done When

A fresh machine can follow the documentation to run the app, create products, track events, generate recommendations, and run the test suite.

## Recommended Study Order

```text
FastAPI and database
    -> products and CRUD
    -> events
    -> deterministic recommendations
    -> tests
    -> LLM narrative generation
    -> vector search
    -> LangGraph workflow
    -> scheduler, email, tracing, deployment
```

## Key Principle

SmartReco becomes an AI project only after its data flow is trustworthy. First make the application collect clean events and create explainable recommendations. Then use AI to improve language, semantic retrieval, and workflow orchestration.