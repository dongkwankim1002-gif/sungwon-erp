import sqlite3
import os
from datetime import datetime
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "erp_database.db")

# ----------------- 하이브리드 DB 분기 판별 -----------------
def is_sheets_configured():
    return "gcp_service_account" in st.secrets and "GSHEET_ID" in st.secrets

# ----------------- 구글 스프레드시트 헬퍼 함수 -----------------
def get_sheets_client():
    creds_dict = st.secrets["gcp_service_account"]
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client

def get_spreadsheet():
    client = get_sheets_client()
    sheet_id = st.secrets["GSHEET_ID"]
    return client.open_by_key(sheet_id)

def get_worksheet_records(worksheet_name):
    sh = get_spreadsheet()
    wks = sh.worksheet(worksheet_name)
    return wks.get_all_records()

def append_worksheet_row(worksheet_name, row_dict):
    sh = get_spreadsheet()
    wks = sh.worksheet(worksheet_name)
    headers = wks.row_values(1)
    # 헤더 순서대로 딕셔너리 값 배열 매핑
    row_values = [row_dict.get(h, "") for h in headers]
    wks.append_row(row_values)

def update_worksheet_cell(worksheet_name, match_col, match_val, update_col, new_val):
    sh = get_spreadsheet()
    wks = sh.worksheet(worksheet_name)
    headers = wks.row_values(1)
    match_col_idx = headers.index(match_col) + 1
    update_col_idx = headers.index(update_col) + 1
    
    cells = wks.findall(str(match_val), in_column=match_col_idx)
    for cell in cells:
        wks.update_cell(cell.row, update_col_idx, new_val)

def update_worksheet_row_multi(worksheet_name, match_col, match_val, update_dict):
    sh = get_spreadsheet()
    wks = sh.worksheet(worksheet_name)
    headers = wks.row_values(1)
    match_col_idx = headers.index(match_col) + 1
    
    cells = wks.findall(str(match_val), in_column=match_col_idx)
    for cell in cells:
        for col_name, new_val in update_dict.items():
            col_idx = headers.index(col_name) + 1
            wks.update_cell(cell.row, col_idx, new_val)

def delete_worksheet_row(worksheet_name, match_col, match_val):
    sh = get_spreadsheet()
    wks = sh.worksheet(worksheet_name)
    headers = wks.row_values(1)
    match_col_idx = headers.index(match_col) + 1
    
    cells = wks.findall(str(match_val), in_column=match_col_idx)
    # 인덱스 꼬임 방지를 위해 아래에서부터 위로 삭제
    for cell in sorted(cells, key=lambda c: c.row, reverse=True):
        wks.delete_rows(cell.row)

