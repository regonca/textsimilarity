from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)  # Initialize Flask app
api = Api(app) # Initialize Flask-RESTful API

client = MongoClient('mongodb://db:27017/') # Connect to MongoDB (service name "db" in docker-compose)
db = client['SimilarityDB']  # Database name
users = db['Users']  # Collection name

def UserExist(username):  # Function to check if user exists
    if users.find_one({'username': username}):
        return True
    else:
        return False    

class Register(Resource): # Define Register resource 
    def post(self):
        postedData = request.get_json()  # Get JSON data from request
        username = postedData['username']
        password = postedData['password']

        if UserExist(username):
            return jsonify(
                {'status': 301, 
                 'message': 'Invalid Username'
                })  

        
        """
        if not users.find_one({'username': username}):
            return jsonify(
                {'status': 301, 
                 'message': 'Invalid Username'
                })
        """

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Hash the password
        users.insert_one({'username': username,
                           'password': hashed_pw,
                           'Tokens': 6
                         })  # Insert user
        return jsonify(
            {'status': 200, 
             'message': 'User registered successfully to the API' 
            })  

def verifyPw(username, password):  # Function to verify password
    hashed_pw = users.find_one({'username': username})['password']  # Get hashed password from DB
    if bcrypt.checkpw(password.encode('utf-8'), hashed_pw):  # Check password
        return True
    else:
        return False

def countTokens(username):  # Function to count user tokens
    tokens = users.find_one({'username': username})['Tokens']           
    return tokens

class Detect(Resource):  # Define Detect resource
    def post(self):
        postedData = request.get_json()  # Get JSON data from request
        username = postedData['username']
        password = postedData['password']
        text1 = postedData['text1']
        text2 = postedData['text2']

        if not UserExist(username):
            return jsonify(
                {'status': 301, 
                 'message': 'Invalid Username'
                })  

        hashed_pw = users.find_one({'username': username})['password']  # Get hashed password from DB

        if not bcrypt.checkpw(password.encode('utf-8'), hashed_pw):  # Check password
            return jsonify(
                {'status': 302, 
                 'message': 'Invalid Password'
                })  

        num_tokens = countTokens(username)  # Get user tokens
    
        if num_tokens <= 0:  # Check if user has enough tokens
            return jsonify(
                {'status': 303, 
                 'message': 'Not enough tokens'
                })  

        nlp = spacy.load('en_core_web_sm')  # Load spaCy model
        text1_nlp = nlp(text1)  # Process text1
        text2_nlp = nlp(text2)  # Process text2

        # ratio is a float value between 0 and 1, where 1 means the texts are identical and 0 means they are completely different
        ratio = text1_nlp.similarity(text2_nlp)  # Calculate similarity score

        current_tokens = countTokens(username)  # Get current token count
        
        users.update_one(
            {'username': username}, 
            {'$set': {'Tokens': current_tokens - 1}
            })  # Deduct one token

        return jsonify(
            {'status': 200, 
             'similarity_score': ratio,
             'message': 'Similarity score calculated successfully'
            })  

class Refill(Resource):  # Define Refill resource   
    def post(self):
        postedData = request.get_json()  # Get JSON data from request
        username = postedData['username']
        password = postedData['admin_pw']
        refill_amount = postedData['refill']

        if not UserExist(username):
            return jsonify(
                {'status': 301, 
                 'message': 'Invalid Username'
                })  

        correct_pw = 'admin123'  # Admin password
        
        if password != correct_pw:  # Check admin password
            return jsonify(
                {'status': 304, 
                 'message': 'Invalid Admin Password'
                })  

        current_tokens = countTokens(username)  # Get current token count
        
        users.update_one(
            {'username': username}, 
            {'$set': {'Tokens': current_tokens + refill_amount}
            })  # Refill tokens

        return jsonify(
            {'status': 200, 
             'message': 'Refilled successfully'
            })  

api.add_resource(Register, '/register')  # Add Register resource to API
api.add_resource(Detect, '/detect')  # Add Detect resource to API
api.add_resource(Refill, '/refill')  # Add Refill resource to API   

if __name__ == "__main__":  # 
    app.run(host='0.0.0.0', port=5000)