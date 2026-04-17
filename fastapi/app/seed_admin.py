from database import SessionLocal, Admin
# bcrypt를 직접 사용하도록 변경 (passlib 라이브러리 버그 회피)
import bcrypt

def get_password_hash(password: str):
    # 비밀번호를 바이트로 변환 후 솔트 생성 및 해싱
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def create_initial_admin():
    db = SessionLocal()
    try:
        # 이메일 중복 확인
        existing_admin = db.query(Admin).filter(Admin.admin_email == "ye@gmail.com").first()
        if existing_admin:
            print("💡 이미 관리자 계정이 존재합니다.")
            return

        # 관리자 객체 생성
        admin_user = Admin(
            admin_email="ye@gmail.com",
            admin_passwd=get_password_hash("11"),  # 직접 만든 해싱 함수 사용
            admin_name="최고관리자"
        )
        
        db.add(admin_user)
        db.commit()
        print("✅ Admin 테이블에 관리자 계정이 성공적으로 생성되었습니다!")
        print("아이디: ye@gmail.com / 비밀번호: 11")
        
    except Exception as e:
        print(f"❌ 생성 중 에러 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_admin()