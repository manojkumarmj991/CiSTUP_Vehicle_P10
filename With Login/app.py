from flask import Flask, render_template, request, flash, jsonify,get_flashed_messages,Response,session,redirect,url_for
import cv2, os,json
from ultralytics import YOLO
import pandas as pd
import mysql.connector
from key import secret_key,salt,salt2
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import sendmail
import mysql.connector.pooling
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = b'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['SESSION_TYPE']='filesystem'

# db=os.environ['RDS_DB_NAME']
# user=os.environ['RDS_USERNAME']
# password=os.environ['RDS_PASSWORD']
# host=os.environ['RDS_HOSTNAME']
# port=os.environ['RDS_PORT']

# conn=mysql.connector.pooling.MySQLConnectionPool(host=host,user=user,password=password,db=db,port=port,pool_name='DED',pool_size=3,pool_reset_session=True)

conn=mysql.connector.pooling.MySQLConnectionPool(host='localhost',user='root',password="root",db='vehicle',pool_name='DED',pool_size=3, pool_reset_session=True)

try:
    mydb=conn.get_connection()
    cursor = mydb.cursor(buffered=True)
    cursor.execute('CREATE TABLE IF NOT EXISTS users (uid INT PRIMARY KEY auto_increment, username VARCHAR(50), password VARCHAR(15), email VARCHAR(60))')

except Exception as e:
    print(e)
finally:
    if mydb.is_connected():
        mydb.close()

# Load the pre-trained YOLO model
model = YOLO('best.pt')

# Load class list
with open("coco.txt", "r") as file:
    class_list = file.read().split("\n")

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to save detected objects to a JSON file
def save_objects(filename, objects, tags):
    try:
        with open('objects.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    
    data[filename] = {'objects': [obj['label'] for obj in objects], 'tags': tags}
    
    with open('objects.json', 'w') as file:
        json.dump(data, file)

def get_unique_objects_and_tags():
    unique_objects = set()
    unique_tags = set()
    try:
        with open('objects.json', 'r') as file:
            data = json.load(file)
            for info in data.values():
                unique_objects.update(info['objects'])
                unique_tags.update(info['tags'])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return list(unique_objects), list(unique_tags)


@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('username'):
        return redirect(url_for('home'))
    if request.method=='POST':
        print(request.form)
        name=request.form['name']
        password=request.form['password']
        try:
            mydb=conn.get_connection()
            cursor=mydb.cursor(buffered=True)
        except Exception as e:
            print(e)
        else:
            cursor.execute('SELECT count(*) from users where username=%s and password=%s',[name,password])
            count=cursor.fetchone()[0]
            cursor.close()
            if count==1:
                session['username']=name
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password')
                return render_template('login.html')
        finally:
            if mydb.is_connected():
                mydb.close()
    return render_template('login.html')

@app.route('/registration',methods=['GET','POST'])
def registration():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        try:
            mydb=conn.get_connection()
            cursor=mydb.cursor(buffered=True)
        except Exception as e:
            print(e)
        else:
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = %s', [username])
            count=cursor.fetchone()[0]
            cursor.execute('select count(*) from users where email=%s',[email])
            count1=cursor.fetchone()[0]
            cursor.close()
            if count==1:
                flash('username already in use')
                return render_template('registration.html')
            elif count1==1:
                flash('Email already in use')
                return render_template('registration.html')
            data={'username':username,'password':password,'email':email}
            subject='Email Confirmation'
            body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data,salt),_external=True)}"
            sendmail(to=email,subject=subject,body=body)
            flash('Confirmation link sent to mail')
            return redirect(url_for('login'))
        finally:
            if mydb.is_connected():
                mydb.close()
    return render_template('registration.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        #print(e)
        return 'Link Expired register again'
    else:
        try:
            mydb=conn.get_connection()
            cursor=mydb.cursor(buffered=True)
        except Exception as e:
            print(e)
        else:
            username=data['username']
            cursor.execute('select count(*) from users where username=%s',[username])
            count=cursor.fetchone()[0]
            if count==1:
                cursor.close()
                flash('You are already registerterd!')
                return redirect(url_for('login'))
            else:
                cursor.execute('insert into users(username,password,email) values(%s,%s,%s)',(data['username'], data['password'], data['email']))
                mydb.commit()
                cursor.close()
                flash('Details registered!')
                return redirect(url_for('login'))
        finally:
            if mydb.is_connected():
                mydb.close()


@app.route('/forget',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        email=request.form['email']
        try:
            mydb=conn.get_connection()
            cursor=mydb.cursor(buffered=True)
        except Exception as e:
            print(e)
        else:
            cursor.execute('select count(*) from users where email=%s',[email])
            count=cursor.fetchone()[0]
            cursor.close()
            if count==1:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('SELECT email from users where email=%s',[email])
                status=cursor.fetchone()[0]
                cursor.close()
                subject='Forget Password'
                confirm_link=url_for('reset',token=token(email,salt=salt2),_external=True)
                body=f"Use this link to reset your password-\n\n{confirm_link}"
                sendmail(to=email,body=body,subject=subject)
                flash('Reset link sent check your email')
                return redirect(url_for('login'))
            else:
                flash('Invalid email id')
                return render_template('forgot.html')
        finally:
            if mydb.is_connected():
                mydb.close()
    return render_template('forgot.html')


@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                try:
                    mydb=conn.get_connection()
                    cursor=mydb.cursor(buffered=True)
                except Exception as e:
                    print(e)
                else:
                    cursor.execute('update users set password=%s where email=%s',[newpassword,email])
                    mydb.commit()
                    flash('Reset Successful')
                    return redirect(url_for('login'))
                finally:
                    if mydb.is_connected():
                        mydb.close()
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')

@app.route('/logout')
def logout():
    if session.get('username'):
        session.pop('username')
        flash('Successfully logged out')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))



