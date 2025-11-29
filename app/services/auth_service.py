from datetime import datetime
from app.extensions import mongo,bcrypt
from app.errors.exceptions import ValidationError, DuplicateUserError,AuthError
from flask_jwt_extended import create_access_token

def login_user(data):
    email = data.get('email')
    password = data.get('password')

    user = mongo.db.users.find_one({"email": email})
    if not user or not bcrypt.check_password_hash(user['password'], password):
        raise AuthError("Email atau password salah")

    token = create_access_token(identity=str(user['_id']))
    
    return {
        "token": token,
    }

def register_user(data):
    required_fields = ['email', 'password', 'nama_lengkap']

    if not all(field in data for field in required_fields):
        missing = [field for field in required_fields if field not in data]
        raise ValidationError(f"Field berikut wajib diisi: {', '.join(missing)}")
    
    email = data['email']
    password = data['password']

    if mongo.db.users.find_one({"email": email}):
        raise DuplicateUserError("Email sudah terdaftar.")

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    new_user_document = {
        "email": email,
        "password": hashed_password,
        "created_at": datetime.utcnow(),
        
        "profile": {
            "nama_lengkap": data['nama_lengkap'],
            "berat_badan_kg": 60, 
            "tinggi_badan_cm": 170
        },
        
        "targets": {
            "calories": 2000,
            "protein": 120,
            "fat": 70,
            "carbs": 250
        }
    }

    result = mongo.db.users.insert_one(new_user_document)
  
    return str(result.inserted_id)
