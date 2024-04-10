# app.py
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    club = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)


class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_name = db.Column(db.Text, unique=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    about = db.Column(db.Text)
    description = db.Column(db.Text)
    location = db.Column(db.Text)


class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)


class Meetings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_date = db.Column(db.Text)
    meeting_time = db.Column(db.Text)
    meeting_duration = db.Column(db.Text)
    meeting_link = db.Column(db.Text)
    meeting_location = db.Column(db.Text)
    note = db.Column(db.Text)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)


class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    author = db.Column(db.Text)
    summary = db.Column(db.Text)
    imageUrl = db.Column(db.Text)
    pages = db.Column(db.Integer)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)


class CurrentlyReadingBook(db.Model):
    __tablename__ = 'CurrentlyReadingBook'
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)


class RatingsAndReviews(db.Model):
    __tablename__ = 'ratingsAndReviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    review = db.Column(db.Text)


class RecomendedBooks(db.Model):
    __tablename__ = 'recomendedBooks'
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Check if the user with the given username or email already exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)).first()

    if existing_user:
        return jsonify({"message": "User already exists"}), 400

    # If user doesn't exist, proceed with registration
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = User(username=username, email=email, password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password, password):
        user_details = {
            "id": user.id,
            "username": user.username,
            "email": user.email,

            # Add more user details as needed
        }
        return jsonify({"message": "Login successful", "user": user_details}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401


@app.route('/users/<int:userId>', methods=['GET'])
def get_user(userId):
    user = User.query.get(userId)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user_info = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'club': user.club,
    }
    return jsonify({'user_info': user_info}), 200


@app.route('/createclub', methods=['POST'])
def create_club():
    data = request.get_json()
    club_name = data.get('club_name')

    if not club_name:
        return jsonify({'error': 'Missing required field: club_name'}), 400

    # Check if the club name already exists
    existing_club = Club.query.filter_by(club_name=club_name).first()
    if existing_club:
        return jsonify({'error': 'Club name already exists'}), 400

    admin_id = data.get('admin_id')
    user = User.query.get(admin_id)

    if not user:
        return jsonify({'error': 'Invalid admin_id'}), 400

    club = Club(club_name=club_name, admin_id=user.id)
    db.session.add(club)
    db.session.commit()

    # Update the Members table
    new_member = Members(user_id=user.id, club_id=club.id)
    db.session.add(new_member)
    db.session.commit()

    return jsonify({'message': 'Club created successfully'}), 201


@app.route('/clubs/<string:club_name>/join', methods=['POST'])
def join_club(club_name):
    user_id = request.get_json().get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    user = User.query.get(user_id)
    club = Club.query.filter_by(club_name=club_name).first()
    if not user or not club:
        return jsonify({'error': 'Invalid user_id or club name'}), 400

    # Update the Members table
    new_member = Members(user_id=user.id, club_id=club.id)
    db.session.add(new_member)
    db.session.commit()

    return jsonify({'message': 'Joined club successfully'}), 200


