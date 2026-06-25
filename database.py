import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "erp_database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 사용자 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        department TEXT NOT NULL,  -- '영업', '물류운송', '통관', '재무', '관리자'
        rank TEXT NOT NULL,        -- '사원', '대리', '과장', '부장', '대표'
        role TEXT NOT NULL         -- 'user', 'manager', 'admin'
    )
    """)

    # 2. 화물 트래킹 테이블 (FMS Core)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cargo_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_no TEXT UNIQUE NOT NULL,
        bl_no TEXT UNIQUE NOT NULL,
        client_name TEXT NOT NULL,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        vessel_name TEXT NOT NULL,
        status TEXT NOT NULL,       -- '입고완료', '출항', '운송중', '통관중', '인도완료'
        cargo_weight REAL NOT NULL, -- 화물 중량 (tons)
        margin INTEGER NOT NULL,    -- 마진 (KRW)
        revenue INTEGER NOT NULL,   -- 매출 (KRW)
        updated_at TEXT NOT NULL
    )
    """)

    # 3. 소통 게시판 테이블 (부서 권한별)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        department TEXT NOT NULL,  -- 작성자 부서
        is_private INTEGER DEFAULT 0, -- 1이면 해당 부서원만 조회 가능, 0이면 전체 공유
        created_at TEXT NOT NULL
    )
    """)

    # 4. 회의록 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        department TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 초기 데이터 삽입 (데이터가 없을 경우에만)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # 비밀번호는 데모용이므로 평문으로 저장 (실 서비스 적용 시 bcrypt 등 해싱 적용)
        users_data = [
            ("admin", "admin123", "관리자", "대표", "admin"),
            ("sales_kim", "sales123", "영업", "대리", "user"),
            ("ops_lee", "ops123", "물류운송", "과장", "manager"),
            ("customs_park", "customs123", "통관", "사원", "user"),
            ("fin_choi", "fin123", "재무", "부장", "manager")
        ]
        cursor.executemany("INSERT INTO users (username, password, department, rank, role) VALUES (?, ?, ?, ?, ?)", users_data)

    cursor.execute("SELECT COUNT(*) FROM cargo_tracking")
    if cursor.fetchone()[0] == 0:
        cargo_data = [
            ("BK20260601", "BLSHAN0912", "(주)선우무역", "부산(Busan)", "상해(Shanghai)", "SUNGWON PRIDE V.101", "인도완료", 12.5, 450000, 3200000, "2026-06-20 14:00:00"),
            ("BK20260602", "BLLAX55431", "대일실업", "부산(Busan)", "로스앤젤레스(Los Angeles)", "PACIFIC VOYAGER V.05", "운송중", 24.0, 1200000, 8500000, "2026-06-24 09:30:00"),
            ("BK20260603", "BLRTM33211", "한국케미칼", "인천(Incheon)", "로테르담(Rotterdam)", "EUROPE EXPLORER V.12", "출항", 18.2, 980000, 6700000, "2026-06-25 11:00:00"),
            ("BK20260604", "BLTYO88761", "(주)정밀테크", "인천(Incheon)", "도쿄(Tokyo)", "EAST SHUTTLE V.42", "통관중", 5.4, 250000, 1800000, "2026-06-25 16:30:00"),
            ("BK20260605", "BLSIN00982", "성원에스엠", "부산(Busan)", "싱가포르(Singapore)", "OCEAN CLIPPER V.03", "입고완료", 8.8, 380000, 2900000, "2026-06-25 17:00:00")
        ]
        cursor.executemany("""
        INSERT INTO cargo_tracking 
        (booking_no, bl_no, client_name, origin, destination, vessel_name, status, cargo_weight, margin, revenue, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, cargo_data)

    cursor.execute("SELECT COUNT(*) FROM posts")
    if cursor.fetchone()[0] == 0:
        posts_data = [
            ("2026년 하반기 물류 단가 가이드라인 공지", "선사 물동량 협의에 따라 영업본부에서 확정한 단가 가이드를 공지합니다.", "admin", "관리자", 0, "2026-06-24 10:00:00"),
            ("영업본부 내부 거래처 등급 조정안 (비공개)", "각 영업 담당자는 담당 화주사의 여신 등급 조정안을 참고하여 거래선 관리에 만전을 기해주시기 바랍니다.", "sales_kim", "영업", 1, "2026-06-24 15:30:00"),
            ("컨테이너 수급 불균형에 따른 운영 지침", "현재 북미 노선 컨테이너 장비 부족으로 대기시간이 늘어나고 있으니 화주사 사전 안내 바랍니다.", "ops_lee", "물류운송", 0, "2026-06-25 09:15:00")
        ]
        cursor.executemany("INSERT INTO posts (title, content, author, department, is_private, created_at) VALUES (?, ?, ?, ?, ?, ?)", posts_data)

    cursor.execute("SELECT COUNT(*) FROM meetings")
    if cursor.fetchone()[0] == 0:
        meetings_data = [
            ("하반기 물동량 증대 전략 회의", "주요 화주사인 대일실업의 북미 수출 신규 오더 수주 대응 방안에 대해 회의함. 선사 스페이스 추가 확보 필요.", "sales_kim", "영업", "2026-06-24 11:30:00"),
            ("선박 체선 대응 및 대체 항로 모색", "로테르담 항구 정체로 인한 납기 지연 방지를 위해 철도 연계 운송(TSR) 옵션 제공 가능 여부 검토.", "ops_lee", "물류운송", "2026-06-25 10:00:00")
        ]
        cursor.executemany("INSERT INTO meetings (title, content, author, department, created_at) VALUES (?, ?, ?, ?, ?)", meetings_data)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# 화물 관련 함수들
