from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configure the Azure SQL Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://joshikacc:5joshika5##@bookstorejoshika.database.windows.net:1433/bookstoredatabase?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Define the Book model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(100), nullable=False)

# Create the database and the table
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    filtered_books = Book.query.filter(Book.title.ilike(f'%{search_query}%')).all()
    return render_template('index.html', books=filtered_books, search_query=search_query)

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        price = request.form['price']
        stock = request.form['stock']

        if 'image' not in request.files:
            return 'No file part'
        file = request.files['image']
        if file.filename == '':
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            new_book = Book(
                title=title,
                author=author,
                price=float(price),
                stock=int(stock),
                image=filename
            )
            db.session.add(new_book)
            db.session.commit()

            return redirect(url_for('index'))
    
    return render_template('add_book.html')

@app.route('/update/<int:book_id>', methods=['GET', 'POST'])
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.price = request.form['price']
        book.stock = request.form['stock']

        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    book.image = filename

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('update_book.html', book=book)

@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/rent/<int:book_id>', methods=['GET', 'POST'])
def rent_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        if book.stock > 0:
            try:
                book.stock -= 1
                db.session.commit()
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                return f"An error occurred: {str(e)}", 500
        else:
            return 'Book out of stock', 400
    return render_template('rent_book.html', book=book)

if __name__ == '__main__':
    app.run(debug=True)