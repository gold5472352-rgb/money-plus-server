from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB = "users.db"

# 🔐 관리자 키 (원하는 값으로 바꿔라)
ADMIN_KEY = "1234"


# DB 초기화
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            expire_date TEXT
        )
    """)
    conn.commit()
    conn.close()


# 유저 생성
def create_user(username, password, expire_date):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?, ?)",
        (username, password, expire_date)
    )
    conn.commit()
    conn.close()


# 로그인 API
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT password, expire_date FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"status": "fail", "msg": "아이디 없음"})

    db_pw, expire = row

    if password != db_pw:
        return jsonify({"status": "fail", "msg": "비밀번호 틀림"})

    if datetime.now() > datetime.fromisoformat(expire):
        return jsonify({"status": "expired", "msg": "기간 만료"})

    return jsonify({"status": "success", "msg": "로그인 성공"})


# ✅ 유저 생성 API
@app.route("/create_user", methods=["POST"])
def api_create_user():
    data = request.json

    username = data.get("username")
    password = data.get("password")
    days = data.get("days", 30)
    admin_key = data.get("admin_key")

    if admin_key != ADMIN_KEY:
        return jsonify({"status": "fail", "msg": "권한 없음"}), 403

    if not username or not password:
        return jsonify({"status": "fail", "msg": "값 누락"}), 400

    expire_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    create_user(username, password, expire_date)

    return jsonify({
        "status": "success",
        "msg": f"{username} 계정 생성 완료",
        "expire_date": expire_date
    })


# ✅ 유저 삭제 API
@app.route("/delete_user", methods=["POST"])
def delete_user():
    data = request.json

    username = data.get("username")
    admin_key = data.get("admin_key")

    if admin_key != ADMIN_KEY:
        return jsonify({"status": "fail", "msg": "권한 없음"}), 403

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "msg": f"{username} 삭제 완료"})


# ✅ 유저 목록 조회 (관리자용)
@app.route("/list_users", methods=["POST"])
def list_users():
    data = request.json
    admin_key = data.get("admin_key")

    if admin_key != ADMIN_KEY:
        return jsonify({"status": "fail", "msg": "권한 없음"}), 403

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT username, expire_date FROM users")
    rows = cur.fetchall()
    conn.close()

    users = []
    for r in rows:
        users.append({
            "username": r[0],
            "expire_date": r[1]
        })

    return jsonify({"status": "success", "users": users})


if __name__ == "__main__":
    init_db()

    # 기본 계정
    create_user("test", "1234", "2026-12-31")

    app.run(host="0.0.0.0", port=5000)
