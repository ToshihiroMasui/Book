from flask import Flask #flask使用
from flask import render_template, request , redirect #htmlテンプレート機能を使用
from flask_sqlalchemy import SQLAlchemy #DB作成およびSQL操作のため

from crypt import methods #パスワードの検証
from email.policy import default #メールアドレス
from enum import unique #一意の値 usernameに使用
from venv import create
from matplotlib.pyplot import title


from flask_login import UserMixin,LoginManager, login_user,logout_user, login_required #ログイン機能
from werkzeug.security import generate_password_hash,check_password_hash #パスワードハッシュ化とチェック
import os
from flask_bootstrap import Bootstrap #ブートストラップ

from datetime import datetime #時間
import pytz #タイムゾーン設定

import requests #ISBN 書籍情報
import xml.etree.ElementTree as et 

import cv2  #カメラ情報

from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
import re
import numpy as np
import math

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin,db.Model): #userテーブル作成
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique = True)
    password = db.Column(db.String(12))

class Book(db.Model): #Bookテーブル作成
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique = True)
    creator = db.Column(db.String(15))
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    

@app.route("/")
def index():
    books = Book.query.all()
    return render_template('index.html', books=books)


@app.route("/signup",methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User(username = username, password = generate_password_hash(password, method='sha256'))

        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template('signup.html')

@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')
    else:
        return render_template('login.html')

@app.route('/logout')
#@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == "POST":
        title = request.form.get('title')
        creator = request.form.get('creator')
        # インスタンスを作成
        book = Book(title=title, creator=creator)
        db.session.add(book)
        db.session.commit()
        return redirect('/')
    else:
        return render_template('create.html')

@app.route("/<int:id>/delete",methods=['GET'])
def delete(id):
    book = Book.query.get(id)

    db.session.delete(book)
    db.session.commit()
    
    return redirect('/')


@app.route('/isbn', methods=['GET', 'POST'])
def fetch_book_data():
    if request.method == 'POST':
        isbn = request.form.get('isbn')
        endpoint = 'https://iss.ndl.go.jp/api/sru'
        params = {'operation': 'searchRetrieve',
                'query': f'isbn="{isbn}"',
                'recordPacking': 'xml'}
        res = requests.get(endpoint, params=params)

        root = et.fromstring(res.text)
        ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
        title = root.find('.//dc:title', ns).text
        creator = root.find('.//dc:creator', ns).text

        book = Book(title=title, creator=creator)
        db.session.add(book)
        db.session.commit()
        return redirect('/')

    else: 
        return render_template('isbn.html')



@app.route('/camera', methods=['GET'])
def contrast(image, a):
    lut = [ np.uint8(255.0 / (1 + math.exp(-a * (i - 128.) / 255.))) for i in range(256)]
    result_image = np.array( [ lut[value] for value in image.flat], dtype=np.uint8 )
    result_image = result_image.reshape(image.shape)
    return result_image
       
def convert_image_to_code():
    capture = cv2.VideoCapture(0) # カメラ番号を選択、例えば　capture = cv2.VideoCapture(1)
    if capture.isOpened() is False:
        raise("IO Error")
    cv2.namedWindow("Capture", cv2.WINDOW_AUTOSIZE)
    isbnNumber = ""
    while True:
        ret, image = capture.read()
        image_mirror = image[:,::-1]
        if ret == False:
            continue
        # GrayScale
        imageGlay = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = contrast(imageGlay, 5)

        # Show image
        cv2.imshow("Capture", image_mirror )

        allCodes = decode(image, symbols=[ZBarSymbol.EAN13])

        if len(allCodes) > 0: # Barcode was detected
            for code in allCodes:
                codesStr = str(code)
                isbnPattern = r"9784\d+"
                isbnSearchOB = re.search(isbnPattern,codesStr)
                if isbnSearchOB: # ISBN was detected
                    if isbnNumber != isbnSearchOB.group(): # New ISBN was detected
                        isbnNumber = isbnSearchOB.group()
                        capture.release()
                        cv2.destroyAllWindows()
                        return isbnNumber

        keyInput = cv2.waitKey(3) # 撮影速度 大きくなると遅くなる
        if keyInput == 27: # when ESC
            break

if __name__ == '__main__':

    code = convert_image_to_code()