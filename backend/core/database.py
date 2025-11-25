from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    play_money_balance = Column(Float, default=10000.0)

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_db_and_tables()