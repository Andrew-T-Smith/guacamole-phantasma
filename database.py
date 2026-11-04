from sqlmodel import SQLModel, create_engine
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
