from flask import Blueprint, jsonify,request
from app.services.user_service import get_user_profile,update_user_profile,update_user_targets
from app.errors.exceptions import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/profile', methods=['GET'])

@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        data = get_user_profile(user_id)
        return jsonify(data), 200
        
    except ValidationError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@user_bp.route('/profile/edit', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        print(data)
        print(data.get('nama_lengkap'))
        msg = update_user_profile(user_id, data)
        return jsonify({"message": msg}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
