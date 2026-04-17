from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

# 우리가 만든 파일들에서 필요한 것들을 가져옵니다.
from database import get_db, User
from admin_login import get_current_admin

router = APIRouter()

# ==========================================
# 📦 데이터 검증 모델 (Pydantic)
# ==========================================
class UserUpdateRequest(BaseModel):
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    user_phone: Optional[str] = None
    user_status: Optional[str] = None
    user_level: Optional[str] = None

# ==========================================
# 🚀 API 엔드포인트 (실제 DB 연동)
# ==========================================

# 1. 회원 리스트 조회 및 검색 (GET /api/admin/user)
@router.get("/user")
async def get_user_list(
    page: int = 1,
    limit: int = 25,
    search_type: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin) # 👈 문지기 통과해야함
):
    query = db.query(User)

    # 검색 조건이 있을 경우 필터링
    if keyword:
        if search_type == "user_email":
            query = query.filter(User.user_email.like(f"%{keyword}%"))
        elif search_type == "user_name":
            query = query.filter(User.user_name.like(f"%{keyword}%"))
        elif search_type == "user_nickname":
            query = query.filter(User.user_nickname.like(f"%{keyword}%"))

    total_users = query.count()
    total_pages = (total_users + limit - 1) // limit
    
    # 페이징 처리 (최신순 정렬)
    items = query.order_by(User.user_id.desc())\
                 .offset((page - 1) * limit)\
                 .limit(limit)\
                 .all()

    return {
        "total_users": total_users,
        "total_pages": total_pages,
        "items": items
    }

# 2. 특정 회원 상세 조회 (GET /api/admin/user/{user_id})
@router.get("/user/{user_id}")
async def get_user_detail(
    user_id: int, 
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin) # 👈 문지기
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="해당 유저를 찾을 수 없습니다.")
    
    # 여기서 post_count 등 추가 정보를 합쳐서 보내줄 수도 있습니다.
    return user

# 3. 특정 회원 정보 수정 (PATCH /api/admin/user/{user_id})
@router.patch("/user/{user_id}")
async def update_user(
    user_id: int, 
    update_data: UserUpdateRequest, 
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin) # 👈 문지기
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    # 넘어온 데이터 중 값이 있는 것만 업데이트
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return {"message": f"{user_id}번 유저 정보가 수정되었습니다.", "user": user}