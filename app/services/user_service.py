from datetime import datetime
from app.extensions import mongo
import bcrypt
from app.errors.exceptions import ValidationError, DuplicateUserError

def register_user(data) :
    
    required_fields = [
        'email', 'password', 'nama_lengkap', 'tanggal_lahir', 
        'berat_badan_kg', 'tinggi_badan_cm'
    ]

    if not all(field in data for field in required_fields):
        missing = [field for field in required_fields if field not in data]
        raise ValidationError(f"Field berikut wajib diisi: {', '.join(missing)}")
    
    email = data['email']
    password = data['password']

    if mongo.db.users.find_one({"email": email}):
        raise DuplicateUserError("Email sudah terdaftar.")

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user_document = {
        "email": email,
        "hashed_password": hashed_password,
        "createdAt": datetime.utcnow(),
        "profile": {
            "nama_lengkap": data['nama_lengkap'],
            "tanggal_lahir": data['tanggal_lahir'],
            "berat_badan_kg": data['berat_badan_kg'],
            "tinggi_badan_cm": data['tinggi_badan_cm']
        }
    }

    result = mongo.db.users.insert_one(new_user_document)
  
    return str(result.inserted_id)