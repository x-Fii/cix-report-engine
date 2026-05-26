import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env file
load_dotenv()

# Build connection string for MariaDB using mysql-connector-python
DB_USER = os.getenv("DB_USER", "cix_app")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cl1ck1x123")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "cix_engine")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Initialize persistent engine pool configuration for MariaDB
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Automatically tests/recovers broken database sockets
    pool_recycle=3600    # Prevents silent connection timeouts on the network layer
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency utility function to safely distribute and close sessions per API request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
