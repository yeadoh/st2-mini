import os
import bcrypt
from datetime import datetime, timedelta, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import jwt

# database.py에서 DB 세션 연결 함수와 User 모델을 가져옵니다.
from database import get_db, User

router = APIRouter()

# ==========================================
# ⚙️ JWT 및 암호화 설정
# ==========================================
SECRET_KEY = os.getenv("SECRET_KEY", "my-super-secret-key-change-this-later")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 일반 유저는 8시간 유지

# ==========================================
# 📦 데이터 검증 모델 (Pydantic)
# ==========================================
class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserSignupRequest(BaseModel):
    user_email: str
    user_passwd: str
    user_name: str
    user_nickname: str
    user_phone: str
    user_gender: str  # 'M', 'F', 'OTHER'
    user_birth: Optional[date] = None

# ==========================================
# 🛠️ 보조 함수: 비밀번호 검증 및 암호화, 토큰 생성
# ==========================================
def verify_password(plain_password: str, hashed_password: str):
    try:
        hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        plain_bytes = plain_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as e:
        print(f"Bcrypt verification error: {e}")
        return False

# 💡 누락되었던 비밀번호 암호화 함수 추가!
def get_password_hash(password: str):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ==========================================
# 🚀 API 엔드포인트: 로그인
# ==========================================
@router.post("/login")
async def user_login(request: UserLoginRequest, db: Session = Depends(get_db)):
    # 1. DB에서 이메일로 유저 찾기
    user = db.query(User).filter(User.user_email == request.email).first()
    
    # 2. 계정 유무 및 비밀번호 검증
    if not user or not verify_password(request.password, user.user_passwd):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 일치하지 않습니다.")
    
    # 3. 상태 검증 (탈퇴한 회원 차단)
    if user.user_status != 'ACTIVE':
        raise HTTPException(status_code=403, detail="탈퇴하거나 정지된 계정입니다.")
        
    # 4. 토큰 발급 (친구를 위해 user_id와 user_level을 담아줍니다)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.user_email,       # 이메일
            "user_id": user.user_id,      # 친구가 본인 글인지 확인할 때 쓸 ID
            "role": user.user_level       # 친구가 매니저인지 확인할 때 쓸 등급 ('USER' or 'MANAGER')
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# ==========================================
# 🚀 API 엔드포인트: 회원가입
# ==========================================
@router.post("/signup")
async def user_signup(request: UserSignupRequest, db: Session = Depends(get_db)):
    # 1. 이메일 또는 닉네임 중복 확인
    existing_user = db.query(User).filter(
        (User.user_email == request.user_email) | 
        (User.user_nickname == request.user_nickname)
    ).first()
    
    if existing_user:
        if existing_user.user_email == request.user_email:
            raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")

    # 2. 비밀번호 암호화 (Bcrypt)
    hashed_password = get_password_hash(request.user_passwd)

    # 3. DB 객체 생성 및 저장
    new_user = User(
        user_email=request.user_email,
        user_passwd=hashed_password,
        user_name=request.user_name,
        user_nickname=request.user_nickname,
        user_phone=request.user_phone,
        user_gender=request.user_gender,
        user_birth=request.user_birth
    )
    
    db.add(new_user)
    db.commit()
    
    return {"message": "회원가입이 성공적으로 완료되었습니다."}