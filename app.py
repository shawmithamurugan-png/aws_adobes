
print("APP.PY IS EXECUTING")

from flask import Flask, render_template, request, redirect, url_for, session
import os
import boto3
import bcrypt
from werkzeug.utils import secure_filename
from datetime import datetime

bookings = []

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


# DynamoDB table name (MUST match AWS exactly)
TABLE_NAME = 'Users'

# DynamoDB connection
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1'
)
table = dynamodb.Table('Table_Name')

# Configuration for File Uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory database (dictionary)
users = {}
admin_users = {}
projects = []  # List of dictionaries: {'id': 1, 'title': '...', 'desc': '...', 'image': '...', 'doc': '...'}
enrollments = {} # Dictionary: {'username': [project_id_1, project_id_2]}


@app.route('/')
def index():

    hotels = [
    {"name": "Grand Chennai Suites", "location": "Chennai", "price": 7500, "rating": 4.8, "image": "images/img3.jpg"},
    {"name": "Beach View Chennai", "location": "Chennai", "price": 9000, "rating": 4.9, "image": "images/img4.jpg"},

    {"name": "Bangalore Palace Hotel", "location": "Bangalore", "price": 5800, "rating": 4.6, "image": "images/img5.jpg"},
    {"name": "City Comfort Inn Bangalore", "location": "Bangalore", "price": 74200, "rating": 4.8, "image": "images/img6.jpg"},
    {"name": "Silicon Valley Stay Bangalore", "location": "Bangalore", "price": 6800, "rating": 4.1, "image": "images/img7.jpg"},

    {"name": "Comfort Inn Delhi", "location": "Delhi", "price": 7900, "rating": 4.0, "image": "images/img8.jpg"},
    {"name": "Goa Cozy Cottage Delhi", "location": "Delhi", "price": 6200, "rating": 4.0, "image": "images/img9.jpg"},

    {"name": "Ocean View Resort Mumbai", "location": "Mumbai", "price": 6500, "rating": 4.9, "image": "images/img10.jpg"},
    {"name": "City Lights Hotel Mumbai", "location": "Mumbai", "price": 7000, "rating": 4.5, "image": "images/img11.jpg"},

    {"name": "Kochi Riverside Hotel Hyderabad", "location": "Hyderabad", "price": 7800, "rating": 4.7, "image": "images/pune.jpg"},
    {"name": "Kochi Budget Stay Hyderabad", "location": "Hyderabad", "price": 8500, "rating": 3.8, "image": "images/goa.jpg"},
]


    # 🔹 Read filters from URL
    place= request.args.get('place')
    price = request.args.get('price')
    rating = request.args.get('rating')

    filtered_hotels = hotels

    # 🔹 place filter
    if place:
        filtered_hotels = [h for h in filtered_hotels if h['location'] == place]

    # 🔹 Price sorting
    if price == 'low':
        filtered_hotels = sorted(filtered_hotels, key=lambda x: x['price'])
    elif price == 'high':
        filtered_hotels = sorted(filtered_hotels, key=lambda x: x['price'], reverse=True)

    # 🔹 Rating filter
    if rating == 'high':
        filtered_hotels = [h for h in filtered_hotels if h['rating'] >= 4.0]
    elif rating == 'low':
        filtered_hotels = [h for h in filtered_hotels if h['rating'] < 4.0]

    return render_template("index.html", hotels=filtered_hotels)


@app.route('/hotel/<hotel_name>', endpoint='hotel_details_page')
def hotel_details_page(hotel_name):
    if 'email' not in session:
        return redirect(url_for('login'))

    hotels = {
        "Blissful Sea View Resort": {
            "location": "Goa",
            "price": "₹4,500 / night",
            "description": "A luxury seaside resort with breathtaking ocean views.",
            "food": "Seafood, Continental, Indian",
            "amenities": [
                "Free Wi-Fi",
                "Swimming Pool",
                "Beach Access",
                "Spa",
                "24/7 Room Service"
            ]
        },
        "Mountain Bliss Retreat": {
            "location": "Ooty",
            "price": "₹3,800 / night",
            "description": "A peaceful mountain retreat surrounded by lush greenery.",
            "food": "South Indian, North Indian",
            "amenities": [
                "Free Wi-Fi",
                "Mountain View",
                "Bonfire",
                "Restaurant",
                "Parking"
            ]
        },
        "Royal Palace Stay": {
            "location": "Jaipur",
            "price": "₹5,200 / night",
            "description": "Experience royal heritage with modern luxury.",
            "food": "Rajasthani, Mughlai, Continental",
            "amenities": [
                "Free Wi-Fi",
                "Heritage Rooms",
                "Cultural Events",
                "Swimming Pool",
                "Fine Dining"
            ]
        }
    }

    hotel = hotels.get(hotel_name)
    if not hotel:
        return "Hotel not found"

    return render_template(
        'hotel_details.html',
        name=hotel_name,
        hotel=hotel
    )



