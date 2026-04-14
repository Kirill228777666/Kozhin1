from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
import re

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="185.114.247.43",
        user="sch688_vvedenie",
        password="Qwerty123",
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            password VARCHAR(255)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def is_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

@app.route("/", methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            error = "Email и пароль обязательны"
            if is_ajax():
                return jsonify(success=False, errors=[error])
            return render_template('login.html', error=error)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            if is_ajax():
                return jsonify(success=True, redirect=url_for('main_page'))
            return redirect(url_for('main_page'))
        else:
            error = "Неверный логин или пароль"
            if is_ajax():
                return jsonify(success=False, errors=[error])
            return render_template('login.html', error=error)
            
    return render_template('login.html', error=None)

@app.route("/registration", methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        errors = []
        
        if not name or len(name) < 2:
            errors.append("Имя должно содержать минимум 2 символа")
        elif not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$', name):
            errors.append("Имя может содержать только буквы, пробелы и дефис")
            
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors.append("Некорректный email")
            
        if len(password) < 8:
            errors.append("Пароль должен содержать минимум 8 символов")
        if not re.search(r'[A-Z]', password):
            errors.append("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r'[a-z]', password):
            errors.append("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r'[0-9]', password):
            errors.append("Пароль должен содержать хотя бы одну цифру")
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$', password):
            errors.append("Пароль может содержать только латинские буквы, цифры и спецсимволы")
        if ' ' in password:
            errors.append("Пароль не должен содержать пробелы")
            
        if errors:
            if is_ajax():
                return jsonify(success=False, errors=errors)
            return render_template('registration.html', errors=errors)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            errors.append("Пользователь с таким email уже существует")
            if is_ajax():
                return jsonify(success=False, errors=errors)
            return render_template('registration.html', errors=errors)
        
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        conn.close()
        
        if is_ajax():
            return jsonify(success=True, redirect=url_for('hello_world'))
        return redirect(url_for('hello_world'))
        
    return render_template('registration.html', errors=[])

@app.route("/password_vosst", methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            error = "Некорректный email"
            if is_ajax():
                return jsonify(success=False, errors=[error])
            return render_template('password_vosst.html', error=error)
        
        success_msg = "Инструкции по восстановлению отправлены на email"
        if is_ajax():
            return jsonify(success=True, message=success_msg)
        return render_template('password_vosst.html', success=success_msg)
        
    return render_template('password_vosst.html')

@app.route("/main")
def main_page():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(debug=True)