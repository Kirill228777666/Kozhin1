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
import json
import tempfile
from pathlib import Path
from threading import Lock
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

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
# БАЛАНС И ЗАПРОСЫ К НЕЙРОСЕТИ
# =========================================================

REQUEST_PRICE = Decimal("1.00")  # Стоимость одного запроса в рублях

# Локальная модель: скачивается автоматически при первом запросе.
MODEL_REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
MODEL_FILE = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODEL_LOCK = Lock()
model = None


def generate_reply(message):
    global model
    # llama.cpp не должен одновременно обрабатывать несколько запросов
    # через один экземпляр Llama.
    with MODEL_LOCK:
        if model is None:
            from llama_cpp import Llama
            model = Llama.from_pretrained(
                repo_id=MODEL_REPO,
                filename=MODEL_FILE,
                n_ctx=2048,
                n_threads=min(4, os.cpu_count() or 1),
                n_gpu_layers=0,
                verbose=False,
            )
        result = model.create_chat_completion(
            messages=[
                {"role": "system", "content": "Ты NeuroSphere AI, полезный помощник. Отвечай на языке пользователя."},
                {"role": "user", "content": message},
            ],
            max_tokens=384,
            temperature=0.7,
        )
        reply = result["choices"][0]["message"]["content"]
        if not isinstance(reply, str) or not reply.strip():
            raise ValueError("Модель вернула пустой ответ")
        return reply.strip()

# История хранится в отдельном JSON-файле, без изменений в MySQL.
HISTORY_FILE = Path(__file__).resolve().parents[2] / "history.json"
HISTORY_LOCK = Lock()


def read_history():
    """Читает историю всех аккаунтов. Вызывать под HISTORY_LOCK."""
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Некорректный формат истории")
    return data


def save_history(email, message, reply):
    """Добавляет один успешный запрос в историю пользователя."""
    with HISTORY_LOCK:
        data = read_history()
        data.setdefault(email, []).append({
            "message": message,
            "reply": reply,
            "date": datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"),
            "cost": format(REQUEST_PRICE, ".2f")
        })
        # Сначала записываем во временный файл, затем заменяем оригинал.
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=HISTORY_FILE.parent,
                prefix=".history-", suffix=".tmp", delete=False
            ) as file:
                temp_path = Path(file.name)
                json.dump(data, file, ensure_ascii=False, indent=4)
            os.replace(temp_path, HISTORY_FILE)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()


def user_history(email):
    with HISTORY_LOCK:
        return list(reversed(read_history().get(email, [])))



def change_balance(amount=None):
    """Получает баланс или изменяет его в одной транзакции."""
    conn = get_db_connection()
    if conn is None:
        return jsonify(success=False, message="Ошибка подключения к базе данных"), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT balance FROM users WHERE email = %s FOR UPDATE",
            (session["user_email"],)
        )
        user = cursor.fetchone()
        if user is None:
            conn.rollback()
            return jsonify(success=False, message="Пользователь не найден"), 404

        balance = Decimal(str(user["balance"]))
        if amount is not None:
            if balance + amount < 0:
                conn.rollback()
                return jsonify(
                    success=False,
                    message="Недостаточно средств. Пополните баланс в личном кабинете.",
                    balance=format(balance, ".2f")
                ), 400

            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE email = %s",
                (amount, session["user_email"])
            )
            cursor.execute(
                "SELECT balance FROM users WHERE email = %s",
                (session["user_email"],)
            )
            balance = Decimal(str(cursor.fetchone()["balance"]))

        conn.commit()
        return jsonify(success=True, balance=format(balance, ".2f"))

    except mysql.connector.Error:
        conn.rollback()
        traceback.print_exc()
        return jsonify(success=False, message="Ошибка при работе с базой данных"), 500
    finally:
        conn.close()


@app.route("/api/balance", methods=["GET"])
def get_balance():
    if not is_authorized():
        return jsonify(success=False, message="Войдите в аккаунт"), 401
    return change_balance()


@app.route("/api/balance/topup", methods=["POST"])
def topup_balance():
    if not is_authorized():
        return jsonify(success=False, message="Войдите в аккаунт"), 401

    data = request.get_json(silent=True)
    try:
        amount = Decimal(str(data["amount"]))
        if (not amount.is_finite() or amount <= 0 or amount > Decimal("1000000")
                or amount != amount.quantize(Decimal("0.01"))):
            raise ValueError
    except (InvalidOperation, ValueError, TypeError, KeyError):
        return jsonify(success=False, message="Введите положительную сумму в рублях (до 1 000 000, не более двух знаков после запятой)"), 400

    return change_balance(amount)


@app.route("/api/chat", methods=["POST"])
def chat_request():
    if not is_authorized():
        return jsonify(success=False, message="Войдите в аккаунт"), 401

    data = request.get_json(silent=True)
    message = data.get("message") if isinstance(data, dict) else None
    if not isinstance(message, str) or not message.strip():
        return jsonify(success=False, message="Введите сообщение"), 400

    # Проверяем баланс до загрузки модели и генерации.
    current = change_balance()
    if isinstance(current, tuple):
        return current
    balance = current.get_json()["balance"]
    if Decimal(balance) < REQUEST_PRICE:
        return jsonify(success=False, balance=balance,
                       message="Недостаточно средств. Пополните баланс в личном кабинете."), 400

    # При ошибке модели деньги не списываются.
    try:
        response = generate_reply(message.strip())
    except Exception:
        traceback.print_exc()
        return jsonify(success=False, message="Не удалось получить ответ Qwen. Проверьте терминал сервера и доступ к Hugging Face. Баланс не списан."), 503

    result = change_balance(-REQUEST_PRICE)
    if isinstance(result, tuple):
        return result
    # Записываем только запросы, за которые успешно списан баланс.
    history_saved = True
    try:
        save_history(session["user_email"], message.strip(), response)
    except (OSError, ValueError, TypeError, AttributeError):
        traceback.print_exc()
        history_saved = False
    return jsonify(success=True, balance=result.get_json()["balance"],
                   reply=response, history_saved=history_saved)


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
        request_price=format(REQUEST_PRICE, ".2f"),
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

    try:
        entries = user_history(session["user_email"])
    except (OSError, ValueError, TypeError, AttributeError):
        traceback.print_exc()
        return render_template("history.html", entries=[], history_error=True), 500

    return render_template("history.html", entries=entries, history_error=False)


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