from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', 'postgres')
db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('DB_NAME', 'monzo_clone')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)

# Transactions Model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'deposit' or 'payment'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/deposit')
def deposit_page():
    return render_template('deposit.html')

@app.route('/payment')
def payment_page():
    return render_template('payment.html')

@app.route('/api')
def api_info():
    return jsonify({
        "message": "Welcome to Monzo Clone API",
        "available_endpoints": {
            "create_user": "POST /users",
            "make_deposit": "POST /deposit",
            "make_payment": "POST /payment",
            "get_transactions": "GET /transactions/<user_id>"
        }
    })

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    new_user = User(name=data['name'], balance=data.get('balance', 0.0))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created", "user_id": new_user.id})

@app.route('/deposit', methods=['POST'])
def deposit():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        user_id = data.get('user_id')
        amount = data.get('amount')
        
        if not user_id or not amount:
            return jsonify({"error": "Missing required fields"}), 400
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user.balance += amount
        new_transaction = Transaction(user_id=user.id, amount=amount, transaction_type='deposit')
        db.session.add(new_transaction)
        db.session.commit()
        return jsonify({"message": "Deposit successful", "new_balance": user.balance})
    except Exception as e:
        print(f"Error in deposit: {str(e)}")  # Debug print
        return jsonify({"error": str(e)}), 500

@app.route('/payment', methods=['POST'])
def make_payment():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        user_id = data.get('user_id')
        recipient_id = data.get('recipient_id')
        amount = data.get('amount')
        
        if not user_id or not recipient_id or not amount:
            return jsonify({"error": "Missing required fields"}), 400
            
        sender = User.query.get(user_id)
        recipient = User.query.get(recipient_id)
        
        if not sender or not recipient:
            return jsonify({"error": "User not found"}), 404
        
        if sender.balance < amount:
            return jsonify({"error": "Insufficient funds"}), 400
        
        # Create transaction for sender
        sender_transaction = Transaction(
            user_id=sender.id,
            recipient_id=recipient.id,
            amount=-amount,
            transaction_type='payment'
        )
        
        # Create transaction for recipient
        recipient_transaction = Transaction(
            user_id=recipient.id,
            recipient_id=sender.id,
            amount=amount,
            transaction_type='payment'
        )
        
        # Update balances
        sender.balance -= amount
        recipient.balance += amount
        
        # Add transactions and commit
        db.session.add(sender_transaction)
        db.session.add(recipient_transaction)
        db.session.commit()
        
        return jsonify({
            "message": "Payment successful",
            "sender_balance": sender.balance,
            "recipient_balance": recipient.balance
        })
    except Exception as e:
        print(f"Error in make_payment: {str(e)}")  # Debug print
        return jsonify({"error": str(e)}), 500

@app.route('/transactions/<int:user_id>', methods=['GET'])
def get_transactions(user_id):
    try:
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        result = []
        for t in transactions:
            recipient = None
            if t.recipient_id:
                recipient = User.query.get(t.recipient_id)
            result.append({
                "amount": t.amount,
                "type": t.transaction_type,
                "timestamp": t.timestamp.isoformat(),
                "recipient_id": t.recipient_id,
                "recipient_name": recipient.name if recipient else None
            })
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_transactions: {str(e)}")  # Debug print
        return jsonify({"error": str(e)}), 500

def reset_db():
    """Drop all tables and recreate them"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database tables have been reset!")

# Create the tables
if __name__ == '__main__':
    try:
        reset_db()  # This will drop and recreate all tables
        app.run(debug=True)
    except Exception as e:
        print(f"Error starting the application: {e}")
        print("Please ensure PostgreSQL is running and the database credentials are correct.")

# # Requirements file
# def create_requirements():
#     with open("requirements.txt", "w") as f:
#         f.write("flask\n")
#         f.write("flask-sqlalchemy\n")
#         f.write("psycopg2\n")

# create_requirements()
