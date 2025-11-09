from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from webapp.models import Base

DATABASE_URL = "sqlite:///./price_monitor.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def migrate_sqlite_schema():
    """Lightweight, best-effort migrations for SQLite in dev.

    Adds missing columns introduced recently without dropping data.
    This is NOT a replacement for Alembic, just convenient for local runs.
    """
    with engine.connect() as conn:
        # listings: add workspace_id
        try:
            res = conn.execute(text("PRAGMA table_info(listings)"))
            cols = {row[1] for row in res.fetchall()}
            if "workspace_id" not in cols:
                conn.execute(
                    text("ALTER TABLE listings ADD COLUMN workspace_id INTEGER")
                )
        except Exception:
            pass

        # price_records: add job_id
        try:
            res = conn.execute(text("PRAGMA table_info(price_records)"))
            cols = {row[1] for row in res.fetchall()}
            if "job_id" not in cols:
                conn.execute(
                    text("ALTER TABLE price_records ADD COLUMN job_id INTEGER")
                )
        except Exception:
            pass

        # scrape_jobs: add season_id, params
        try:
            res = conn.execute(text("PRAGMA table_info(scrape_jobs)"))
            cols = {row[1] for row in res.fetchall()}
            if "season_id" not in cols:
                conn.execute(
                    text("ALTER TABLE scrape_jobs ADD COLUMN season_id INTEGER")
                )
            if "params" not in cols:
                # store JSON as TEXT in SQLite
                conn.execute(text("ALTER TABLE scrape_jobs ADD COLUMN params JSON"))
        except Exception:
            pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
