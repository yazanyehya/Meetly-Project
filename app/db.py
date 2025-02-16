import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.auth.models import Base


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") 

engine = create_engine(DATABASE_URL,echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