# ----------------- SQLite3 로컬 DB 헬퍼 함수 -----------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------- 공통 DB 초기화 (SQLite / Google Sheets) -----------------
def init_db():
    if is_sheets_configured():
        # --- 구글 스프레드시트 초기화 ---
        sh = get_spreadsheet()
        
        # 1. users 시트 검증 및 생성
        try:
            wks_users = sh.worksheet("users")
        except gspread.WorksheetNotFound:
            wks_users = sh.add_worksheet("users", 100, 10)
            wks_users.append_row(["id", "username", "password", "department", "rank", "role"])
            
        if len(wks_users.get_all_values()) <= 1:
            # 초기 데모 계정 데이터 주입
            users_data = [
                ["1", "admin", "admin123", "관리자", "대표", "admin"],
                ["2", "sales_kim", "sales123", "영업", "대리", "user"],
                ["3", "ops_lee", "ops123", "물류운송", "과장", "manager"],
                ["4", "customs_park", "customs123", "통관", "사원", "user"],
                ["5", "fin_choi", "fin123", "재무", "부장", "manager"]
            ]
            wks_users.append_rows(users_data)
            
        # 2. cargo_tracking 시트 검증 및 생성
        try:
            wks_cargo = sh.worksheet("cargo_tracking")
        except gspread.WorksheetNotFound:
            wks_cargo = sh.add_worksheet("cargo_tracking", 100, 15)
            wks_cargo.append_row(["id", "booking_no", "bl_no", "client_name", "origin", "destination", "vessel_name", "status", "cargo_weight", "margin", "revenue", "updated_at"])
            
        if len(wks_cargo.get_all_values()) <= 1:
            cargo_data = [
                ["1", "BK20260601", "BLSHAN0912", "(주)선우무역", "부산(Busan)", "상해(Shanghai)", "SUNGWON PRIDE V.101", "인도완료", "12.5", "450000", "3200000", "2026-06-20 14:00:00"],
                ["2", "BK20260602", "BLLAX55431", "대일실업", "부산(Busan)", "로스앤젤레스(Los Angeles)", "PACIFIC VOYAGER V.05", "운송중", "24.0", "1200000", "8500000", "2026-06-24 09:30:00"],
                ["3", "BK20260603", "BLRTM33211", "한국케미칼", "인천(Incheon)", "로테르담(Rotterdam)", "EUROPE EXPLORER V.12", "출항", "18.2", "980000", "6700000", "2026-06-25 11:00:00"],
                ["4", "BK20260604", "BLTYO88761", "(주)정밀테크", "인천(Incheon)", "도쿄(Tokyo)", "EAST SHUTTLE V.42", "통관중", "5.4", "250000", "1800000", "2026-06-25 16:30:00"],
                ["5", "BK20260605", "BLSIN00982", "성원에스엠", "부산(Busan)", "싱가포르(Singapore)", "OCEAN CLIPPER V.03", "입고완료", "8.8", "380000", "2900000", "2026-06-25 17:00:00"]
            ]
            wks_cargo.append_rows(cargo_data)
            
        # 3. posts 시트 검증 및 생성
        try:
            wks_posts = sh.worksheet("posts")
        except gspread.WorksheetNotFound:
            wks_posts = sh.add_worksheet("posts", 100, 10)
            wks_posts.append_row(["id", "title", "content", "author", "department", "is_private", "created_at"])
            
        if len(wks_posts.get_all_values()) <= 1:
            posts_data = [
                ["1", "2026년 하반기 물류 단가 가이드라인 공지", "선사 물동량 협의에 따라 영업본부에서 확정한 단가 가이드를 공지합니다.", "admin", "관리자", "0", "2026-06-24 10:00:00"],
                ["2", "영업본부 내부 거래처 등급 조정안 (비공개)", "각 영업 담당자는 담당 화주사의 여신 등급 조정안을 참고하여 거래선 관리에 만전을 기해주시기 바랍니다.", "sales_kim", "영업", "1", "2026-06-24 15:30:00"],
                ["3", "컨테이너 수급 불균형에 따른 운영 지침", "현재 북미 노선 컨테이너 장비 부족으로 대기시간이 늘어나고 있으니 화주사 사전 안내 바랍니다.", "ops_lee", "물류운송", "0", "2026-06-25 09:15:00"]
            ]
            wks_posts.append_rows(posts_data)
            
        # 4. meetings 시트 검증 및 생성
        try:
            wks_meetings = sh.worksheet("meetings")
        except gspread.WorksheetNotFound:
            wks_meetings = sh.add_worksheet("meetings", 100, 10)
            wks_meetings.append_row(["id", "title", "content", "author", "department", "created_at"])
            
        if len(wks_meetings.get_all_values()) <= 1:
            meetings_data = [
                ["1", "하반기 물동량 증대 전략 회의", "주요 화주사인 대일실업의 북미 수출 신규 오더 수주 대응 방안에 대해 회의함. 선사 스페이스 추가 확보 필요.", "sales_kim", "영업", "2026-06-24 11:30:00"],
                ["2", "선박 체선 대응 및 대체 항로 모색", "로테르담 항구 정체로 인한 납기 지연 방지를 위해 철도 연계 운송(TSR) 옵션 제공 가능 여부 검토.", "ops_lee", "물류운송", "2026-06-25 10:00:00"]
            ]
            wks_meetings.append_rows(meetings_data)
            
        print("Google Sheets Cloud Database Initialized successfully.")
    else:
        # --- SQLite 로컬 DB 초기화 ---
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            department TEXT NOT NULL,
            rank TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cargo_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_no TEXT UNIQUE NOT NULL,
            bl_no TEXT UNIQUE NOT NULL,
            client_name TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            vessel_name TEXT NOT NULL,
            status TEXT NOT NULL,
            cargo_weight REAL NOT NULL,
            margin INTEGER NOT NULL,
            revenue INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            department TEXT NOT NULL,
            is_private INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """)
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
        
        # 데모용 데이터 삽입 로직
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
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
            cursor.executemany("INSERT INTO cargo_tracking (booking_no, bl_no, client_name, origin, destination, vessel_name, status, cargo_weight, margin, revenue, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", cargo_data)
            
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
        print("Local SQLite Database Initialized successfully.")

# ----------------- 화물(Cargo) 관련 함수 -----------------
def get_cargo_list():
    if is_sheets_configured():
        records = get_worksheet_records("cargo_tracking")
        for r in records:
            r["cargo_weight"] = float(r.get("cargo_weight", 0))
            r["margin"] = int(r.get("margin", 0))
            r["revenue"] = int(r.get("revenue", 0))
        return sorted(records, key=lambda x: str(x.get("updated_at", "")), reverse=True)
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cargo_tracking ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

def add_cargo(booking_no, bl_no, client_name, origin, destination, vessel_name, status, cargo_weight, margin, revenue):
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if is_sheets_configured():
        records = get_worksheet_records("cargo_tracking")
        # 중복 방지
        if any(r["booking_no"] == booking_no or r["bl_no"] == bl_no for r in records):
            return False
        
        # ID 부여
        new_id = str(max([int(r["id"]) for r in records]) + 1) if records else "1"
        append_worksheet_row("cargo_tracking", {
            "id": new_id,
            "booking_no": booking_no,
            "bl_no": bl_no,
            "client_name": client_name,
            "origin": origin,
            "destination": destination,
            "vessel_name": vessel_name,
            "status": status,
            "cargo_weight": str(cargo_weight),
            "margin": str(margin),
            "revenue": str(revenue),
            "updated_at": updated_at
        })
        return True
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
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
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if is_sheets_configured():
        update_worksheet_row_multi("cargo_tracking", "id", cargo_id, {
            "status": status,
            "updated_at": updated_at
        })
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE cargo_tracking SET status = ?, updated_at = ? WHERE id = ?", (status, updated_at, cargo_id))
        conn.commit()
        conn.close()

def delete_cargo(cargo_id):
    if is_sheets_configured():
        delete_worksheet_row("cargo_tracking", "id", cargo_id)
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cargo_tracking WHERE id = ?", (cargo_id,))
        conn.commit()
        conn.close()

# ----------------- 소통 게시판(Posts) 관련 함수 -----------------
def get_posts(viewer_dept):
    if is_sheets_configured():
        records = get_worksheet_records("posts")
        # 타입 캐스팅
        for r in records:
            r["is_private"] = int(r.get("is_private", 0))
            
        if viewer_dept == "관리자":
            results = records
        else:
            results = [r for r in records if r["is_private"] == 0 or r["department"] == viewer_dept]
        return sorted(results, key=lambda x: str(x.get("created_at", "")), reverse=True)
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
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
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if is_sheets_configured():
        records = get_worksheet_records("posts")
        new_id = str(max([int(r["id"]) for r in records]) + 1) if records else "1"
        append_worksheet_row("posts", {
            "id": new_id,
            "title": title,
            "content": content,
            "author": author,
            "department": department,
            "is_private": str(is_private),
            "created_at": created_at
        })
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO posts (title, content, author, department, is_private, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (title, content, author, department, is_private, created_at))
        conn.commit()
        conn.close()

# ----------------- 회의록(Meetings) 관련 함수 -----------------
def get_meetings(viewer_dept):
    if is_sheets_configured():
        records = get_worksheet_records("meetings")
        if viewer_dept == "관리자":
            results = records
        else:
            results = [r for r in records if r["department"] == viewer_dept]
        return sorted(results, key=lambda x: str(x.get("created_at", "")), reverse=True)
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        if viewer_dept == "관리자":
            cursor.execute("SELECT * FROM meetings ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM meetings WHERE department = ? ORDER BY created_at DESC", (viewer_dept,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

def add_meeting(title, content, author, department):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if is_sheets_configured():
        records = get_worksheet_records("meetings")
        new_id = str(max([int(r["id"]) for r in records]) + 1) if records else "1"
        append_worksheet_row("meetings", {
            "id": new_id,
            "title": title,
            "content": content,
            "author": author,
            "department": department,
            "created_at": created_at
        })
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO meetings (title, content, author, department, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (title, content, author, department, created_at))
        conn.commit()
        conn.close()

# ----------------- 직원(사용자) 관리 관련 함수 -----------------
def get_users():
    if is_sheets_configured():
        records = get_worksheet_records("users")
        # 패스워드 제외하고 반환 (보안)
        users_list = []
        for r in records:
            users_list.append({
                "id": r.get("id"),
                "username": r.get("username"),
                "department": r.get("department"),
                "rank": r.get("rank"),
                "role": r.get("role")
            })
        return sorted(users_list, key=lambda x: int(x.get("id", 0)))
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, department, rank, role FROM users ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

def add_user(username, password, department, rank, role):
    if is_sheets_configured():
        records = get_worksheet_records("users")
        if any(r["username"] == username for r in records):
            return False
        new_id = str(max([int(r["id"]) for r in records]) + 1) if records else "1"
        append_worksheet_row("users", {
            "id": new_id,
            "username": username,
            "password": password,
            "department": department,
            "rank": rank,
            "role": role
        })
        return True
    else:
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
    if is_sheets_configured():
        update_worksheet_row_multi("users", "id", user_id, {
            "department": department,
            "rank": rank,
            "role": role
        })
    else:
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
    if is_sheets_configured():
        delete_worksheet_row("users", "id", user_id)
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

def verify_user(username, password):
    if is_sheets_configured():
        records = get_worksheet_records("users")
        # 데이터 시트에서 매칭 확인
        for r in records:
            if str(r.get("username")) == username and str(r.get("password")) == password:
                return r
        return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

if __name__ == "__main__":
    init_db()
