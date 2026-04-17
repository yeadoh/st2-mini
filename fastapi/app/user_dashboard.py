import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# database.py에서 DB 연결과 모델 가져오기
from database import get_db, User, Post

router = APIRouter()
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# ==========================================
# 🛡️ 문지기 함수: 토큰 검증
# ==========================================
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었거나 변조되었습니다.")

# ==========================================
# 📦 데이터 검증 모델
# ==========================================
class PostUpdateRequest(BaseModel):
    title: str
    content: str

# ==========================================
# 🚀 API: 1. 유저 정보 조회 (대시보드 상단용)
# ==========================================
@router.get("/info")
async def get_dashboard_info(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    # 내 정보 가져오기
    user = db.query(User).filter(User.user_id == user_id).first()
    # 내가 쓴 글 갯수 가져오기
    post_count = db.query(Post).filter(Post.user_id == user_id).count()
    
    return {
        "user_id": user.user_id,
        "nickname": user.user_nickname,
        "post_count": post_count,
        "role": current_user["role"]
    }

# ==========================================
# 🚀 API: 2. 게시글 목록 조회 (JOIN, 검색, 페이징, 권한 분기)
# ==========================================
@router.get("/posts")
async def get_dashboard_posts(
    title: str = None, 
    page: int = 1, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    role = current_user["role"]
    limit = 25
    offset = (page - 1) * limit

    # 💡 핵심: Post와 User를 JOIN하여 최신 닉네임을 가져옵니다.
    query = db.query(Post, User.user_nickname).outerjoin(User, Post.user_id == User.user_id)

    # USER 등급이면 자기 글만 필터링 (MANAGER는 이 필터를 타지 않아 전체가 보임)
    if role != "MANAGER":
        query = query.filter(Post.user_id == user_id)
        
    # 검색어가 있으면 제목 필터링
    if title:
        query = query.filter(Post.post_title.ilike(f"%{title}%"))

    # 최신순 정렬 및 페이징
    results = query.order_by(Post.post_date.desc()).offset(offset).limit(limit).all()

    post_list = []
    for post, nickname in results:
        post_list.append({
            "post_id": post.post_id,
            "title": post.post_title,
            "content": post.post_content,
            # 💡 2. 닉네임이 NULL인 경우에 대한 처리 (예: '탈퇴한 사용자' 또는 '익명')
            "nickname": nickname if nickname else "알 수 없음", 
            "view_count": post.post_view_count,
            "date": post.post_date.strftime("%Y-%m-%d %H:%M:%S")
        })

    return post_list

# ==========================================
# 🚀 API: 3. 게시글 수정
# ==========================================
@router.put("/posts/{post_id}")
async def update_post(
    post_id: int, 
    request: PostUpdateRequest, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    # 권한 이중 체크: 내 글이거나 내가 매니저일 때만 통과!
    if post.user_id != current_user["user_id"] and current_user["role"] != "MANAGER":
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")

    post.post_title = request.title
    post.post_content = request.content
    db.commit()
    return {"message": "수정 완료"}

# ==========================================
# 🚀 API: 4. 게시글 삭제
# ==========================================
@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    # 권한 이중 체크
    if post.user_id != current_user["user_id"] and current_user["role"] != "MANAGER":
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")

    db.delete(post)
    db.commit()
    return {"message": "삭제 완료"}