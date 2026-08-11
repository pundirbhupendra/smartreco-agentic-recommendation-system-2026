"""Frontend page routes for the SmartReco web UI."""
from types import SimpleNamespace
from typing import Any, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.services.auth_service import AuthService
from src.services.product_service import ProductService
from src.services.recommendation_service import RecommendationService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="frontend/templates")


def _session(request: Request) -> dict[str, Any]:
    return {
        "user_id": request.cookies.get("user_id"),
        "username": request.cookies.get("username", ""),
        "is_admin": request.cookies.get("is_admin") == "true",
        "token": request.cookies.get("access_token", ""),
    }


def _template_context(request: Request, **extra: Any) -> dict[str, Any]:
    context: dict[str, Any] = {
        "request": request,
        "session": _session(request),
        "get_flashed_messages": lambda with_categories=True: [],
        "csrf_token": lambda: "",
        "error": request.query_params.get("error"),
        "success": request.query_params.get("success"),
    }
    context.update(extra)
    return context


def _view_product(product: Any) -> Any:
    if product is None:
        return None
    return SimpleNamespace(
        id=product.id,
        title=getattr(product, "name", ""),
        name=getattr(product, "name", ""),
        description=getattr(product, "description", ""),
        category=getattr(product, "category", "General") or "General",
        price=getattr(product, "price", 0.0),
    )


@router.get("/", name="home")
async def home(request: Request):
    return templates.TemplateResponse("index.html", _template_context(request))


@router.get("/login", name="login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", _template_context(request))


@router.post("/login", name="login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(email, password)
    if not user:
        return RedirectResponse("/login?error=Invalid email or password", status_code=status.HTTP_303_SEE_OTHER)

    token = auth_service.create_access_token(user.id)
    response = RedirectResponse("/dashboard?success=Login successful", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    response.set_cookie("user_id", str(user.id), samesite="lax")
    response.set_cookie("username", user.username, samesite="lax")
    response.set_cookie("is_admin", "true" if user.id == 1 else "false", samesite="lax")
    return response


@router.get("/signup", name="signup")
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", _template_context(request))


@router.post("/signup", name="signup")
async def signup_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    if auth_service.user_repo.user_exists(email):
        return RedirectResponse("/signup?error=Email already registered", status_code=status.HTTP_303_SEE_OTHER)

    user = auth_service.register_user(username=username, email=email, password=password)
    if not user:
        return RedirectResponse("/signup?error=Failed to create user", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse("/login?success=Account created. Please sign in.", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout", name="logout")
async def logout():
    response = RedirectResponse("/?success=Logged out", status_code=status.HTTP_303_SEE_OTHER)
    for name in ("access_token", "user_id", "username", "is_admin"):
        response.delete_cookie(name)
    return response


@router.get("/dashboard", name="dashboard")
async def dashboard(request: Request):
    stats = {"viewed_products": 0, "searches": 0, "recommendations": 0, "interests": 0}`r`n    insights = {"ai_ml": 0, "development": 0, "data_science": 0, "cloud": 0}`r`n    recent_activity = []
    return templates.TemplateResponse(
        "dashboard.html",
        _template_context(`r`n            request,`r`n            stats=stats,`r`n            latest_recommendation=None,`r`n            insights=insights,`r`n            recent_activity=recent_activity,`r`n        ),
    )


@router.get("/products", name="products")
async def products(
    request: Request,
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    product_service = ProductService(db)
    if q:
        items = product_service.search_products(q, 0, 100)
    elif category:
        items = product_service.get_products_by_category(category, 0, 100)
    else:
        items = product_service.get_all_products(0, 100)

    view_products = [_view_product(product) for product in items]
    categories = sorted({product.category for product in view_products if product and product.category})
    return templates.TemplateResponse(
        "products.html",
        _template_context(
            request,
            products=view_products,
            categories=categories,
            current_category=category,
            search_query=q,
        ),
    )


@router.get("/products/{product_id}", name="product_detail")
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    product = product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    similar = [item for item in product_service.get_products_by_category(product.category, 0, 4) if item.id != product.id]
    return templates.TemplateResponse(
        "product_detail.html",
        _template_context(
            request,
            product=_view_product(product),
            similar_products=[_view_product(item) for item in similar[:3]],
        ),
    )


@router.get("/product/{product_id}")
async def product_detail_compat(product_id: int):
    return RedirectResponse(f"/products/{product_id}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/recommendations", name="recommendations")
async def recommendations(request: Request, db: Session = Depends(get_db)):
    session = _session(request)
    user_id = session.get("user_id")
    recs = []
    if user_id:
        feed = RecommendationService(db).get_recommendation_feed(int(user_id), 5)
        recs = feed.get("recommendations", []) if isinstance(feed, dict) else []

    return templates.TemplateResponse(
        "recommendations.html",
        _template_context(request, recommendations=recs),
    )


@router.get("/admin/dashboard", name="admin_dashboard")
async def admin_dashboard(request: Request):
    stats = {"total_products": 0, "total_users": 0, "total_events": 0, "total_recommendations": 0}
    return templates.TemplateResponse("admin/dashboard.html", _template_context(request, stats=stats))


@router.get("/admin/products", name="manage_products")
async def manage_products(request: Request, db: Session = Depends(get_db)):
    products = [_view_product(product) for product in ProductService(db).get_all_products(0, 1000)]
    return templates.TemplateResponse("admin/product_manage.html", _template_context(request, products=products))

def _product_json(product: Any) -> dict[str, Any]:
    view = _view_product(product)
    return {
        "id": view.id,
        "title": view.title,
        "name": view.name,
        "description": view.description,
        "category": view.category,
        "price": view.price,
    }


@router.get("/api/search")
async def api_search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    products = ProductService(db).search_products(q, 0, 20)
    return {"results": [_product_json(product) for product in products]}


@router.post("/api/track-events")
async def api_track_events(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    events = payload.get("events", []) if isinstance(payload, dict) else []
    session = _session(request)
    user_id = session.get("user_id")

    if not user_id:
        return {"success": True, "tracked": 0, "skipped": len(events)}

    event_data = []
    for event in events:
        if not isinstance(event, dict) or not event.get("product_id"):
            continue
        event_data.append(
            {
                "user_id": int(user_id),
                "product_id": int(event["product_id"]),
                "score": 1.0,
            }
        )

    if not event_data:
        return {"success": True, "tracked": 0, "skipped": len(events)}

    from src.services.event_service import EventService

    tracked = EventService(db).batch_track_events(event_data)
    return {"success": True, "tracked": len(tracked), "skipped": len(events) - len(event_data)}


@router.post("/api/refresh-recommendations")
async def api_refresh_recommendations(request: Request, db: Session = Depends(get_db)):
    session = _session(request)
    user_id = session.get("user_id")
    if not user_id:
        return {"success": False, "message": "Login required"}

    recommendations = RecommendationService(db).get_or_generate_recommendation(int(user_id))
    return {"success": bool(recommendations), "recommendations": recommendations or []}


@router.post("/api/cart/add")
async def api_add_to_cart():
    return {"success": True}
