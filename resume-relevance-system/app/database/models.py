from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import Config

Base = declarative_base()
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ResumeEvaluation(Base):
    __tablename__ = "resume_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String(255))
    candidate_email = Column(String(255))
    job_title = Column(String(255))
    company = Column(String(255))
    location = Column(String(255))
    resume_filename = Column(String(255))
    jd_filename = Column(String(255))
    overall_score = Column(Float)
    verdict = Column(String(50))
    hard_match_score = Column(Float)
    semantic_score = Column(Float)
    experience_score = Column(Float)
    matched_skills = Column(JSON)
    missing_required_skills = Column(JSON)
    missing_preferred_skills = Column(JSON)
    recommendations = Column(JSON)
    feedback = Column(Text)
    evaluation_date = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_name': self.candidate_name,
            'candidate_email': self.candidate_email,
            'job_title': self.job_title,
            'company': self.company,
            'location': self.location,
            'overall_score': self.overall_score,
            'verdict': self.verdict,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None
        }

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    company = Column(String(255))
    location = Column(String(255))
    description = Column(Text)
    required_skills = Column(JSON)
    preferred_skills = Column(JSON)
    experience_required = Column(String(100))
    education_required = Column(String(255))
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'required_skills': self.required_skills,
            'preferred_skills': self.preferred_skills,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }

# Create tables
Base.metadata.create_all(bind=engine)

# Database operations
class DatabaseOperations:
    @staticmethod
    def save_evaluation(evaluation_data: dict):
        """Save evaluation results to database"""
        db = SessionLocal()
        try:
            evaluation = ResumeEvaluation(**evaluation_data)
            db.add(evaluation)
            db.commit()
            db.refresh(evaluation)
            return evaluation
        except Exception as e:
            db.rollback()
            print(f"Database error: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_evaluations(job_title: str = None, verdict: str = None):
        """Get evaluations with optional filters"""
        db = SessionLocal()
        try:
            query = db.query(ResumeEvaluation)
            if job_title:
                query = query.filter(ResumeEvaluation.job_title == job_title)
            if verdict:
                query = query.filter(ResumeEvaluation.verdict == verdict)
            return query.all()
        finally:
            db.close()
    
    @staticmethod
    def save_job_description(jd_data: dict):
        """Save job description to database"""
        db = SessionLocal()
        try:
            jd = JobDescription(**jd_data)
            db.add(jd)
            db.commit()
            db.refresh(jd)
            return jd
        except Exception as e:
            db.rollback()
            print(f"Database error: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_job_descriptions():
        """Get all job descriptions"""
        db = SessionLocal()
        try:
            return db.query(JobDescription).all()
        finally:
            db.close()