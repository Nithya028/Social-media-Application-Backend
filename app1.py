import os
from flask import Flask, render_template, request, redirect, session
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Connect to the SQLite database
engine = create_engine('sqlite:///testdb.db')
Base = declarative_base()

# Define the User model
from sqlalchemy import Column, String, Date  # Import Date data type

class User(Base):
    __tablename__ = 'newuser'
    username = Column(String, primary_key=True)
    password = Column(String)
    birthday = Column(Date)  # Use Date data type for birthday
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)

# Define the Post model
from sqlalchemy import Column, Integer, String

class Post(Base):
    __tablename__ = 'poster'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    caption = Column(String)  # Add the caption field
    content = Column(String)
    content_type = Column(String)  # Assuming this field determines the type of content (image or video)
    user_id = Column(String)  # Store the user's ID who created the post 
    phone_number = Column(String)  # Add phone_number column

Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
db_session = Session()

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Query the database for the user
        user = db_session.query(User).filter_by(username=username, password=password).first()
        
        # Check if user exists and passwords match
        if user:
            session['username'] = username  # Mark user as logged in
            return redirect('/home')  # Redirect to home page
        else:
            return render_template('login.html', message='Invalid username or password')
    else:
        return render_template('login.html')


@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        
        # Query the database for user information
        user = db_session.query(User).filter_by(username=username).first()
        
        if user:
            # Fetch user's additional details from the database
            user_details = db_session.query(User).filter_by(username=username).first()
            
            if user_details:
                first_name = user_details.first_name
                last_name = user_details.last_name
                phone_number = user_details.phone_number
            else:
                # Set default values if details are not found
                first_name = ""
                last_name = ""
                phone_number = ""
            
            # Fetch user's posts from the database
            posts = db_session.query(Post).filter_by(user_id=user.username).all()
            
            return render_template('profile.html', user=user, first_name=first_name, last_name=last_name, phone_number=phone_number, posts=posts)
        else:
            return render_template('error.html', message='User not found')
    else:
        return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' in session:
        if request.method == 'POST':
            new_username = request.form['username']
            new_first_name = request.form['first_name']
            new_last_name = request.form['last_name']
            new_phone_number = request.form['phone_number']
            
            # Get the current username from the session
            current_username = session['username']
            
            # Query the database for the user
            user = db_session.query(User).filter_by(username=current_username).first()
            
            if user:
                # Update the user's information
                user.username = new_username
                user.first_name = new_first_name
                user.last_name = new_last_name
                user.phone_number = new_phone_number
                db_session.commit()
                
                # Update the username in the session
                session['username'] = new_username
                
                # Update the username in the Post table
                posts = db_session.query(Post).filter_by(user_id=current_username).all()
                for post in posts:
                    post.user_id = new_username
                db_session.commit()
                
                return redirect('/profile')
            else:
                return render_template('error.html', message='User not found')
        else:
            # If it's a GET request, render the edit_profile.html template with the user's current information
            current_username = session['username']
            user = db_session.query(User).filter_by(username=current_username).first()
            return render_template('edit_profile.html', user=user)
    else:
        return redirect('/login')


@app.route('/home')
def home():
    if 'username' in session:
        search_query = request.args.get('q')  # Get the search query from the URL parameters
        if search_query:
            # If there is a search query, filter posts by the username
            posts = db_session.query(Post).filter(Post.user_id != session['username'], Post.user_id == search_query).all()
        else:
            # If no search query provided, display all posts except the logged-in user's posts
            posts = db_session.query(Post).filter(Post.user_id != session['username']).all()
        return render_template('l.html', posts=posts)
    else:
        return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        

# Convert the birthday string to a Python date object
        birthday = datetime.strptime(request.form['birthday'], '%Y-%m-%d').date()
        first_name = request.form['first_name']  
        last_name = request.form['last_name']  
        phone_number = request.form['phone_number'] 
        
        # Check if password and confirm_password match
        if password != confirm_password:
            return render_template('register.html', message='Passwords do not match', username=username, birthday=birthday, first_name=first_name, last_name=last_name, phone_number=phone_number)

        # Check if the username is already taken
        if db_session.query(User).filter_by(username=username).first():
            return render_template('register.html', message='Username already taken', birthday=birthday, first_name=first_name, last_name=last_name, phone_number=phone_number)

        # Create a new user and add it to the database
        new_user = User(username=username, password=password, birthday=birthday, first_name=first_name, last_name=last_name, phone_number=phone_number)
        db_session.add(new_user)
        db_session.commit()

        # Redirect the user to the home page after successful registration
        return redirect('/home')
    else:
        return render_template('register.html')
@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if 'username' in session:
        if request.method == 'POST':
            username = session['username']
            title = request.form['title']
            caption = request.form['caption']
            post_type = request.form['post_type']
            
            file = request.files['file']
            
            user = db_session.query(User).filter_by(username=username).first()
            
            if file:
                filename = file.filename
                file.save(os.path.join(app.instance_path, filename))
                file_path = os.path.join(app.instance_path, filename)
            else:
                file_path = None
            
            new_post = Post(title=title, caption=caption, content=file_path, content_type=post_type, user_id=user.username)  # Include phone_number
            db_session.add(new_post)
            db_session.commit()
            
            return redirect('/profile')
        else:
            return render_template('add_post.html')
    else:
        return redirect('/login')
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'username' in session:
        if request.method == 'POST':
            username = session['username']
            new_title = request.form['title']
            new_caption = request.form['caption']
            new_post_type = request.form['post_type']
            file = request.files['file']
            post = db_session.query(Post).filter_by(id=post_id, user_id=username).first()
            if post:
                post.title = new_title
                post.caption = new_caption
                post.content_type = new_post_type
                if file:
                    filename = file.filename
                    file.save(os.path.join(app.instance_path, filename))
                    post.content = os.path.join(app.instance_path, filename)
                db_session.commit()
                return redirect('/profile')
            else:
                return render_template('error.html', message='Post not found or you are not authorized to edit it.')
        else:
            username = session['username']
            post = db_session.query(Post).filter_by(id=post_id, user_id=username).first()
            if post:
                return render_template('edit_post.html', post=post)
            else:
                return render_template('error.html', message='Post not found or you are not authorized to edit it.')
    else:
        return redirect('/login')
@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    if 'username' in session:
        username = session['username']
        post = db_session.query(Post).filter_by(id=post_id, user_id=username).first()
        if post:
            db_session.delete(post)
            db_session.commit()
            return redirect('/profile')
        else:
            return render_template('error.html', message='Post not found or you are not authorized to delete it.')
    else:
        return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
