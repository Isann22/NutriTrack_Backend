from bson.objectid import ObjectId
from app.extensions import mongo
from app.errors.exceptions import ValidationError

def get_user_profile(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise ValidationError("User tidak ditemukan")

    profile = user.get('profile', {})
    targets = user.get('targets', {})

    return {
        "email": user.get('email'),
        "nama_lengkap": profile.get('nama_lengkap'),
        "berat_badan_kg": profile.get('berat_badan_kg'),
        "tinggi_badan_cm": profile.get('tinggi_badan_cm'),
        "targets": {
            "calories": targets.get('calories', 2000),
            "protein": targets.get('protein', 120),
            "fat": targets.get('fat', 70),
            "carbs": targets.get('carbs', 250)
        }
    }

def update_user_profile(user_id, data):
    user_obj = ObjectId(user_id)

    
    update_data = {
        "profile.nama_lengkap": data.get('nama_lengkap'),
        "profile.berat_badan_kg": int(data.get('berat_badan_kg', 0)),
        "profile.tinggi_badan_cm": int(data.get('tinggi_badan_cm', 0)),
        "targets.calories": int(data.get('calories', 0)),
        "targets.protein": int(data.get('protein', 0)),
        "targets.fat": int(data.get('fat', 0)),
        "targets.carbs": int(data.get('carbs', 0))
    }

    mongo.db.users.update_one(
        {"_id": user_obj},
        {"$set": update_data}
    )
    
    return "Profil berhasil diperbarui"

def update_user_targets(user_id, data):
    user_obj = ObjectId(user_id)

    update_data = {
        "targets.calories": int(data.get('calories', 0)),
        "targets.protein": int(data.get('protein', 0)),
        "targets.fat": int(data.get('fat', 0)),
        "targets.carbs": int(data.get('carbs', 0))
    }

    mongo.db.users.update_one(
        {"_id": user_obj},
        {"$set": update_data}
    )

    return "Rencana nutrisi berhasil diperbarui"