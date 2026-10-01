from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import func, select, Integer, String, create_engine, Boolean, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, sessionmaker
from flask_login import UserMixin
from datetime import datetime
from typing import List 
from flask_login import UserMixin
import os


engine = create_engine(os.getenv("DATABASE_URL", "DATABASE_KEY"), echo=False)

PG_USER = "postgres"
PG_PASSWORD = "Tesla31!"
PG_DBNAME = "posts"
PG_SCHEMA = "python_posts"


engine = create_engine(
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@localhost:5432/{PG_DBNAME}",
    connect_args={"options": f"-csearch_path={PG_SCHEMA}"},
    echo=False,
)

with engine.begin() as connection:
    connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{PG_SCHEMA}"'))

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

class User(UserMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    registerdate: Mapped[datetime] = mapped_column(server_default=func.now())
    registered_at: Mapped[datetime] = mapped_column(server_default=func.now())

    posts: Mapped[List["Post"]] = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    date: Mapped[datetime] = mapped_column(server_default=func.now())
    registered_at: Mapped[datetime] = mapped_column(server_default=func.now())

    author: Mapped["User"] = relationship("User", back_populates="posts")

Base.metadata.create_all(bind=engine)


