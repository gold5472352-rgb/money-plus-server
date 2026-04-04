from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "users.db"

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

def create_user(username, password, expire_date):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?, ?)",
        (username, password, expire_date)
    )
    conn.commit()
    conn.close()

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

if __name__ == "__main__":
    init_db()

    # 🔥 여기서 계정 추가하면 됨
    create_user("test", "1234", "2026-12-31")
    create_user("user1", "1111", "2026-04-05")
    create_user("user2", "2222", "2026-06-01")
    create_user("vip", "9999", "2027-01-01")

    app.run(host="0.0.0.0", port=5000)