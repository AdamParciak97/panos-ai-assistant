from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine("sqlite:///assistant.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    question = Column(Text)
    rag_answer = Column(Text)
    ft_answer = Column(Text)
    rag_rating = Column(Integer, nullable=True)   # 1 lub -1
    ft_rating = Column(Integer, nullable=True)
    sources = Column(Text)  # JSON lista źródeł


Base.metadata.create_all(bind=engine)


def save_conversation(question, rag_answer, ft_answer, sources=""):
    db = SessionLocal()
    record = Conversation(
        question=question,
        rag_answer=rag_answer,
        ft_answer=ft_answer,
        sources=sources
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    db.close()
    return record.id


def update_rating(conv_id, mode, rating):
    db = SessionLocal()
    record = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if record:
        if mode == "rag":
            record.rag_rating = rating
        else:
            record.ft_rating = rating
        db.commit()
    db.close()


def get_history(limit=50):
    db = SessionLocal()
    records = db.query(Conversation).order_by(Conversation.timestamp.desc()).limit(limit).all()
    db.close()
    return records
