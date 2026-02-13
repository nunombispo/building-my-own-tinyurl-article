from fastapi import FastAPI, HTTPException, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional
import uvicorn

from database import engine, get_db, Base
from models import URL, Click
from utils import encode_id, validate_url, validate_custom_slug, parse_user_agent

# Reserved slugs that cannot be used as custom slugs
RESERVED_SLUGS = {"stats", "shorten", "admin", "login", "logout"}

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="TinyURL Clone",
    description="A self-hosted URL shortener with analytics",
    version="1.0.0"
)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request):
    """
    Homepage with URL shortening form
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/shorten")
async def create_short_url(
    request: Request,
    long_url: str = Form(...),
    custom_slug: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Create a new short URL
    
    Args:
        long_url: The long URL to shorten
        custom_slug: Optional custom slug (if not provided, auto-generated)
        db: Database session
        
    Returns:
        JSON with short_url and slug
    """
    # Validate URL
    if not validate_url(long_url):
        raise HTTPException(
            status_code=400, 
            detail="Invalid URL. Must start with http:// or https://"
        )
    
    # Handle custom slug
    if custom_slug:
        custom_slug = custom_slug.strip().lower()  # Normalize to lowercase
        
        # Check if slug is reserved
        if custom_slug in RESERVED_SLUGS:
            raise HTTPException(
                status_code=400,
                detail=f"Slug '{custom_slug}' is reserved. Please choose another."
            )
        
        # Validate custom slug format
        if not validate_custom_slug(custom_slug):
            raise HTTPException(
                status_code=400,
                detail="Invalid slug. Use 3-50 alphanumeric characters, hyphens, or underscores."
            )
        
        # Check if custom slug already exists
        existing = db.query(URL).filter(URL.slug == custom_slug).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Slug '{custom_slug}' is already taken. Please choose another."
            )
        
        # Create URL with custom slug
        new_url = URL(slug=custom_slug, long_url=long_url)
        db.add(new_url)
        
        try:
            db.commit()
            db.refresh(new_url)
        except Exception as e:
            db.rollback()
            print(f"Error creating short URL with custom slug: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create short URL: {str(e)}")
        
    else:
        # Create URL with auto-generated slug
        new_url = URL(long_url=long_url, slug="temp")
        db.add(new_url)
        
        try:
            db.flush()  # Get the auto-increment ID
            
            # Generate slug from ID
            slug = encode_id(new_url.id)
            new_url.slug = slug
            
            db.commit()
            db.refresh(new_url)
        except Exception as e:
            db.rollback()
            print(f"Error creating short URL with auto-generated slug: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create short URL: {str(e)}")
    
    # Build full short URL properly
    # Use base_url which handles proxy headers correctly
    base_url = str(request.base_url).rstrip('/')
    short_url = f"{base_url}/{new_url.slug}"
    
    return {
        "short_url": short_url,
        "slug": new_url.slug,
        "long_url": new_url.long_url
    }

@app.get("/{slug}")
async def redirect_to_long_url(
    slug: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Redirect short URL to original URL and track analytics
    
    Args:
        slug: Short URL slug
        request: FastAPI request object
        db: Database session
        
    Returns:
        Redirect to the original long URL
    """
    # Look up URL
    url = db.query(URL).filter(URL.slug == slug).first()
    
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    # Check expiration
    if url.expires_at:
        expires_at_aware = url.expires_at.replace(tzinfo=timezone.utc) if url.expires_at.tzinfo is None else url.expires_at
        if datetime.now(timezone.utc) > expires_at_aware:
            raise HTTPException(status_code=410, detail="This URL has expired")
    
    # Parse user agent
    user_agent_string = request.headers.get("user-agent")
    device_info = parse_user_agent(user_agent_string)
    
    # Track click analytics
    try:
        click = Click(
            url_id=url.id,
            referrer=request.headers.get("referer"),
            user_agent=user_agent_string,
            ip_address=request.client.host if request.client else None,
            device_type=device_info["device_type"],
            browser=device_info["browser"],
            os=device_info["os"]
        )
        db.add(click)
        db.commit()
    except Exception:
        # Don't fail redirect if analytics tracking fails
        db.rollback()
    
    # Redirect to long URL
    return RedirectResponse(url=url.long_url, status_code=302)

@app.get("/stats/{slug}", response_class=HTMLResponse)
async def get_stats(
    slug: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    View analytics for a short URL
    
    Args:
        slug: Short URL slug
        request: FastAPI request object
        db: Database session
        
    Returns:
        HTML page with analytics dashboard
    """
    url = db.query(URL).filter(URL.slug == slug).first()
    
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    # Get click statistics
    clicks = url.clicks
    
    # Calculate unique IPs
    unique_ips = len(set(click.ip_address for click in clicks if click.ip_address))
    
    # Get click count efficiently
    click_count = db.query(func.count(Click.id)).filter(Click.url_id == url.id).scalar()
    
    # Calculate average clicks per day
    created_at_aware = url.created_at.replace(tzinfo=timezone.utc) if url.created_at.tzinfo is None else url.created_at
    days_since_creation = (datetime.now(timezone.utc) - created_at_aware).days or 1
    avg_clicks_per_day = round(click_count / days_since_creation, 1)
    
    # Group clicks by date for chart
    clicks_by_date = {}
    for click in clicks:
        date_key = click.timestamp.strftime('%Y-%m-%d')
        clicks_by_date[date_key] = clicks_by_date.get(date_key, 0) + 1
    
    # Group by device type
    clicks_by_device = {}
    for click in clicks:
        device = click.device_type or "unknown"
        clicks_by_device[device] = clicks_by_device.get(device, 0) + 1
    
    # Group by referrer
    clicks_by_referrer = {}
    for click in clicks:
        referrer = click.referrer or "Direct"
        # Shorten long referrers
        if len(referrer) > 50:
            referrer = referrer[:47] + "..."
        clicks_by_referrer[referrer] = clicks_by_referrer.get(referrer, 0) + 1
    
    # Get recent clicks (last 20, most recent first)
    recent_clicks = list(reversed(clicks[-20:]))
    
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "url": url,
        "clicks": clicks,
        "recent_clicks": recent_clicks,
        "unique_ips": unique_ips,
        "days_since_creation": days_since_creation,
        "avg_clicks_per_day": avg_clicks_per_day,
        "clicks_by_date": clicks_by_date,
        "clicks_by_device": clicks_by_device,
        "clicks_by_referrer": clicks_by_referrer
    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
