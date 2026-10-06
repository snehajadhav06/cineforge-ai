import os
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

# Database directory and SQLite URL
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "cineforge.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Default Project")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    generations = relationship("Generation", back_populates="project")
    videos = relationship("Video", back_populates="project")


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, default="default")
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    duration = Column(Integer, nullable=False, default=5)
    width = Column(Integer, nullable=False, default=1280)
    height = Column(Integer, nullable=False, default=720)
    fps = Column(Integer, nullable=False, default=24)
    format = Column(String, nullable=False, default="mp4")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="videos")


class Generation(Base):
    __tablename__ = "generations"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, default="default")
    prompt = Column(Text, nullable=False)
    enhanced_prompt = Column(Text, nullable=True)
    negative_prompt = Column(Text, nullable=False)
    mode = Column(String, nullable=False, default="text-to-video")  # text-to-video | image-to-video
    reference_image_url = Column(Text, nullable=True)
    model_id = Column(String, nullable=False, default="ltx-video")
    duration = Column(Integer, nullable=False, default=5)
    aspect_ratio = Column(String, nullable=False, default="16:9")
    resolution = Column(String, nullable=False, default="720p")
    fps = Column(Integer, nullable=False, default=24)
    seed = Column(Integer, nullable=False)
    is_fixed_seed = Column(Boolean, default=False)
    steps = Column(Integer, default=25)
    guidance = Column(Float, default=6.5)
    status = Column(String, default="completed")  # idle, queued, processing, completed, failed
    progress = Column(Float, default=100.0)
    current_step = Column(Integer, default=25)
    total_steps = Column(Integer, default=25)
    eta_seconds = Column(Integer, default=0)
    video_url = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False)
    sha256_hash = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="generations")


class PromptCache(Base):
    __tablename__ = "prompts"

    id = Column(String, primary_key=True, index=True)
    prompt_hash = Column(String, unique=True, index=True, nullable=False)
    original_prompt = Column(Text, nullable=False)
    enhanced_prompt = Column(Text, nullable=False)
    provider = Column(String, nullable=False, default="openrouter")
    created_at = Column(DateTime, default=datetime.utcnow)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, nullable=False)  # image | video | thumbnail
    file_path = Column(String, nullable=False)
    sha256_hash = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String, primary_key=True, index=True)
    generation_id = Column(String, ForeignKey("generations.id"), nullable=False)
    status = Column(String, default="queued")
    error_message = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Ensure default project exists
    db = SessionLocal()
    try:
        default_proj = db.query(Project).filter(Project.id == "default").first()
        if not default_proj:
            default_proj = Project(
                id="default",
                name="Default Studio Project",
                description="Default project for CineForge AI generations"
            )
            db.add(default_proj)
            db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
