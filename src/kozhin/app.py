from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
import re
import traceback

app = Flask(__name__)

def get_db_connection():
    """Возвращает соединение с БД или None при ошибке."""
    try:
        conn = mysql.connector.connect(
            host="185.114.247.43",
            user="sch688_vvedenie",
            port=3306,
            password="Qwerty123",
            database="sch688_vvedenie"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Ошибка подключения к БД: {err}")
        traceback.print_exc()
        return None

def is_json_request():
    return request.is_json or request.headers.get('Accept') == 'application/json'

@app.route("/", methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip()
            password = data.get('password', '')
        else:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')

        if not email or not password:
            error = "Email и пароль обязательны"
            if is_json_request():
                return jsonify(success=False, errors=[error]), 400
            return render_template('login.html', error=error)

        conn = get_db_connection()
        if conn is None:
            error = "Ошибка подключения к базе данных"
            if is_json_request():
                return jsonify(success=False, errors=[error]), 500
            return render_template('login.html', error=error)

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Ошибка запроса: {err}")
            traceback.print_exc()
            error = "Ошибка при работе с базой данных"
            if is_json_request():
                return jsonify(success=False, errors=[error]), 500
            return render_template('login.html', error=error)
        finally:
            conn.close()

        if user:
            if is_json_request():
                return jsonify(success=True, redirect=url_for('main_page'))
            return redirect(url_for('main_page'))
        else:
            error = "Неверный логин или пароль"
            if is_json_request():
                return jsonify(success=False, errors=[error]), 401
            return render_template('login.html', error=error)

    if is_json_request():
        return jsonify(message="Отправьте POST с JSON {email, password}")
    return render_template('login.html', error=None)

@app.route("/registration", methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
        else:
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
            if is_json_request():
                return jsonify(success=False, errors=errors), 400
            return render_template('registration.html', errors=errors)

        conn = get_db_connection()
        if conn is None:
            errors.append("Ошибка подключения к базе данных")
            if is_json_request():
                return jsonify(success=False, errors=errors), 500
            return render_template('registration.html', errors=errors)

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                errors.append("Пользователь с таким email уже существует")
                if is_json_request():
                    return jsonify(success=False, errors=errors), 409
                return render_template('registration.html', errors=errors)

            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                           (name, email, password))
            conn.commit()
        except mysql.connector.Error as err:
            print(f"Ошибка запроса: {err}")
            traceback.print_exc()
            errors.append("Ошибка при работе с базой данных")
            if is_json_request():
                return jsonify(success=False, errors=errors), 500
            return render_template('registration.html', errors=errors)
        finally:
            conn.close()

        if is_json_request():
            return jsonify(success=True, redirect=url_for('hello_world'))
        return redirect(url_for('hello_world'))

    if is_json_request():
        return jsonify(message="Отправьте POST с JSON {name, email, password}")
    return render_template('registration.html', errors=[])

@app.route("/password_vosst", methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip()
        else:
            email = request.form.get('email', '').strip()

        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            error = "Некорректный email"
            if is_json_request():
                return jsonify(success=False, errors=[error]), 400
            return render_template('password_vosst.html', error=error)

        success_msg = "Инструкции по восстановлению отправлены на email"
        if is_json_request():
            return jsonify(success=True, message=success_msg)
        return render_template('password_vosst.html', success=success_msg)

    if is_json_request():
        return jsonify(message="Отправьте POST с JSON {email}")
    return render_template('password_vosst.html')

@app.route("/main")
def main_page():
    if is_json_request():
        return jsonify(message="Добро пожаловать на главную страницу")
    return render_template('main.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)