def get_cargo_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cargo_tracking ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_cargo(booking_no, bl_no, client_name, origin, destination, vessel_name, status, cargo_weight, margin, revenue):
    conn = get_db_connection()
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
        INSERT INTO cargo_tracking 
        (booking_no, bl_no, client_name, origin, destination, vessel_name, status, cargo_weight, margin, revenue, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (booking_no, bl_no, client_name, origin, destination, vessel_name, status, cargo_weight, margin, revenue, updated_at))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def update_cargo_status(cargo_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE cargo_tracking SET status = ?, updated_at = ? WHERE id = ?", (status, updated_at, cargo_id))
    conn.commit()
    conn.close()

def delete_cargo(cargo_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cargo_tracking WHERE id = ?", (cargo_id,))
    conn.commit()
    conn.close()

# 게시판/소통 관련 함수들
def get_posts(viewer_dept):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 1. 본인 부서 글이거나 2. 공개(is_private=0) 글이거나 3. 뷰어가 관리자인 경우 전체 노출
    if viewer_dept == "관리자":
        cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    else:
        cursor.execute("""
        SELECT * FROM posts 
        WHERE is_private = 0 OR department = ? 
        ORDER BY created_at DESC
        """, (viewer_dept,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_post(title, content, author, department, is_private):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO posts (title, content, author, department, is_private, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (title, content, author, department, is_private, created_at))
    conn.commit()
    conn.close()

# 회의록 관련 함수들
def get_meetings(viewer_dept):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 회의록은 동일 부서 또는 관리자만 조회 가능하도록 권한 분리
    if viewer_dept == "관리자":
        cursor.execute("SELECT * FROM meetings ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM meetings WHERE department = ? ORDER BY created_at DESC", (viewer_dept,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_meeting(title, content, author, department):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO meetings (title, content, author, department, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (title, content, author, department, created_at))
    conn.commit()
    conn.close()

# 직원(사용자) 관리 관련 함수들
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, department, rank, role FROM users ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_user(username, password, department, rank, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO users (username, password, department, rank, role)
        VALUES (?, ?, ?, ?, ?)
        """, (username, password, department, rank, role))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def update_user(user_id, department, rank, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users 
    SET department = ?, rank = ?, role = ?
    WHERE id = ?
    """, (department, rank, role, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# 사용자 검증 함수 (실 서비스 로그인 대용)
def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

if __name__ == "__main__":
    init_db()

