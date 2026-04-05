from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB = "users.db"

# 🔐 관리자 키
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


# 유저 생성
@app.route("/create_user", methods=["POST"])
def api_create_user():
    data = request.json

    if data.get("admin_key") != ADMIN_KEY:
        return jsonify({"status": "fail", "msg": "권한 없음"}), 403

    username = data.get("username")
    password = data.get("password")
    days = data.get("days", 30)

    expire_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    create_user(username, password, expire_date)

    return jsonify({"status": "success", "msg": "계정 생성 완료"})


# 유저 삭제
@app.route("/delete_user", methods=["POST"])
def delete_user():
    data = request.json

    if data.get("admin_key") != ADMIN_KEY:
        return jsonify({"status": "fail", "msg": "권한 없음"}), 403

    username = data.get("username")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "msg": "삭제 완료"})


# 유저 목록
@app.route("/list_users", methods=["POST"])
def list_users():
    data = request.json

    if data.get("admin_key") != ADMIN_KEY:
        return jsonify({"status": "fail", "msg": "권한 없음"}), 403

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT username, expire_date FROM users")
    rows = cur.fetchall()
    conn.close()

    users = [{"username": r[0], "expire_date": r[1]} for r in rows]

    return jsonify({"status": "success", "users": users})


# 🔥 관리자 웹페이지
@app.route("/admin")
def admin_page():
    return f"""
    <html>
    <body>
        <h2>🔥 관리자 패널</h2>

        <h3>유저 생성</h3>
        <input id="u" placeholder="아이디"><br>
        <input id="p" placeholder="비번"><br>
        <input id="d" value="30"><br>
        <button onclick="c()">생성</button>

        <h3>유저 삭제</h3>
        <input id="du" placeholder="아이디"><br>
        <button onclick="del()">삭제</button>

        <h3>목록</h3>
        <button onclick="l()">조회</button>

        <pre id="r"></pre>

        <script>
        const key = "{ADMIN_KEY}"

        function c() {{
            fetch('/create_user', {{
                method:'POST',
                headers:{{'Content-Type':'application/json'}},
                body:JSON.stringify({{
                    username:document.getElementById('u').value,
                    password:document.getElementById('p').value,
                    days:parseInt(document.getElementById('d').value),
                    admin_key:key
                }})
            }}).then(r=>r.json()).then(d=>out(d))
        }}

        function del() {{
            fetch('/delete_user', {{
                method:'POST',
                headers:{{'Content-Type':'application/json'}},
                body:JSON.stringify({{
                    username:document.getElementById('du').value,
                    admin_key:key
                }})
            }}).then(r=>r.json()).then(d=>out(d))
        }}

        function l() {{
            fetch('/list_users', {{
                method:'POST',
                headers:{{'Content-Type':'application/json'}},
                body:JSON.stringify({{admin_key:key}})
            }}).then(r=>r.json()).then(d=>out(d))
        }}

        function out(d) {{
            document.getElementById('r').innerText = JSON.stringify(d,null,2)
        }}
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    init_db()
    create_user("test", "1234", "2026-12-31")
    app.run(host="0.0.0.0", port=5000)
