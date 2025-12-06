"""
Veritabanı Bağlantı Yönetimi
"""

from typing import Optional, Generator
from contextlib import contextmanager
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


class DatabaseConfig:
    """Veritabanı konfigürasyonu"""
    
    def __init__(
        self,
        db_type: str = "sqlite",
        host: str = "localhost",
        port: int = 5432,
        database: str = "animal_tracking",
        username: str = "",
        password: str = "",
        pool_size: int = 5,
        max_overflow: int = 10
    ):
        self.db_type = db_type
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Environment variables'dan konfigürasyon oluştur"""
        return cls(
            db_type=os.getenv("DB_TYPE", "sqlite"),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "animal_tracking"),
            username=os.getenv("DB_USER", ""),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10"))
        )
        
    def get_connection_url(self) -> str:
        """Bağlantı URL'i oluştur"""
        if self.db_type == "sqlite":
            return f"sqlite:///{self.database}.db"
        elif self.db_type == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == "mysql":
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Desteklenmeyen veritabanı türü: {self.db_type}")


class DatabaseConnection:
    """Veritabanı bağlantı yöneticisi"""
    
    _instance: Optional["DatabaseConnection"] = None
    
    def __new__(cls, config: DatabaseConfig = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self, config: DatabaseConfig = None):
        if self._initialized:
            return
            
        if config is None:
            config = DatabaseConfig.from_env()
            
        self.config = config
        self._engine = None
        self._session_factory = None
        self._initialized = True
        
    def get_engine(self):
        """SQLAlchemy engine döndür"""
        if self._engine is None:
            connection_url = self.config.get_connection_url()
            
            if self.config.db_type == "sqlite":
                # SQLite için özel ayarlar
                self._engine = create_engine(
                    connection_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=os.getenv("DB_ECHO", "false").lower() == "true"
                )
                
                # Foreign key desteği için
                @event.listens_for(self._engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
            else:
                # PostgreSQL/MySQL için
                self._engine = create_engine(
                    connection_url,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_pre_ping=True,
                    echo=os.getenv("DB_ECHO", "false").lower() == "true"
                )
                
        return self._engine
        
    def get_session_factory(self) -> sessionmaker:
        """Session factory döndür"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.get_engine()
            )
        return self._session_factory
        
    def get_session(self) -> Session:
        """Yeni session oluştur"""
        return self.get_session_factory()()
        
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Context manager ile session yönetimi"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            
    def create_tables(self, base):
        """Tüm tabloları oluştur"""
        base.metadata.create_all(bind=self.get_engine())
        
    def drop_tables(self, base):
        """Tüm tabloları sil"""
        base.metadata.drop_all(bind=self.get_engine())
        
    def close(self):
        """Bağlantıyı kapat"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            
    @classmethod
    def reset_instance(cls):
        """Singleton instance'ı sıfırla (test için)"""
        if cls._instance:
            cls._instance.close()
        cls._instance = None


# Global database instance
_db: Optional[DatabaseConnection] = None


def get_db() -> DatabaseConnection:
    """Global database instance döndür"""
    global _db
    if _db is None:
        _db = DatabaseConnection()
    return _db


def get_session() -> Session:
    """Session döndür"""
    return get_db().get_session()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Session context manager"""
    with get_db().session_scope() as session:
        yield session


# FastAPI dependency
def get_db_session() -> Generator[Session, None, None]:
    """FastAPI için database session dependency"""
    db = get_db()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
