from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
import psycopg2
import os
import secrets


app = Flask(__name__, static_url_path='/static')

os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = '2680328442'
secret_key = secrets.token_urlsafe(32)

def initialize_database():
    conn = psycopg2.connect(
        host="localhost",
        database="adoption_db",
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD']
    )
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS users;')

    cur.execute('CREATE TABLE users ('
                'id serial PRIMARY KEY, '
                'email varchar(255) UNIQUE NOT NULL, ' 
                'password varchar(255) NOT NULL, '      
                'name varchar(150) NOT NULL, '
                'last_name varchar(50) NOT NULL, '  
                'pet_name varchar(100), '  
                'date_added date DEFAULT CURRENT_TIMESTAMP);'
                )
    conn.commit()
    cur.close()
    conn.close()

# initialize_database()

app.secret_key = secret_key

bcrypt = Bcrypt(app)

@app.route("/home")
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = psycopg2.connect(
            host="localhost",
            database="adoption_db",
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD']
        )
        cur = conn.cursor()

        cur.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if user:
            name = user[0]
        else:
            name = "Unknown"
        return render_template("index.html", logged_in=True, name=name)
    else:
        return render_template("index.html", logged_in=False)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = psycopg2.connect(
            host="localhost",
            database="adoption_db",
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD']
        )
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user:
            if bcrypt.check_password_hash(user[2], password):  
                session['user_id'] = user[0]  
                cur.close()
                conn.close()
                return redirect(url_for('pets')) 
            else:
                cur.close()
                conn.close()
                return "Incorrect password"
        else:
            cur.close()
            conn.close()
            return "User not found"

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"] 
        name = request.form["name"]
        last_name = request.form["last_name"]
        pet_name = request.form.get("pets")
        
        if password != confirm_password:
            return "Passwords do not match!"

        conn = psycopg2.connect(
            host="localhost",
            database="adoption_db",
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD']
        )
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()
        if existing_user:
            cur.close()
            conn.close()
            return "Email in use!"

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cur.execute("INSERT INTO users (email, password, name, last_name, pet_name) VALUES (%s, %s, %s, %s, %s)",
                    (email, hashed_password, name, last_name, pet_name))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('login'))

    return render_template("signup.html")

@app.route("/pets")
def pets():
    return render_template("pets.html")

app.static_folder = 'static'

if __name__ == "__main__":
    app.run(debug=True)
