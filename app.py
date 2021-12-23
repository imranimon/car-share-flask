from flask import Flask, render_template, redirect, url_for, request, session
from flask_db2 import DB2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
import os
import process

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.config['DB2_DATABASE'] = os.getenv('DB2_DATABASE')
app.config['DB2_HOSTNAME'] = os.getenv('DB2_HOSTNAME')
app.config['DB2_PORT'] = os.getenv('DB2_PORT')
app.config['DB2_PROTOCOL'] = os.getenv('DB2_PROTOCOL')
app.config['DB2_USER'] = os.getenv('DB2_USER')
app.config['DB2_PASSWORD'] = os.getenv('DB2_PASSWORD')

db = DB2(app)


@app.route('/')
def index():
    cur = db.connection.cursor()
    cur.execute('select * from fahrt')
    rides = cur.fetchall()
    ride_list = process.process_list(rides)

    cur.close()
    del cur
    return render_template('index.html', rides=ride_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
    cur = db.connection.cursor()
    message = ""
    if request.method == "POST":
        email = request.form["email"]
        if email is not None:
            cur.execute("select bid,name,email from benutzer where email= ?", (email,))
            result = cur.fetchone()
            loggedinUser = []
            if result is not None:
                for item in result:
                    loggedinUser.append(item)
            if result:
                session["ses_user"] = loggedinUser
                session['logged_in'] = True
                return redirect(url_for("mainView"))
            else:
                session['logged_in'] = False
                message = "Email Is Not Valid"
    cur.close()
    del cur
    return render_template('login.html', message=message)


@app.route('/register', methods=['GET', 'POST'])
def register():
    cur = db.connection.cursor()
    message = ''
    if request.method == "POST":
        email = request.form["email"]
        name = request.form["name"]
        cur.execute("select * from benutzer where email=?", (email,))
        result = cur.fetchall()

        if result:
            message = 'You are already registered to our site'
        else:
            cur.execute("insert into benutzer (email, name) values (?,?)", (email, name,))
            return redirect(url_for("login"))
    cur.close()
    del cur
    return render_template('register.html', message=message)


@app.route('/logout')
def logout():
    session.pop("ses_user", None)
    return redirect(url_for("login"))


@app.route('/main-view', methods=['GET', 'POST'])
def mainView():
    if "ses_user" in session:
        user = session["ses_user"]
        cur = db.connection.cursor()
        cur.execute(
            "select startort,zielort,status, transportmittel.icon,fid from fahrt join reservieren on fahrt.fid = reservieren.fahrt join transportmittel on fahrt.transportmittel = transportmittel.tid where reservieren.kunde =? ",
            (user[0],))
        result = cur.fetchall()
        booked_trips = process.process_list(result)
        cur.execute(
            "select startort,zielort,status,fahrtkosten,transportmittel.icon,fid from fahrt join transportmittel on fahrt.transportmittel = transportmittel.tid where  maxPlaetze>0")
        result = cur.fetchall()
        availabe_rides = process.process_list(result)

        cur.close()
        del cur
        return render_template('main_view.html', booked_trips=booked_trips, availabe_rides=availabe_rides)
    else:
        return redirect(url_for("login"))


@app.route('/view-drive/<fid>')
def viewDrive(fid):
    if "ses_user" in session:
        user = session["ses_user"]
        cur = db.connection.cursor()

        cur.close()
        del cur
        return render_template('view_drive.html')
    else:
        return redirect(url_for("login"))


@app.route('/new-drive', methods=['GET', 'POST'])
def newDrive():
    if "ses_user" in session:
        user = session["ses_user"]
        cur = db.connection.cursor()
        message = ''
        if request.method == "POST":
            start_from = request.form["from"]
            destination = request.form["to"]
            max_capacity = int(request.form["maxCapacity"])
            cost = int(request.form["cost"])
            transport = request.form["transport"]
            description = request.form["description"]

            date_time = request.form["dateTime"]
            [date, time] = date_time.split('T')
            formated_date_time = date + ' ' + time + ':' + '00'

            if start_from is not None and destination is not None and max_capacity in (
                    1, 2, 3, 4, 5, 6, 7, 8, 9,
                    10) and (cost > 0) and transport is not None and date_time is not None and len(description) <= 50:
                cur.execute(
                    'INSERT INTO fahrt (startort, zielort, fahrtdatumzeit, maxPlaetze, fahrtkosten, anbieter, transportmittel, beschreibung)  VALUES (?,?,?,?,?,?,?,?)',
                    (start_from, destination, formated_date_time, max_capacity, cost, user[0], transport, description))
                return redirect(url_for("mainView"))
            else:
                message = ['All asterisk (*) fileds and required',
                           'The allowed value for Maximum Capacity is between 1 and 10',
                           'Cost have to be a greater than 0',
                           'Length of description can not be greater than 50']
        cur.close()
        del cur
        return render_template('new_drive.html', message=message)
    else:
        return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(debug=True)
