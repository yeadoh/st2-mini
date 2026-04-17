import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt

security = HTTPBearer()

# database.py에서 DB 세션 연결 함수와 Admin 모델을 가져옵니다.
from database import get_db, Admin

router = APIRouter()

# ==========================================
# ⚙️ JWT 및 암호화 설정
# ==========================================
SECRET_KEY = os.getenv("SECRET_KEY", "my-super-secret-key-change-this-later")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 토큰 유효기간 (8시간)

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """토큰을 해독하여 유효한 관리자인지 검증하는 문지기 함수"""
    token = credentials.credentials
    try:
        # 토큰 해독
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        
        # 관리자(SYS_ADMIN) 역할이 맞는지 확인
        if email is None or role != "SYS_ADMIN":
            raise HTTPException(status_code=401, detail="권한이 없습니다.")
            
        return email # 검증 완료 시 이메일 반환
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

# ==========================================
# 📦 데이터 검증 모델 (Pydantic)
# ==========================================
class LoginRequest(BaseModel):
    email: str
    password: str

# ==========================================
# 🛠️ 보조 함수: 비밀번호 검증 및 토큰 생성 (수정된 핵심 부분 ⭐)
# ==========================================
def verify_password(plain_password: str, hashed_password: str):
    """사용자가 입력한 비번과 DB의 해시된 비번이 일치하는지 확인"""
    try:
        # DB에서 가져온 해시가 문자열이라면 바이트로 변환
        hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        plain_bytes = plain_password.encode('utf-8')
        
        # bcrypt 직접 사용
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as e:
        print(f"Bcrypt verification error: {e}")
        return False

def get_password_hash(password: str):
    """비밀번호를 Bcrypt로 암호화"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None):
    """JWT 토큰을 생성하는 함수"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ==========================================
# 🚀 로그인 API 엔드포인트
# ==========================================
@router.post("/login")
async def admin_login(request: LoginRequest, db: Session = Depends(get_db)):
    # 1. 'Admin' 테이블에서 조회
    admin = db.query(Admin).filter(Admin.admin_email == request.email).first()
    
    # 2. 계정이 없거나 비밀번호가 틀리면 에러
    if not admin:
        raise HTTPException(status_code=401, detail="존재하지 않는 관리자 계정입니다.")
        
    if not verify_password(request.password, admin.admin_passwd):
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
        
    # 3. 토큰 발급 (권한을 시스템 최고 관리자로 명시)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.admin_email, "role": "SYS_ADMIN"},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}