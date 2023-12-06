import os
from flask_mysqldb import MySQL
from flask import Flask,render_template,request,redirect,url_for,session,flash
import MySQLdb.cursors
import re
import numpy as np
import pickle
import tensorflow as tf
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bangkit123'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'pintarkur'
mysql = MySQL(app)
model_try = None  # Global variable to store the loaded model

def load_model():
    global nn_model
    nn_model = tf.keras.models.load_model('ML/model.h5')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        if '@' not in email:
            flash('Invalid Email', 'error')
            return email
        else:
            password = request.form['password']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM user WHERE email = %s AND password = %s", (email, password))
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['nama'] = account['nama']
                return redirect(url_for('home'))
            else:
                flash("Email/password salah", "error")
    return render_template('auth/login.html', title="Login")

@app.route('/daftar', methods=['GET', 'POST'])
def daftar():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    if request.method == 'POST' and 'nama' in request.form and 'password' in request.form and 'email' in request.form:
        nik = request.form['nik']
        if len(nik) != 16:
            flash("Masukkan 16 digit NIK anda!", "danger")
        elif not nik.isnumeric():
            flash("Masukkan angka dengan benar!", "danger") 
        else:
            nama = request.form['nama']
            email = request.form['email']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM user WHERE email LIKE %s", [email])
            account = cursor.fetchone()
            if account:
                flash("Email telah digunakan!", "danger")
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                flash("Alamat email invalid!", "danger")
            else:
                password = request.form['password']
                cursor.execute('INSERT INTO user VALUES (%s,%s,%s,%s)', (nik, nama, email, password))
                mysql.connection.commit()
                flash("Registrasi Berhasil!", "Success")
                return redirect(url_for('login'))
    elif request.method == 'POST':
        flash("Mohon isi form!", "danger")
    return render_template('auth/daftar.html', title="Sign up")
# End of Authentication

#After authentication
@app.route('/home')
def home():
    if 'loggedin' in session:
        nama = session['nama']  
        return render_template('home/home.html', title="Home", nama=nama)
    return render_template(url_for('login'))
@app.route('/tentang')
def tentang():
    if 'loggedin' in session:
        nama = session['nama']
        return render_template('home/tentang.html', title="Home", nama=nama)
    return render_template(url_for('login'))
@app.route('/penyalur')
def penyalur():
    if 'loggedin' in session:
        nama = session['nama']
        return render_template('home/cari_penyalur.html', title="Home", nama=nama)
    return render_template(url_for('login'))
@app.route('/simulasi')
def simulasi():
    if 'loggedin' in session:
        nama = session['nama']
        return render_template('home/simulasi.html', title="Home", nama=nama)
    return render_template(url_for('login'))
@app.route('/analisis')
def analisis():
    #if 'loggedin' in session:
    return render_template('home/analisis.html',title="Analisis")
    #return redirect('login')

@app.route('/predict',methods=['POST'])
def predict():
    list_request = []
    list_request.append(request.form['term'])
    list_request.append(request.form['number_of_employee'])
    list_request.append(request.form['new_existing_business'])
    list_request.append(request.form['created_job'])
    list_request.append(request.form['retained_job'])
    list_request.append(request.form['urban_area'])
    list_request.append(request.form['loan_documentation'])
    list_request.append(request.form['loan_requested'])
    list_request.append(request.form['has_franchise'])
    list_request.append(request.form['real_estate'])

    # State One Hot Encode
    state = [0] * 51
    state_idx = int(request.form['state'])
    state[state_idx-1] = 1

    # NAICS One Hot Encode 
    naics_code = [0] * 21
    naics_idx = int(request.form['business_sector'])
    naics_code[naics_idx] = 1

    # Compiling 
    list_request = list_request + state + naics_code

    # SBA Coverage Calculation 
    sba_coverage = int(request.form['sba_covered']) / int(request.form['loan_requested']) * 100
    list_request.append(sba_coverage)

    # Iterate over the generator and print each value
    print(list_request)
    print(len(list_request))

    # import scaler
    sc_file_path = "ML/pre_process_scaler.pkl"
    with open(sc_file_path, 'rb') as file:
        scaler_fixed = pickle.load(file)

    # load model 
    load_model()

    # prediction
    int_list_req = [int(x) for x in list_request]
    final_features = np.array(int_list_req)
    final_data_2d = final_features.reshape(1, -1)
    scaled_final_data = scaler_fixed.transform(final_data_2d)
    predict_data = nn_model.predict(scaled_final_data)[0][0]
    predict_data = '{:.2f}'.format(predict_data)
    predict_data = float(predict_data)*100
    return render_template('home/predict.html', predict_score=predict_data)

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host='0.0.0.0', port=port)