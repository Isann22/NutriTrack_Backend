from flask import Blueprint, request, jsonify
from app.services.user_service import register_user
from app.errors.exceptions import ValidationError, DuplicateUserError

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def handle_register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body harus berupa JSON"}), 400

        user_id = register_user(data)
        
        return jsonify({
            "message": "Registrasi berhasil.",
            "userId": user_id
        }), 201

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    except DuplicateUserError as e:
        return jsonify({"error": str(e)}), 409  

    except Exception as e:
        print(f"An unexpected error occurred in registration: {e}") 
        return jsonify({"error": "Terjadi kesalahan pada server."}), 500


def handle_login() :
    pass