@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/debug-users')
def debug_users():
    return users

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # 🔐 HASH PASSWORD
        hashed_pw = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        )

        table.put_item(Item={
            'email': email,
            'password': hashed_pw.decode('utf-8')
        })

        session['email'] = email
        return redirect(url_for('dashboard'))

    return render_template('signup.html')


@app.route('/book/<hotel_name>', methods=['GET', 'POST'])
def book_hotel(hotel_name):
    if 'username' not in session:
        return redirect(url_for('login'))

    hotel = next((h for h in hotels if h['name'] == hotel_name), None)

    if request.method == 'POST':
        booking = {
            "booking_id": len(bookings) + 1,
            "username": session['username'],
            "hotel_name": hotel['name'],
            "location": hotel['location'],
            "price": hotel['price'],
            "check_in": request.form['check_in'],
            "check_out": request.form['check_out'],
            "guests": request.form['guests'],
            "status": "Confirmed",
            "booked_on": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        bookings.append(booking)
        return redirect(url_for('my_bookings'))

    return render_template('book.html', hotel=hotel)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        response = table.get_item(Key={'email': email})

        if 'Item' in response:
            stored_hash = response['Item']['password']

            if bcrypt.checkpw(
                password.encode('utf-8'),
                stored_hash.encode('utf-8')
            ):
                session['email'] = email
                return redirect(url_for('dashboard'))

        return "Invalid email or password"

    return render_template('login.html')

@app.route('/payment-success/<hotel_name>')
def payment_success(hotel_name):
    return render_template('payment_success.html', hotel_name=hotel_name)

@app.route('/payment/<hotel_name>', methods=['GET', 'POST'])
def payment(hotel_name):
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        return redirect(url_for('payment_success', hotel_name=hotel_name))

    return render_template('payment.html', hotel_name=hotel_name)


@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        user_enrollments_ids = enrollments.get(username, [])

        # Filter projects to get full details of enrolled ones
        my_projects = [p for p in projects if p['id'] in user_enrollments_ids]

        return render_template('home.html', username=username, my_projects=my_projects)
    return redirect(url_for('login'))

@app.route('/projects')
def projects_list():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user_enrollments_ids = enrollments.get(username, [])

    return render_template('projects_list.html', projects=projects, user_enrollments=user_enrollments_ids)

@app.route('/enroll/<int:project_id>')
def enroll(project_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    if username not in enrollments:
        enrollments[username] = []

    if project_id not in enrollments[username]:
        enrollments[username].append(project_id)

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# Admin Routes
@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in admin_users:
            return "Admin already exists!"

        admin_users[username] = password
        return redirect(url_for('admin_login'))
    return render_template('admin_signup.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in admin_users and admin_users[username] == password:
            session['admin'] = username
            return redirect(url_for('admin_dashboard'))
        return "Invalid admin credentials!"
    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html')



@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html', username=session['admin'], projects=projects, users=users, enrollments=enrollments)

@app.route('/admin/create-project', methods=['GET', 'POST'])
def admin_create_project():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        title = request.form['title']
        problem_statement = request.form['problem_statement']
        solution_overview = request.form['solution_overview']

        # Handle File Uploads
        image = request.files['image']
        document = request.files['document']

        image_filename = None
        doc_filename = None

        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        if document:
            doc_filename = secure_filename(document.filename)
            document.save(os.path.join(app.config['UPLOAD_FOLDER'], doc_filename))

        # Create Project ID (simple auto-increment)
        project_id = len(projects) + 1

        new_project = {
            'id': project_id,
            'title': title,
            'problem_statement': problem_statement,
            'solution_overview': solution_overview,
            'image': image_filename,
            'document': doc_filename
        }

        projects.append(new_project)
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_create_project.html', username=session['admin'])

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)