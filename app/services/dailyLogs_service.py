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
        
        # Data dari esp32
        # response_esp = requests.get(esp32_url, timeout=15)
        # response_esp.raise_for_status() 
        # weight_data = round(float(response_esp.text.strip()))
        
        # Data random
        weight_data = random.randint(10, 100)
        
        # --- 2. Ambil Data Nutrisi ---
        full_query = f"{weight_data}g {food_name}"
        headers_ninja = {'X-Api-Key': calorie_ninja_api_key}
        params_ninja = {'query': full_query}
        response_ninja = requests.get(f"{calorie_ninja_api_url}/nutrition", headers=headers_ninja, params=params_ninja, timeout=10)
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

def analyze_recipe(image_file):
    try:
        calorie_ninja_api_url = current_app.config.get('CALORIE_NINJA_API_URL')
        calorie_ninja_api_key = current_app.config.get('CALORIE_NINJA_API_KEY')
        files = {'image': (image_file.filename, image_file.read(), image_file.content_type)}
        headers = {'X-Api-Key': calorie_ninja_api_key}

        # 2. Request ke External API
        response = requests.post(f"{calorie_ninja_api_url}/imagetextnutrition", headers=headers, files=files)

        if response.status_code != 200:
            raise Exception(f"CalorieNinjas Error: {response.text}")

        data = response.json()
        items = data.get('items', [])

    
        processed_items = []
        
        for item in items:
            current_item = {
                "name": item.get('name', 'Unknown'),
                "calories": float(item.get('calories', 0)),
                "serving_size_g": float(item.get('serving_size_g', 0)),
                "fat_total_g": float(item.get('fat_total_g', 0)),
                "fat_saturated_g": float(item.get('fat_saturated_g', 0)),
                "protein_g": float(item.get('protein_g', 0)),
                "sodium_mg": int(item.get('sodium_mg', 0)),
                "potassium_mg": int(item.get('potassium_mg', 0)),
                "cholesterol_mg": int(item.get('cholesterol_mg', 0)),
                "carbohydrates_total_g": float(item.get('carbohydrates_total_g', 0)),
                "fiber_g": float(item.get('fiber_g', 0)),
                "sugar_g": float(item.get('sugar_g', 0))
            }
            processed_items.append(current_item)

        return {"items": processed_items}

    except Exception as e:
        print(f"Service Error: {str(e)}")
        raise e

def fetch_history_for_user(user_id):
    user_id_obj = ObjectId(user_id) 

    cursor = mongo.db.daily_logs.find(
        {"userId": user_id_obj}
    ).sort("tanggal", -1)

    logs = list(cursor)
    return logs