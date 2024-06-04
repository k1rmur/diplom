from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import psycopg2
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import re

base_dir = os.path.abspath(os.path.dirname(__file__))

template_dir = os.path.join(base_dir, '/home/kirmur/computer_club/templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'your_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, name):
        self.id = id
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    try:
        conn = psycopg2.connect(database="computer_club", user="postgres", password="15964", host="localhost", port="5432")
        cur = conn.cursor()
        cur.execute("SELECT id_user, email FROM computer_club.users WHERE id_user = %s", (user_id,))
        user = cur.fetchone()
        if user:
            return User(user[0], user[1])
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        cur.close()
        conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            conn = psycopg2.connect(database="computer_club", user="postgres", password="15964", host="localhost", port="5432")
            cur = conn.cursor()

            query = "SELECT id_user, name FROM computer_club.users WHERE email = %s AND parol = %s"
            cur.execute(query, (email, password))
            user = cur.fetchone()

            if user:
                user_obj = User(user[0], user[1])
                login_user(user_obj, remember=True)
                print(f"User {user[0]} logged in successfully.")
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Неверные email или пароль."})
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            print(traceback.format_exc())
            return jsonify({"success": False, "error": str(e)})
        finally:
            cur.close()
            conn.close()

    return render_template('login.html')

@app.route('/profile')
@login_required
def profile():
    try:
        conn = psycopg2.connect(database="computer_club", user="postgres", password="15964", host="localhost", port="5432")
        cur = conn.cursor()

        # Получаем текущего пользователя
        user = current_user

        # Получаем роль пользователя
        cur.execute("SELECT role_user FROM computer_club.users WHERE email = %s", (user.name,))
        role = cur.fetchone()[0]

        # Получаем баланс пользователя из базы данных по его email
        cur.execute("SELECT balance FROM computer_club.users WHERE email = %s", (user.name,))
        balance = cur.fetchone()[0]
        # Получаем будущие брони пользователя
        future_bookings = get_future_bookings(user.name)
        
        # Проверяем, является ли пользователь администратором
        is_admin = (role == 'admin')

        return render_template('profile.html', username=user.name, balance=balance, future_bookings=future_bookings, is_admin=is_admin)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)})

    finally:
        cur.close()
        conn.close()



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/reg')
@login_required
def reg():
    return render_template('register.html')

@app.route('/get-seat-image', methods=['GET'])
def get_seat_image():
    place_id = request.args.get('place_id')

    try:
        conn = psycopg2.connect(database="computer_club", user="postgres", password="15964", host="localhost", port="5432")
        cur = conn.cursor()
        query = "SELECT start_time, end_time FROM computer_club.seats_halls WHERE place = %s"
        cur.execute(query, (place_id,))
        result = cur.fetchone()
        
        if result:
            start_time, end_time = result
            current_time = datetime.now().time()

            if start_time < end_time:
                if start_time <= current_time <= end_time:
                    image = "red"
                else:
                    image = "green"
            else:
                if current_time >= start_time or current_time <= end_time:
                    image = "red"
                else:
                    image = "green"
        else:
            image = "green"

    except Exception as e:
        print(f"Error: {e}")
        image = "green" 

    finally:
        cur.close()
        conn.close()

    return jsonify({"image_url": image})

