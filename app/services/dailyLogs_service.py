import requests
from app.errors.exceptions import (
  ValidationError,
  NoNutritionDataFound,
  NutritionAPIFetchError
)
from datetime import datetime, date
from bson.objectid import ObjectId
from flask import current_app 
from app.extensions import mongo
import random

def analyze_food(food_name,food_name_display, meal_type,user_id):
    esp32_url = current_app.config.get('ESP32_URL')
    calorie_ninja_api_url = current_app.config.get('CALORIE_NINJA_API_URL')
    calorie_ninja_api_key = current_app.config.get('CALORIE_NINJA_API_KEY')
    
    if not food_name:
        raise ValidationError("Nama makanan tidak boleh kosong.")
        
    VALID_MEAL_TYPES = ["Sarapan", "Makan Siang", "Makan Malam"]
    if meal_type not in VALID_MEAL_TYPES:
        raise ValidationError(f"mealType tidak valid. Harus salah satu dari: {VALID_MEAL_TYPES}")

    try:
        
        response_esp = requests.get(esp32_url, timeout=15)
        response_esp.raise_for_status() 
        weight_data = round(float(response_esp.text.strip()))
        
       
    
     
        
        # --- 2. Ambil Data Nutrisi ---
        full_query = f"{weight_data}g {food_name}"
        headers_ninja = {'X-Api-Key': calorie_ninja_api_key}
        params_ninja = {'query': full_query}
        response_ninja = requests.get(calorie_ninja_api_url, headers=headers_ninja, params=params_ninja, timeout=10)
        response_ninja.raise_for_status()
        nutrition_data = response_ninja.json()

        if not nutrition_data.get('items'):
            raise NoNutritionDataFound(f"Tidak ditemukan data nutrisi untuk '{full_query}'")

        food_item = nutrition_data['items'][0]

       
        user_id_obj = ObjectId(user_id) 
        today = datetime.combine(date.today(), datetime.min.time())
   

        calories_to_add = round(food_item.get("calories", 0), 2)
        protein_to_add = round(food_item.get("protein_g", 0), 2)
        fat_to_add = round(food_item.get("fat_total_g", 0), 2)
        carbs_to_add = round(food_item.get("carbohydrates_total_g", 0), 2) 
        
        new_entry = {
            "foodName": food_name_display,
            "timestamp": datetime.utcnow(),
            "portionSize_g": weight_data,
            "nutrition": {
                "calories_kcal": calories_to_add,
                "protein_g": protein_to_add,
                "fat_total_g": fat_to_add,
                "carbohydrates_g": carbs_to_add
            }
        }

        query = {"userId": user_id_obj, "tanggal": today}
        
        push_key = f"log.{meal_type}" 

        update = {
            "$push": { push_key: new_entry }, 
            "$inc": {
                "summary.total_calories_kcal": calories_to_add,
                "summary.total_protein_g": protein_to_add,
                "summary.total_fat_g": fat_to_add,
                "summary.total_carbs_g": carbs_to_add
            },
         
            "$setOnInsert": {
                "userId": user_id_obj,
                "tanggal": today
            }
        }
        
        mongo.db.daily_logs.update_one(query, update, upsert=True)
        
        return {
            "message": "Data nutrisi berhasil dianalisis dan disimpan.",
            "query": full_query,
            "data": new_entry
        }

    except requests.exceptions.HTTPError as http_err:
        raise NutritionAPIFetchError(f"Terjadi masalah saat menghubungi CalorieNinjas API: {http_err.response.text}")
    
    except requests.exceptions.RequestException as e:
        raise NutritionAPIFetchError(f"Gagal terhubung ke CalorieNinjas: {e}")
    
def fetch_history_for_user(user_id):
    user_id_obj = ObjectId(user_id) 

    cursor = mongo.db.daily_logs.find(
        {"userId": user_id_obj}
    ).sort("tanggal", -1)

    logs = list(cursor)
    return logs