@app.route('/')
def home():
    if session.get('username'):
        # Remove items from session
        session.pop('uploaded_filename', None)
        session.pop('detection_filename', None)
        session.pop('detected_objects', None)
        session.pop('ocr_text', None)
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/index')
def index():
    if session.get('username'): 
        uploaded_filename = session.get('uploaded_filename', '')
        detection_filename = session.get('detection_filename', '')
        detected_objects = session.get('detected_objects', [])
        counts = session.get('value_counts')

        unique_objects, unique_tags = get_unique_objects_and_tags()
        return render_template('index.html', uploaded_filename=uploaded_filename, detection_filename=detection_filename, detected_objects=detected_objects, unique_objects=unique_objects,counts=counts )
    else:
        return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload_image():
    if session.get('username'):
        if 'file' not in request.files:
            return redirect(url_for('home'))
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return redirect(url_for('home'))
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        session['uploaded_filename'] = filename
        session.pop('detection_filename', None)
        session.pop('detected_objects', None)
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/detect',methods=['GET','POST'])
def detect_objects():
    if session.get('username'):
        filename = session.get('uploaded_filename', '')
        if not filename:
            return redirect(url_for('home'))
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        frame = cv2.imread(file_path)
        results = model.predict(frame)
        detections = results[0].boxes.data
        detected_objects = []
        tags = []
        print(detections)
        d = pd.DataFrame(detections).astype("float")
        d[5] = [class_list[int(index)] for index in d[5]]
        counts = dict(d[5].value_counts().items())
        print(counts)
        print(list(pd.DataFrame(detections).astype("float").iterrows()))
        for index, row in pd.DataFrame(detections).astype("float").iterrows():
            x1, y1, x2, y2, conf, class_id = map(float, row)
            label = class_list[int(class_id)]
            print(int(conf),int(conf * 100))
            tags.append(label)
            detected_objects.append({'label': label, 'confidence': int(conf*100), 'coordinates': (int(x1), int(y1), int(x2), int(y2))})
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(frame, f'{label} ({int(conf*100)}%)', (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)   
        detection_filename = 'detected_' + filename
        print(detected_objects)
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], detection_filename), frame)
        save_objects(detection_filename, detected_objects, tags)
        session['detection_filename'] = detection_filename
        session['detected_objects'] = detected_objects
        session['value_counts'] = counts
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
