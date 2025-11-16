from flask import Blueprint, request, jsonify
from app.services.dailyLogs_service import analyze_food,fetch_history_for_user
from app.errors.exceptions import (
    ValidationError, 
    NutritionAPIFetchError, 
    NoNutritionDataFound
)
from bson import ObjectId
from bson.json_util import dumps



food_bp = Blueprint('food', __name__, url_prefix='/api/food')

@food_bp.route('/analyze', methods=['POST'])
def handle_analyze_food():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body harus berupa JSON"}), 400

        food_name = data.get('foodName')
        meal_type = data.get('mealType')
        food_name_display = data.get('foodNameDisplay')

        if not food_name:
            return jsonify({"error": "foodName tidak boleh kosong"}), 400
        if not meal_type:
            return jsonify({"error": "mealType tidak boleh kosong"}), 400

        result = analyze_food(food_name,food_name_display , meal_type) 
        
        return jsonify(result), 200
    
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except NoNutritionDataFound as e:
        return jsonify({"error": str(e)}), 404
    except NutritionAPIFetchError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        return jsonify({"error": f"Terjadi kesalahan internal: {str(e)}"}), 500

@food_bp.route('/history', methods=['GET'])
def get_history():
    try:
        user_id = "68de776fa1396d792bf75555" 
        
        logs = fetch_history_for_user(user_id)
        
        return dumps(logs), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return jsonify({"error": f"Terjadi kesalahan internal: {str(e)}"}), 500