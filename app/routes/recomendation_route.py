from flask import Blueprint, request, jsonify
from app.services.recomendation_service import DietService

recommendation_bp = Blueprint('recommendation_bp', __name__,url_prefix="/api")

diet_service = DietService()

@recommendation_bp.route('/recommendation', methods=['POST'])
def get_recommendation():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error', 
                'message': 'No input data provided'
            }), 400

        # Panggil logic dari service
        result = diet_service.process_recommendation(data)

        return jsonify({
            'status': 'success',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500