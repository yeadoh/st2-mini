import os
from sqlalchemy import create_engine, Column, Integer, String, Date, Enum, ForeignKey, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

# ==========================================
# 1. DB 환경 변수 로드 (K8s Secret 또는 로컬 환경변수)
# ==========================================
# os.getenv()를 사용하면 EKS의 K8s Secret을 통해 주입된 값을 자동으로 읽어옵니다.
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD") # 로컬 테스트용 기본값
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

# pymysql 드라이버를 사용한 MariaDB/MySQL 연결 주소
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ==========================================
# 2. 엔진 및 세션 (자체 Connection Pool 사용)
# ==========================================
# pool_size: 평소에 유지할 커넥션 수 / max_overflow: 트래픽 스파이크 시 추가로 허용할 커넥션 수
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_size=5, 
    max_overflow=10,
    pool_recycle=3600 # 1시간마다 커넥션 갱신 (DB 끊김 방지)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# FastAPI 엔드포인트에서 주사기처럼 꽂아서 쓸 DB 세션 제너레이터
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 3. SQLAlchemy 모델 (Models) 정의
# ==========================================

# 1. 유저 데이터 읽어오는 get요청 
class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_nickname = Column(String(50), unique=True, nullable=False)
    user_email = Column(String(100), unique=True, nullable=False)
    user_name = Column(String(50), nullable=False)
    user_passwd = Column(String(255), nullable=False)
    user_birth = Column(Date, nullable=True)
    user_gender = Column(Enum('M', 'F', 'OTHER'), nullable=False)
    user_phone = Column(String(20), nullable=False)
    user_status = Column(Enum('ACTIVE', 'DELETING', 'OUT'), default='ACTIVE', nullable=False)
    user_level = Column(Enum('USER', 'MANAGER'), default='USER', nullable=False)

    # 역참조: 이 유저가 작성한 게시글들
    posts = relationship("Post", back_populates="author")

# 2. 유저 데이터 수정하기위한 post요청
class Post(Base):
    __tablename__ = "post"

    post_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id", ondelete="SET NULL"), nullable=True)
    post_title = Column(String(200), nullable=False)
    post_content = Column(Text, nullable=False)
    post_view_count = Column(Integer, default=0, nullable=False)
    post_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    post_status = Column(Enum('Y', 'N'), default='N', nullable=False)

    # 참조: 이 게시글의 작성자
    author = relationship("User", back_populates="posts")

# 3. Admin 테이블 로그인정보 가져오기
class Admin(Base):
    __tablename__ = "admin"

    admin_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    admin_email = Column(String(100), unique=True, nullable=False)
    admin_passwd = Column(String(255), nullable=False)
    admin_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)