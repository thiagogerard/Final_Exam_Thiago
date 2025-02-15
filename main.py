from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    borrowed_books = db.relationship('Borrow', backref='user', lazy=True)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    books = db.relationship('Book', backref='author', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    borrows = db.relationship('Borrow', backref='book', lazy=True)

class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'User with this email already exists'}), 400
    user = User(name=name, email=email)
    db.session.add(user)
    db.session.commit()
    return jsonify({
        'message': 'User created',
        'user': {'id': user.id, 'name': user.name, 'email': user.email}
    }), 201

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    output = [{'id': user.id, 'name': user.name, 'email': user.email} for user in users]
    return jsonify({'users': output})

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email})

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    if name:
        user.name = name
    if email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({'error': 'Email already in use'}), 400
        user.email = email
    db.session.commit()
    return jsonify({
        'message': 'User updated',
        'user': {'id': user.id, 'name': user.name, 'email': user.email}
    })

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})


@app.route('/authors', methods=['POST'])
def create_author():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    author = Author(name=name)
    db.session.add(author)
    db.session.commit()
    return jsonify({
        'message': 'Author created',
        'author': {'id': author.id, 'name': author.name}
    }), 201

@app.route('/authors', methods=['GET'])
def get_authors():
    authors = Author.query.all()
    output = [{'id': author.id, 'name': author.name} for author in authors]
    return jsonify({'authors': output})

@app.route('/authors/<int:author_id>/books', methods=['GET'])
def get_authors_books(author_id):
    author = Author.query.get(author_id)
    if not author:
        return jsonify({'error': 'Author not found'}), 404
    books = Book.query.filter_by(author_id=author_id).all()
    output = [{'id': book.id, 'title': book.title} for book in books]
    return jsonify({'author': author.name, 'books': output})


@app.route('/books', methods=['POST'])
def create_book():
    data = request.get_json()
    title = data.get('title')
    author_id = data.get('author_id')
    if not title or not author_id:
        return jsonify({'error': 'Title and author_id are required'}), 400
    if not Author.query.get(author_id):
        return jsonify({'error': 'Author not found'}), 404
    book = Book(title=title, author_id=author_id)
    db.session.add(book)
    db.session.commit()
    return jsonify({
        'message': 'Book created',
        'book': {'id': book.id, 'title': book.title, 'author_id': book.author_id}
    }), 201

@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    output = [{'id': book.id, 'title': book.title, 'author_id': book.author_id} for book in books]
    return jsonify({'books': output})

@app.route('/books/author/<int:author_id>', methods=['GET'])
def get_books_by_author(author_id):
    books = Book.query.filter_by(author_id=author_id).all()
    if not books:
        return jsonify({'message': 'No books found for this author'}), 404
    output = [{'id': book.id, 'title': book.title} for book in books]
    return jsonify({'books': output})

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted'})


@app.route('/borrow', methods=['POST'])
def borrow_book():
    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    if not user_id or not book_id:
        return jsonify({'error': 'user_id and book_id are required'}), 400
    if not User.query.get(user_id):
        return jsonify({'error': 'User not found'}), 404
    if not Book.query.get(book_id):
        return jsonify({'error': 'Book not found'}), 404
    borrow = Borrow(user_id=user_id, book_id=book_id, borrow_date=datetime.utcnow())
    db.session.add(borrow)
    db.session.commit()
    return jsonify({
        'message': 'Book borrowed',
        'borrow': {
            'id': borrow.id,
            'user_id': borrow.user_id,
            'book_id': borrow.book_id,
            'borrow_date': borrow.borrow_date.isoformat()
        }
    }), 201

@app.route('/borrow/user/<int:user_id>', methods=['GET'])
def get_borrows_by_user(user_id):
    borrows = Borrow.query.filter_by(user_id=user_id).all()
    if not borrows:
        return jsonify({'message': 'No borrow records found for this user'}), 404
    output = [{
        'id': borrow.id,
        'book_id': borrow.book_id,
        'borrow_date': borrow.borrow_date.isoformat()
    } for borrow in borrows]
    return jsonify({'user_id': user_id, 'borrows': output})

@app.route('/borrow/book/<int:book_id>', methods=['GET'])
def get_borrows_by_book(book_id):
    borrows = Borrow.query.filter_by(book_id=book_id).all()
    if not borrows:
        return jsonify({'message': 'No borrow records found for this book'}), 404
    output = [{
        'id': borrow.id,
        'user_id': borrow.user_id,
        'borrow_date': borrow.borrow_date.isoformat()
    } for borrow in borrows]
    return jsonify({'book_id': book_id, 'borrows': output})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

