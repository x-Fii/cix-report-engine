# database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Map connection string parameters to the local loopback socket interface
DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# Initialize persistent engine pool configuration
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
