import os
import sqlite3
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "setna-secret-key-change-me")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

# ---------------------------------------------------------------------------
# قاعدة البيانات
# ---------------------------------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# التصميم (CSS) مدمج داخل نفس الملف
# ---------------------------------------------------------------------------

STYLE = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "Segoe UI", Tahoma, Arial, sans-serif;
    background: linear-gradient(135deg, #0f766e 0%, #134e4a 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .card {
    background: #ffffff;
    width: 100%;
    max-width: 400px;
    border-radius: 16px;
    padding: 32px 28px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  }
  .logo { text-align: center; margin-bottom: 24px; }
  .logo h1 { color: #0f766e; font-size: 26px; font-weight: 700; }
  .logo p { color: #6b7280; font-size: 13px; margin-top: 4px; }
  .form-group { margin-bottom: 16px; }
  label { display: block; margin-bottom: 6px; font-size: 14px; color: #374151; font-weight: 600; }
  input {
    width: 100%; padding: 12px 14px; border: 1px solid #d1d5db;
    border-radius: 8px; font-size: 14px; transition: border-color 0.2s;
  }
  input:focus { outline: none; border-color: #0f766e; }
  button {
    width: 100%; padding: 12px; background: #0f766e; color: #fff;
    border: none; border-radius: 8px; font-size: 15px; font-weight: 700;
    cursor: pointer; margin-top: 8px; transition: background 0.2s;
  }
  button:hover { background: #0d5f58; }
  .switch-link { text-align: center; margin-top: 18px; font-size: 13px; color: #6b7280; }
  .switch-link a { color: #0f766e; font-weight: 700; text-decoration: none; }
  .switch-link a:hover { text-decoration: underline; }
  .flash { padding: 10px 14px; border-radius: 8px; margin-bottom: 16px; font-size: 13px; text-align: center; }
  .flash.success { background: #d1fae5; color: #065f46; }
  .flash.error { background: #fee2e2; color: #991b1b; }
  @media (max-width: 480px) { .card { padding: 24px 18px; } }
</style>
"""

# ---------------------------------------------------------------------------
# صفحات HTML مدمجة داخل نفس الملف
# ---------------------------------------------------------------------------

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>تسجيل الدخول - ستنا للصيانة</title>
  """ + STYLE + """
</head>
<body>
  <div class="card">
    <div class="logo">
      <h1>ستنا للصيانة</h1>
      <p>تسجيل الدخول إلى حسابك</p>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form method="POST" action="{{ url_for('login') }}">
      <div class="form-group">
        <label for="email">البريد الإلكتروني</label>
        <input type="email" id="email" name="email" placeholder="example@email.com" required />
      </div>
      <div class="form-group">
        <label for="password">كلمة المرور</label>
        <input type="password" id="password" name="password" placeholder="••••••••" required />
      </div>
      <button type="submit">تسجيل الدخول</button>
    </form>

    <div class="switch-link">
      ليس لديك حساب؟ <a href="{{ url_for('register') }}">أنشئ حسابًا جديدًا</a>
    </div>
  </div>
</body>
</html>
"""

REGISTER_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>إنشاء حساب - ستنا للصيانة</title>
  """ + STYLE + """
</head>
<body>
  <div class="card">
    <div class="logo">
      <h1>ستنا للصيانة</h1>
      <p>إنشاء حساب جديد</p>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form method="POST" action="{{ url_for('register') }}">
      <div class="form-group">
        <label for="full_name">الاسم الكامل</label>
        <input type="text" id="full_name" name="full_name" placeholder="اكتب اسمك" required />
      </div>
      <div class="form-group">
        <label for="email">البريد الإلكتروني</label>
        <input type="email" id="email" name="email" placeholder="example@email.com" required />
      </div>
      <div class="form-group">
        <label for="password">كلمة المرور</label>
        <input type="password" id="password" name="password" placeholder="••••••••" required />
      </div>
      <div class="form-group">
        <label for="confirm_password">تأكيد كلمة المرور</label>
        <input type="password" id="confirm_password" name="confirm_password" placeholder="••••••••" required />
      </div>
      <button type="submit">إنشاء الحساب</button>
    </form>

    <div class="switch-link">
      لديك حساب بالفعل؟ <a href="{{ url_for('login') }}">تسجيل الدخول</a>
    </div>
  </div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# المسارات (Routes)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            flash("الرجاء تعبئة جميع الحقول", "error")
            return render_template_string(REGISTER_PAGE)

        if password != confirm_password:
            flash("كلمتا المرور غير متطابقتين", "error")
            return render_template_string(REGISTER_PAGE)

        if len(password) < 6:
            flash("يجب أن تكون كلمة المرور 6 أحرف على الأقل", "error")
            return render_template_string(REGISTER_PAGE)

        conn = get_db_connection()
        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()

        if existing_user:
            conn.close()
            flash("هذا البريد الإلكتروني مسجل بالفعل", "error")
            return render_template_string(REGISTER_PAGE)

        password_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
            (full_name, email, password_hash),
        )
        conn.commit()
        conn.close()

        flash("تم إنشاء الحساب بنجاح، الرجاء تسجيل الدخول", "success")
        return redirect(url_for("login"))

    return render_template_string(REGISTER_PAGE)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]
            flash(f"مرحبًا بك، {user['full_name']}!", "success")
            return redirect(url_for("login"))

        flash("البريد الإلكتروني أو كلمة المرور غير صحيحة", "error")
        return render_template_string(LOGIN_PAGE)

    return render_template_string(LOGIN_PAGE)


@app.route("/logout")
def logout():
    session.clear()
    flash("تم تسجيل الخروج بنجاح", "success")
    return redirect(url_for("login"))


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
