from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 다른 파일에서 만들어둔 라우터들을 가져옵니다.
from admin import router as admin_router
from admin_login import router as login_router
from user_login import router as user_login_router
from user_dashboard import router as user_dashboard_router

app = FastAPI(title="Management API")

# CORS 설정 (로컬의 HTML 파일이나 Nginx에서 찔러도 에러가 안 나게 해줍니다)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 지금은 개발용이라 모두 열어둠. 나중엔 프론트 도메인만 넣으세요!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 가져온 라우터들을 /api/admin 이라는 공통 주소 아래에 붙입니다.
app.include_router(admin_router, prefix="/api/admin", tags=["관리자 - 회원 관리(admin.html)"])
app.include_router(login_router, prefix="/api/admin", tags=["관리자 - 인증 및 로그인(admin-login)"])
# 일반 유저 라우팅
app.include_router(user_dashboard_router, prefix="/api/user/dashboard", tags=["사용자 - 대시보드 및 게시글 관리"])
app.include_router(user_login_router, prefix="/api/user", tags=["사용자 - 인증 및 로그인"])