@app.route('/clubs/<string:club_name>', methods=['GET'])
def get_club_info(club_name):
    club = Club.query.filter_by(club_name=club_name).first()

    if not club:
        return jsonify({'error': 'Club not found'}), 404

    meetings = Meetings.query.filter_by(club_id=club.id).all()

    # Get club information
    club_info = {
        'club_name': club.club_name,
        'about': club.about,
        'description': club.description,
        'location': club.location,
        'meetings': [{
            'meeting_date': meeting.meeting_date,
            'meeting_time': meeting.meeting_time,
            'meeting_duration': meeting.meeting_duration,
            'meeting_link': meeting.meeting_link,
            'meeting_location': meeting.meeting_location,
            'note': meeting.note
        } for meeting in meetings],
        'admin': {
            'admin_id': club.admin_id,
            'admin_username': User.query.get(club.admin_id).username,
        },
    }

    # Get regular members information
    members_info = []
    members = Members.query.filter_by(club_id=club.id).all()

    for member in members:
        if member.user_id != club.admin_id:  # Exclude admin from members
            user = User.query.get(member.user_id)
            members_info.append({
                'user_id': user.id,
                'username': user.username,
            })

    club_info['members'] = members_info

    # Get Currently Reading Books
    currently_reading_books = (
        db.session.query(Books)
        .join(CurrentlyReadingBook, CurrentlyReadingBook.book_id == Books.id)
        .filter(CurrentlyReadingBook.club_id == club.id)
        .all()
    )

    club_info['currently_reading_books'] = [{
        'title': book.title,
        'author': book.author,
        'summary': book.summary,
        'imageUrl': book.imageUrl,
        'pages': book.pages,
        'ratings_and_reviews': [{
            'user_id': rating.user_id,
            'username': User.query.get(rating.user_id).username,
            'rating': rating.rating,
            'review': rating.review,
        } for rating in RatingsAndReviews.query.filter_by(book_id=book.id).all()],
    } for book in currently_reading_books]

    # Get Recommended Books
    recommended_books = (
        db.session.query(Books)
        .join(RecomendedBooks, RecomendedBooks.book_id == Books.id)
        .filter(RecomendedBooks.club_id == club.id)
        .all()
    )

    club_info['recommended_books'] = [{
        'title': book.title,
        'author': book.author,
        'summary': book.summary,
        'imageUrl': book.imageUrl,
        'pages': book.pages,
    } for book in recommended_books]

    return jsonify({'club_info': club_info}), 200


@app.route('/clubs/<string:club_name>/meetings', methods=['POST'])
def create_meeting(club_name):
    data = request.get_json()
    meeting_date = data.get('meeting_date')

    if not meeting_date:
        return jsonify({'error': 'Missing required field: meeting_date'}), 400

    club = Club.query.filter_by(club_name=club_name).first()

    if not club:
        return jsonify({'error': 'Club not found'}), 404

    new_meeting = Meetings(meeting_date=meeting_date,
                           meeting_time=data.get('meeting_time'),
                           meeting_duration=data.get('meeting_duration'),
                           meeting_link=data.get('meeting_link'),
                           meeting_location=data.get('meeting_location'),
                           note=data.get('note'),
                           club_id=club.id)

    db.session.add(new_meeting)
    db.session.commit()

    return jsonify({'message': 'Meeting created successfully'}), 201


@app.route('/clubs/<string:club_name>/books', methods=['POST'])
def post_book(club_name):
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    summary = data.get('summary')
    imageUrl = data.get('imageUrl')
    pages = data.get('pages')

    if not title:
        return jsonify({'error': 'Missing required field: title'}), 400

    club = Club.query.filter_by(club_name=club_name).first()

    if not club:
        return jsonify({'error': 'Club not found'}), 404

    new_book = Books(title=title, author=author, summary=summary,
                     imageUrl=imageUrl, pages=pages, club_id=club.id)
    db.session.add(new_book)
    db.session.commit()

    return jsonify({'message': 'Book added successfully'}), 201


@app.route('/clubs/<string:club_name>/currently-reading', methods=['POST'])
def post_currently_reading_book(club_name):
    data = request.get_json()
    book_id = data.get('book_id')

    if not book_id:
        return jsonify({'error': 'Missing required field: book_id'}), 400

    club = Club.query.filter_by(club_name=club_name).first()

    if not club:
        return jsonify({'error': 'Club not found'}), 404

    book = Books.query.get(book_id)

    if not book:
        return jsonify({'error': 'Book not found'}), 404

    new_currently_reading_book = CurrentlyReadingBook(
        club_id=club.id, book_id=book.id)
    db.session.add(new_currently_reading_book)
    db.session.commit()

    return jsonify({'message': 'Book added to currently reading list successfully'}), 201


@app.route('/clubs/<string:club_name>/recomended-books', methods=['POST'])
def post_recommended_book(club_name):
    data = request.get_json()
    book_id = data.get('book_id')

    if not book_id:
        return jsonify({'error': 'Missing required field: book_id'}), 400

    club = Club.query.filter_by(club_name=club_name).first()

    if not club:
        return jsonify({'error': 'Club not found'}), 404

    book = Books.query.get(book_id)

    if not book:
        return jsonify({'error': 'Book not found'}), 404

    new_recommended_book = RecomendedBooks(
        club_id=club.id, book_id=book.id, user_id=club.admin_id)
    db.session.add(new_recommended_book)
    db.session.commit()

    return jsonify({'message': 'Book added to recommended list successfully'}), 201


