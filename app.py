# from re import search
from flask import Flask #flask使用
from flask import render_template, request , redirect,session #htmlテンプレート機能を使用
from flask_sqlalchemy import SQLAlchemy#DB作成およびSQL操作のため
from sqlalchemy import or_
from crypt import methods #パスワードの検証
from email.policy import default #メールアドレス
from enum import unique #一意の値 usernameに使用
from venv import create
from matplotlib.pyplot import title
from flask_login import UserMixin,LoginManager, login_user,logout_user, login_required #ログイン機能
from werkzeug.security import generate_password_hash,check_password_hash #パスワードハッシュ化とチェック
import os
from datetime import datetime,timedelta #時間

import pytz #タイムゾーン設定
import requests #ISBN 書籍情報
import xml.etree.ElementTree as et 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book.db'
app.config['SECRET_KEY'] = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=3)
app.config['ITEMS_PER_PAGE'] = 5
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin,db.Model): #userテーブル作成
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique = True)
    password = db.Column(db.String(12))

class Book(db.Model): #Bookテーブル作成
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.BIGINT, )
    asin = db.Column(db.BIGINT, )
    title = db.Column(db.String(50), )
    creator = db.Column(db.String(15))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/") 
def top():
    return render_template('top.html')

@app.route("/index",methods=['GET','POST'])
def index():
    search_title = request.form.get('search_title')
    if request.method == 'POST':
        if search_title != "":
            session['title'] = search_title
            books = db.session.query(Book).filter(or_(Book.title.like('%' + search_title + '%'),Book.creator.like('%' + search_title + '%')))
            books = books.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
            
        else:
            books = Book.query.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
            
    else:
        session.pop('title', None)
        books = Book.query.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
    return render_template('index.html', books=books,search_title = search_title)



@app.route('/pages/<int:page_num>', methods=['GET','POST'])
def index_pages(page_num):
    if "title" in session:
        search_title  = session['title']
        books = db.session.query(Book).filter(or_(Book.title.like('%' + search_title + '%'),Book.creator.like('%' + search_title + '%')))
        books = books.paginate(page_num, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
    
    else:
        books = Book.query.paginate(page=page_num, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
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
            return redirect('/index')
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
        return redirect('/index')
    else:
        return render_template('create.html')

@app.route("/<int:id>/update",methods=['GET','POST'])
def update(id):
    book = Book.query.get(id)
    if request.method == "GET":
        return render_template('update.html',book=book)
    else:
        book.title = request.form.get('title')
        book.creator = request.form.get('creator')
        db.session.commit()
        return redirect('/index')


@app.route("/<int:id>/delete",methods=['GET'])
def delete(id):
    book = Book.query.get(id)

    db.session.delete(book)
    db.session.commit()
    
    return redirect('/index')


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
        if root.find('.//dc:title', ns) != None:

            title = root.find('.//dc:title', ns).text
            creator = root.find('.//dc:creator', ns).text
            creator = creator.replace("著","")

            asin = jan_to_asin(isbn)
            book = Book(title=title, creator=creator,isbn=isbn,asin=asin)
            db.session.add(book)
            db.session.commit()
            return redirect('/index') 
        else: 
            return render_template('isbn.html')
    else: 
        return render_template('isbn.html')


    

        


def jan_to_asin(jan13):
    s = str(jan13)[3:12]
    a = 10
    c = 0
   
    for i in range(0, len(s)):
        c += int(s[i]) *(a-i)

    d = c % 11
    d = 11 - d 
    if d == 10:
        d = "X"
    return str(s) + str(d)