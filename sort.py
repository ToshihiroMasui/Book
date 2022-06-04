# if request.method == 'POST':
    #     if request.form.get('sort') == 'asc':
    #         books = db.session.query(Book).order_by(Book.id.asc()).all()
    #     elif request.form.get('sort') == 'desc':
    #         books = db.session.query(Book).order_by(Book.id.desc()).all()
    # else:
    #     books = Book.query.all()
    # return render_template('index.html', books=books)

    # books = Book.query.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
    # return render_template('index.html', books=books) 



# @app.route("/test",methods=['GET','POST'])
# def search():
#     search = request.form.get('search')
#     if not search == "":
#         if request.method == 'POST':
#             books = db.session.query(Book).filter(Book.title.contains(search)).all()
#         else:
#             books = Book.query.all()
#     else:
#         books = Book.query.all()
#     return render_template('test.html', books = books ,search = search)



# books = Book.query.paginate(page=1, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
#     return render_template('index.html', books=books,search = search)