@app.route('/clubs/<string:club_name>/ratings-reviews', methods=['POST'])
def post_rating_and_review(club_name):
    data = request.get_json()
    user_id = data.get('user_id')
    rating = data.get('rating')
    book_id = data.get('book_id')
    review = data.get('review')

    club = Club.query.filter_by(club_name=club_name).first()

    if not club:
        return jsonify({'error': 'Club not found'}), 404

    user = User.query.get(user_id)
    book = Books.query.get(book_id)

    if not user or not book:
        return jsonify({'error': 'User or Book not found'}), 404

    new_rating_and_review = RatingsAndReviews(
        user_id=user.id,
        rating=rating,
        book_id=book.id,
        review=review
    )

    db.session.add(new_rating_and_review)
    db.session.commit()

    return jsonify({'message': 'Rating and review added successfully'}), 201


@app.route('/user/<int:user_id>/is-in-club', methods=['GET'])
def is_user_in_any_club(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Check if the user is a member of any club
    membership = Members.query.filter_by(user_id=user.id).first()

    if membership:
        return jsonify({'is_in_club': True, 'club_id': membership.club_id}), 200
    else:
        return jsonify({'is_in_club': False}), 200


@app.route('/clubs/<int:club_id>', methods=['GET'])
def get_club_by_id(club_id):
    club = Club.query.get(club_id)

    if not club:
        return jsonify({'error': 'Club not found'}), 404

    # Get admin details
    admin = User.query.get(club.admin_id)
    admin_details = {
        'admin_id': admin.id,
        'admin_username': admin.username,
    }

    # Get members details
    members_info = []
    members = Members.query.filter_by(club_id=club_id).all()
    for member in members:
        user = User.query.get(member.user_id)
        members_info.append({
            'user_id': user.id,
            'username': user.username,
        })

    # Get meetings details
    meetings_info = []
    meetings = Meetings.query.filter_by(club_id=club_id).all()
    for meeting in meetings:
        meetings_info.append({
            'meeting_date': meeting.meeting_date,
            'meeting_time': meeting.meeting_time,
            'meeting_duration': meeting.meeting_duration,
            'meeting_link': meeting.meeting_link,
            'meeting_location': meeting.meeting_location,
            'note': meeting.note,
        })

    # Get currently reading books details
    currently_reading_books_info = []
    currently_reading_books = CurrentlyReadingBook.query.filter_by(
        club_id=club_id).all()
    for cr_book in currently_reading_books:
        book = Books.query.get(cr_book.book_id)
        ratings_and_reviews_info = []
        ratings_and_reviews = RatingsAndReviews.query.filter_by(
            book_id=book.id).all()
        for rating_review in ratings_and_reviews:
            user = User.query.get(rating_review.user_id)
            ratings_and_reviews_info.append({
                'user_id': user.id,
                'username': user.username,
                'rating': rating_review.rating,
                'review': rating_review.review,
            })
        currently_reading_books_info.append({
            'title': book.title,
            'author': book.author,
            'summary': book.summary,
            'imageUrl': book.imageUrl,
            'pages': book.pages,
            'ratings_and_reviews': ratings_and_reviews_info,
        })

    # Get recommended books details
    recommended_books_info = []
    recommended_books = RecomendedBooks.query.filter_by(club_id=club_id).all()
    for rec_book in recommended_books:
        book = Books.query.get(rec_book.book_id)
        recommended_books_info.append({
            'title': book.title,
            'author': book.author,
            'summary': book.summary,
            'imageUrl': book.imageUrl,
            'pages': book.pages,
        })

    club_info = {
        'club_name': club.club_name,
        'about': club.about,
        'description': club.description,
        'location': club.location,
        'admin': admin_details,
        'members': members_info,
        'meetings': meetings_info,
        'currently_reading_books': currently_reading_books_info,
        'recommended_books': recommended_books_info,
    }

    return jsonify({'club_info': club_info}), 200


if __name__ == '__main__':
    app.run(debug=True)
