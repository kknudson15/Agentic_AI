from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///feedback.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    is_helpful = Column(Boolean, nullable=False)
    sources = Column(Text)  # JSON string of sources

# Create table if not exists
Base.metadata.create_all(bind=engine)

def add_feedback(query: str, answer: str, is_helpful: bool, sources: str):
    session = SessionLocal()
    fb = Feedback(query=query, answer=answer, is_helpful=is_helpful, sources=sources)
    session.add(fb)
    session.commit()
    session.close()
    return {"status": "recorded"}