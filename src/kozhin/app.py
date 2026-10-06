from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    session
)

import mysql.connector
import re
import traceback
import os

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


app = Flask(__name__)


app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-neurosphere-secret-key-change-me"
)


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
    """
    Определяем, ожидает ли клиент JSON.
    script.js отправляет Accept: application/json.
    """

    return (
        request.is_json
        or request.headers.get("Accept") == "application/json"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def is_authorized():
    """
    Проверяем, авторизован ли пользователь.
    """

    return "user_email" in session


# =========================================================
# ВХОД
# =========================================================

@app.route("/", methods=["GET", "POST"])
def hello_world():

    if request.method == "GET" and is_authorized():
        return redirect(url_for("lk"))

    if request.method == "POST":

        if request.is_json:
            data = request.get_json()

            email = data.get("email", "").strip()
            password = data.get("password", "")

        else:
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

        if not email or not password:

            error = "Email и пароль обязательны"

            if is_json_request():
                return jsonify(
                    success=False,
                    errors=[error]
                ), 400

            return render_template(
                "login.html",
                error=error
            )

        conn = get_db_connection()

        if conn is None:

            error = "Ошибка подключения к базе данных"

            if is_json_request():
                return jsonify(
                    success=False,
                    errors=[error]
                ), 500

            return render_template(
                "login.html",
                error=error
            )

        try:

            cursor = conn.cursor(
                dictionary=True
            )

            # Ищем пользователя по email
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

        except mysql.connector.Error as err:

            print(f"Ошибка запроса: {err}")
            traceback.print_exc()

            error = "Ошибка при работе с базой данных"

            if is_json_request():
                return jsonify(
                    success=False,
                    errors=[error]
                ), 500

            return render_template(
                "login.html",
                error=error
            )

        finally:
            conn.close()

        # Проверяем пароль по хэшу
        if (
            user
            and check_password_hash(
                user["password_hash"],
                password
            )
        ):

            # Очищаем старую сессию
            session.clear()

            # Запоминаем пользователя
            session["user_email"] = user["email"]
            session["username"] = user["username"]

            # После успешного входа отправляем в ЛК
            if is_json_request():

                return jsonify(
                    success=True,
                    redirect=url_for("lk")
                )

            return redirect(
                url_for("lk")
            )

        error = "Неверный логин или пароль"

        if is_json_request():

            return jsonify(
                success=False,
                errors=[error]
            ), 401

        return render_template(
            "login.html",
            error=error
        )

    return render_template(
        "login.html",
        error=None
    )


# =========================================================
# РЕГИСТРАЦИЯ
# =========================================================

@app.route(
    "/registration",
    methods=["GET", "POST"]
)
def registration():

    if request.method == "POST":

        if request.is_json:

            data = request.get_json()

            name = data.get(
                "name",
                ""
            ).strip()

            surname = data.get(
                "surname",
                ""
            ).strip()

            email = data.get(
                "email",
                ""
            ).strip()

            password = data.get(
                "password",
                ""
            )

        else:

            name = request.form.get(
                "name",
                ""
            ).strip()

            surname = request.form.get(
                "surname",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip()

            password = request.form.get(
                "password",
                ""
            )

        errors = []

        # ---------------------------
        # ИМЯ
        # ---------------------------

        if not name or len(name) < 2:

            errors.append(
                "Имя должно содержать минимум 2 символа"
            )

        elif not re.match(
            r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$",
            name
        ):

            errors.append(
                "Имя может содержать только буквы, пробелы и дефис"
            )

        # ---------------------------
        # ФАМИЛИЯ
        # ---------------------------

        if not surname or len(surname) < 2:

            errors.append(
                "Фамилия должна содержать минимум 2 символа"
            )

        elif not re.match(
            r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$",
            surname
        ):

            errors.append(
                "Фамилия может содержать только буквы, пробелы и дефис"
            )

        # ---------------------------
        # EMAIL
        # ---------------------------

        if not re.match(
            r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
            email
        ):

            errors.append(
                "Некорректный email"
            )

        # ---------------------------
        # ПАРОЛЬ
        # ---------------------------

        if len(password) < 8:

            errors.append(
                "Пароль должен содержать минимум 8 символов"
            )

        if not re.search(
            r"[A-Z]",
            password
        ):

            errors.append(
                "Пароль должен содержать хотя бы одну заглавную букву"
            )

        if not re.search(
            r"[a-z]",
            password
        ):

            errors.append(
                "Пароль должен содержать хотя бы одну строчную букву"
            )

        if not re.search(
            r"[0-9]",
            password
        ):

            errors.append(
                "Пароль должен содержать хотя бы одну цифру"
            )

        if not re.match(
            r"""^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]+$""",
            password
        ):

            errors.append(
                "Пароль может содержать только латинские буквы, цифры и спецсимволы"
            )

        if re.search(r"\s", password):

            errors.append(
                "Пароль не должен содержать пробелы"
            )

        # ---------------------------
        # ЕСЛИ ЕСТЬ ОШИБКИ
        # ---------------------------

        if errors:

            if is_json_request():

                return jsonify(
                    success=False,
                    errors=errors
                ), 400

            return render_template(
                "registration.html",
                errors=errors
            )

        conn = get_db_connection()

        if conn is None:

            errors.append(
                "Ошибка подключения к базе данных"
            )

            if is_json_request():

                return jsonify(
                    success=False,
                    errors=errors
                ), 500

            return render_template(
                "registration.html",
                errors=errors
            )

        try:

            cursor = conn.cursor()

            # Проверяем существование пользователя
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            existing_user = cursor.fetchone()

            if existing_user:

                errors.append(
                    "Пользователь с таким email уже существует"
                )

                if is_json_request():

                    return jsonify(
                        success=False,
                        errors=errors
                    ), 409

                return render_template(
                    "registration.html",
                    errors=errors
                )

            # Хэшируем пароль
            hashed_password = generate_password_hash(
                password
            )

            # Создаём пользователя.
            # balance автоматически станет 0.00
            # благодаря DEFAULT в таблице.
            cursor.execute(
                """
                INSERT INTO users (
                    username,
                    surname,
                    email,
                    password_hash
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    name,
                    surname,
                    email,
                    hashed_password
                )
            )

            conn.commit()

        except mysql.connector.Error as err:

            print(f"Ошибка запроса: {err}")
            traceback.print_exc()

            errors.append(
                "Ошибка при работе с базой данных"
            )

            if is_json_request():

                return jsonify(
                    success=False,
                    errors=errors
                ), 500

            return render_template(
                "registration.html",
                errors=errors
            )

        finally:
            conn.close()

        # После регистрации отправляем на вход
        if is_json_request():

            return jsonify(
                success=True,
                redirect=url_for(
                    "hello_world"
                )
            )

        return redirect(
            url_for(
                "hello_world"
            )
        )

    return render_template(
        "registration.html",
        errors=[]
    )


# =========================================================
# ВОССТАНОВЛЕНИЕ ПАРОЛЯ
# =========================================================

@app.route(
    "/password_vosst",
    methods=["GET", "POST"]
)
def password_reset():

    if request.method == "POST":

        if request.is_json:

            data = request.get_json()

            email = data.get(
                "email",
                ""
            ).strip()

        else:

            email = request.form.get(
                "email",
                ""
            ).strip()

        if not re.match(
            r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
            email
        ):

            error = "Некорректный email"

            if is_json_request():

                return jsonify(
                    success=False,
                    errors=[error]
                ), 400

            return render_template(
                "password_vosst.html",
                error=error
            )

        success_msg = (
            "Инструкции по восстановлению отправлены на email"
        )

        if is_json_request():

            return jsonify(
                success=True,
                message=success_msg
            )

        return render_template(
            "password_vosst.html",
            success=success_msg
        )

    return render_template(
        "password_vosst.html"
    )


# =========================================================
# ЛИЧНЫЙ КАБИНЕТ
# =========================================================

@app.route("/lk")
def lk():

    # Без авторизации в ЛК попасть нельзя
    if not is_authorized():

        return redirect(
            url_for(
                "hello_world"
            )
        )

    conn = get_db_connection()

    if conn is None:

        return (
            "Ошибка подключения к базе данных",
            500
        )

    try:

        cursor = conn.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                username,
                surname,
                email,
                balance
            FROM users
            WHERE email = %s
            """,
            (
                session["user_email"],
            )
        )

        user = cursor.fetchone()

    except mysql.connector.Error as err:

        print(f"Ошибка запроса: {err}")
        traceback.print_exc()

        return (
            "Ошибка при работе с базой данных",
            500
        )

    finally:
        conn.close()

    # Пользователь был в session,
    # но из БД его почему-то удалили
    if not user:

        session.clear()

        return redirect(
            url_for(
                "hello_world"
            )
        )

    return render_template(
        "lk.html",
        user=user
    )


# =========================================================
# СТРАНИЦА НЕЙРОСЕТИ
# =========================================================

@app.route("/main")
def main_page():

    if not is_authorized():

        return redirect(
            url_for(
                "hello_world"
            )
        )

    return render_template(
        "main.html",
        user_name=session.get(
            "username",
            "Профиль"
        )
    )


# =========================================================
# ИСТОРИЯ
# =========================================================

@app.route("/history")
def history():

    if not is_authorized():

        return redirect(
            url_for(
                "hello_world"
            )
        )

    return render_template(
        "history.html"
    )


# =========================================================
# ВЫХОД
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for(
            "hello_world"
        )
    )


# =========================================================
# ЗАПУСК
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=8000
    )