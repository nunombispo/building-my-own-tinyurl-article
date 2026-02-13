from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite database configuration
# Can be overridden with environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./urls.db")

# Create engine with appropriate connect_args
connect_args = {}
engine_args = {"echo": False}  # Set to True for SQL debugging

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 30  # Increase timeout for Windows
    }
    # Use pool_pre_ping to handle stale connections
    engine_args["pool_pre_ping"] = True

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args,
    **engine_args
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
