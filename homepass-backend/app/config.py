from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    # 데이터베이스 설정 (AWS RDS MySQL)
    # 형식: mysql+pymysql://username:password@host:port/database
    # 예시: mysql+pymysql://admin:password@homepass-db.xxxxx.ap-northeast-2.rds.amazonaws.com:3306/homepass
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/homepass"

    # JWT 설정
    JWT_SECRET_KEY: str = "change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # CORS 설정
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # 네이버 클라우드 플랫폼 (주변 시설 검색용)
    NAVER_CLIENT_ID: str = ""
    NAVER_CLIENT_SECRET: str = ""
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    
    # Cookie / Session
    COOKIE_SECURE: bool = False  # HTTPS 환경이면 True
    COOKIE_DOMAIN: str | None = None  # 필요 시 설정 (예: ".example.com")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """설정 객체를 싱글톤으로 반환"""
    return Settings()

# 전역 설정 객체
settings = get_settings()