@app.route('/submit-booking', methods=['POST'])
def submit_booking():
    phone_or_email = request.form['phone']
    date = request.form['date']
    time = request.form['time']
    place = request.form['place']
    seat = request.form['seat']
    hours = int(request.form['hours'])
    start_datetime = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
    end_datetime = start_datetime + timedelta(hours=hours)

    if re.match(r'^(\+7|8)\d{10}$', phone_or_email):
        phone = phone_or_email
        email = None
    elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', phone_or_email):
        phone = None
        email = phone_or_email
    else:
        return jsonify({"success": False, "error": "Введите корректный номер телефона или email."})

    try:
        conn = psycopg2.connect(database="computer_club", user="postgres", password="15964", host="localhost", port="5432")
        cur = conn.cursor()

        if place == 'PC Общий зал':
            seat = int(seat)
        elif place == 'PC VIP зал':
            seat = int(seat) + 15
        elif place == 'PS 4':
            seat = 21
        elif place == 'PS 5':
            seat = 22
        elif place == 'Стримерская':
            seat = 23
        else:
            return jsonify({"success": False, "error": "Выбрано неверное место."})
        
        # Проверка наличия записей в базе данных перед добавлением новой брони
        query_check = """
            SELECT 1 FROM computer_club.reservation
            WHERE id_oborud = %s AND 
                  (date_and_time_nachala <= %s AND date_and_time_konec >= %s)
        """
        cur.execute(query_check, (seat, start_datetime, end_datetime))
        print(cur.mogrify(query_check, (seat, start_datetime, end_datetime)))
        if cur.fetchone():
            return jsonify({"success": False, "error": "Это место уже забронировано на указанное время."})

        if email:
            cur.execute("SELECT id_user FROM computer_club.users WHERE email = %s", (email,))
            user_id = cur.fetchone()
            if user_id:
                user_id = user_id[0]
            else:
                return jsonify({"success": False, "error": "Пользователь с указанным email не найден."})

        query = "SELECT MAX(id_bron) FROM computer_club.reservation"
        cur.execute(query)
        max_id_bron = cur.fetchone()[0]

        new_id_bron = max_id_bron + 1 if max_id_bron else 1

        id_oborud = seat

        query = """
            INSERT INTO computer_club.reservation (id_bron, id_user, id_oborud, date_and_time_nachala, date_and_time_konec)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(query, (new_id_bron, user_id, id_oborud, start_datetime, end_datetime) if email else (new_id_bron, current_user.id, id_oborud, start_datetime, end_datetime))
        conn.commit()

        if phone:
            return jsonify({"success": True, "message": f"Бронирование выполнено успешно."})
        elif email:
            return jsonify({"success": True, "message": f"Бронирование выполнено успешно."})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)})

    finally:
        cur.close()
        conn.close()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    surname = request.form.get('surname')
    email = request.form.get('email')
    password = request.form.get('password')

    try:
        conn = psycopg2.connect(database="computer_club", user="postgres", password="15964", host="localhost", port="5432")
        cur = conn.cursor()

        cur.execute("SELECT id_user FROM computer_club.users WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({"success": False, "error": "Пользователь с таким email уже существует."})

        cur.execute("SELECT MAX(id_user) FROM computer_club.users WHERE id_user <> 4321")
        max_id_user = cur.fetchone()[0] or 0
        new_id_user = max_id_user + 1

        query = """
            INSERT INTO computer_club.users (id_user, name, familia, email, parol, balance, role_user)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (new_id_user, username, surname, email, password, 0, 'client'))
        conn.commit()

        return jsonify({"success": True, "message": "Регистрация успешно завершена!"})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)})

    finally:
        cur.close()
        conn.close()

def get_future_bookings(email):
    try:
        conn = psycopg2.connect(database="computer_club", user="postgres", password="15964", host="localhost", port="5432")
        cur = conn.cursor()
        
        # Получаем ID пользователя по его электронной почте
        cur.execute("SELECT id_user FROM computer_club.users WHERE email = %s", (email,))
        user_id = cur.fetchone()[0]
        
        # Получаем все будущие брони пользователя
        cur.execute("""
            SELECT id_bron, id_oborud, date_and_time_nachala
            FROM computer_club.reservation
            WHERE id_user = %s AND date_and_time_nachala > NOW()
            ORDER BY date_and_time_nachala
        """, (user_id,))
        
        bookings = cur.fetchall()
        return bookings
        
    except Exception as e:
        print(f"Error: {e}")
        return []

    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)