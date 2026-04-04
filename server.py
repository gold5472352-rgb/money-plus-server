from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB = "users.db"

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

# 유저 생성 함수
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


# 🔥 유저 생성 API (핵심 추가)
@app.route("/create_user", methods=["POST"])
def api_create_user():
    data = request.json

    username = data.get("username")
    password = data.get("password")
    days = data.get("days", 30)

    if not username or not password:
        return jsonify({"status": "fail", "msg": "값 누락"}), 400

    expire_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    create_user(username, password, expire_date)

    return jsonify({
        "status": "success",
        "msg": f"{username} 계정 생성 완료",
        "expire_date": expire_date
    })


if __name__ == "__main__":
    init_db()

    # 기본 테스트 계정
    create_user("test", "1234", "2026-12-31")

    app.run(host="0.0.0.0", port=5000)
