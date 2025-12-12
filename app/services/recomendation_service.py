import os
import torch
import joblib
import pandas as pd
import numpy as np
import random
from app.ai_model import CaloriesModel, NutritionModel 

class DietService:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(current_dir)
        self.artifacts_dir = os.path.join(app_dir, 'artifacts')

        self.activity_level_map = {
            "Sedentary": 1.2, 
            "Active": 1.55, 
            "Very Active": 1.725
        }

        self.load_models()

    def load_models(self):
        print("Loading AI Models...")
        try:
            # 1. Load Calories Model
            self.calories_model = CaloriesModel()
            self.calories_model.load_state_dict(torch.load(os.path.join(self.artifacts_dir, 'calories_model.pth')))
            self.calories_model.eval()
            
            self.calories_scaler_X = joblib.load(os.path.join(self.artifacts_dir, 'calories_scaler_X.pkl'))
            self.gender_label_encoder = joblib.load(os.path.join(self.artifacts_dir, 'gender_label_encoder.pkl'))
            y_params = joblib.load(os.path.join(self.artifacts_dir, 'calories_y_scaler_params.pkl'))
            self.y_mean = y_params['mean']
            self.y_std = y_params['std']

            # 2. Load Meal Models
            self.meals = ['breakfast', 'lunch', 'dinner']
            self.meal_resources = {} # Simpan model, scaler, data di dict ini

            for meal in self.meals:
                targets = joblib.load(os.path.join(self.artifacts_dir, f'{meal}_targets.pkl'))
                
                model = NutritionModel(input_size=1, output_size=len(targets))
                model.load_state_dict(torch.load(os.path.join(self.artifacts_dir, f'{meal}_nutrient_model.pth')))
                model.eval()
                
                self.meal_resources[meal] = {
                    'model': model,
                    'scaler_X': joblib.load(os.path.join(self.artifacts_dir, f'{meal}_scaler_X.pkl')),
                    'scaler_y': joblib.load(os.path.join(self.artifacts_dir, f'{meal}_scaler_y.pkl')),
                    'targets': targets,
                    'data': pd.read_pickle(os.path.join(self.artifacts_dir, f'{meal}_data.pkl'))
                }
            print("AI Models Loaded Successfully.")
        except Exception as e:
            print(f"Error loading models: {e}")
            raise e

    def calculate_bmi(self, weight, height):
        if height <= 0: return None
        return weight / (height ** 2)

    def calculate_bmr(self, age, weight, height, gender):
        height_cm = height * 100
        if gender == "M":
            return 88.362 + (13.397 * weight) + (4.799 * height_cm) - (5.677 * age)
        else:
            return 447.593 + (9.247 * weight) + (3.098 * height_cm) - (4.330 * age)

    def _predict_calories_raw(self, inputs):
        # Internal function
        inputs_scaled = self.calories_scaler_X.transform([inputs])
        inputs_tensor = torch.tensor(inputs_scaled, dtype=torch.float32)
        with torch.no_grad():
            prediction = self.calories_model(inputs_tensor).item()
        return prediction * self.y_std + self.y_mean

    def _predict_nutrients_raw(self, caloric_value, meal_name):
        # Internal function
        res = self.meal_resources[meal_name]
        cal_scaled = res['scaler_X'].transform([[caloric_value]])
        cal_tensor = torch.tensor(cal_scaled, dtype=torch.float32)
        with torch.no_grad():
            pred = res['model'](cal_tensor).numpy()
        return res['scaler_y'].inverse_transform(pred)[0]

    def select_meal_recipes(self, meal_df, target_cal, target_nutrients, max_attempts=5000):
        # Logika algoritma seleksi resep (sama seperti kode asli, hanya disesuaikan return value)
        nutrient_priority = {'Protein': 0.15, 'Carbohydrates': 0.15, 'Fat': 0.15, 'default': 0.25}
        
        def calculate_score(actual_cal, actual_nut, target_c, target_n):
            scores = []
            cal_err = abs(actual_cal - target_c) / target_c if target_c != 0 else 1
            scores.append(min(cal_err / 0.10, 1.0))
            for nut, val in target_n.items():
                actual = actual_nut.get(nut, 0)
                tol = nutrient_priority.get(nut, nutrient_priority['default'])
                err = abs(actual - val) / val if val != 0 else 1
                scores.append(min(err / tol, 1.0))
            return np.mean(scores)

        best_score = float('inf')
        best_combo = None
        closest_cal_combo = None
        min_cal_diff = float('inf')
        
        nutrient_cols = list(target_nutrients.keys())
        tolerance = 0.15

        for _ in range(max_attempts):
            num = random.choices([1, 2, 3], weights=[0.2, 0.3, 0.5])[0]
            try:
                sample = meal_df.sample(n=num, replace=False)
            except ValueError: continue
            
            total_cal = sample['Caloric Value'].sum()
            
            # Track closest calorie match as fallback
            cal_diff = abs(total_cal - target_cal)
            if cal_diff < min_cal_diff:
                min_cal_diff = cal_diff
                closest_cal_combo = sample

            # Check logic
            if (target_cal * (1 - tolerance)) <= total_cal <= (target_cal * (1 + tolerance)):
                total_nut = sample[nutrient_cols].sum().to_dict()
                score = calculate_score(total_cal, total_nut, target_cal, target_nutrients)
                if score < best_score:
                    best_score = score
                    best_combo = sample

        final_combo = best_combo if best_combo is not None else closest_cal_combo
        
        # Format output menjadi list of dict agar mudah jadi JSON
        if final_combo is None: return []
        
        results = []
        for _, row in final_combo.iterrows():
            results.append({
                "recipe_name": row.get('food_id', row['food']),
                "calories": float(row['Caloric Value']),
                "protein": float(row['Protein']),
                "carbs": float(row['Carbohydrates']),
                "fat": float(row['Fat'])
            })
        return results

    def process_recommendation(self, data):
        """
        Fungsi utama yang dipanggil oleh Route/Controller
        data: Dictionary dari input JSON
        """
        # 1. Parse Input
        age = data['age']
        weight = data['weight']
        height = data['height']
        gender = data['gender'] # "M" or "F"
        activity_str = data['activity_level']
        weight_goal = data['weight_goal']

        activity_val = self.activity_level_map.get(activity_str, 1.2)

        # 2. Logic Perhitungan Dasar
        bmi = self.calculate_bmi(weight, height)
        bmr = self.calculate_bmr(age, weight, height, gender)
        
        gender_enc = self.gender_label_encoder.transform([gender])[0]
        inputs = [age, weight, height, gender_enc, bmi, bmr, activity_val]
        
        tdee = self._predict_calories_raw(inputs)
        
        # Adjust Calorie
        recommended_cal = tdee
        if weight_goal == "Lose Weight":
             min_limit = 1200 if gender == "F" else 1500
             recommended_cal = max(tdee - 500, min_limit)
        elif weight_goal == "Gain Weight":
            recommended_cal = tdee + 500

        # 3. Bagi Kalori per Makan
        b_cal = recommended_cal * 0.25
        l_cal = recommended_cal * 0.31
        d_cal = recommended_cal * 0.35 # Sisa bisa untuk snack, logic aslinya 0.35 di dinner?

        # 4. Generate Menu untuk setiap waktu makan
        meal_plan = {}
        cal_distribution = {'breakfast': b_cal, 'lunch': l_cal, 'dinner': d_cal}
        
        # --- [UPDATE] FILTER 5 NUTRISI BERDASARKAN KOLOM DATA KAMU ---
        # Nama harus SAMA PERSIS dengan header CSV/Dataset
        priority_nutrients = ['Protein', 'Carbohydrates', 'Fat', 'Dietary Fiber', 'Sugars'] 

        for meal_name, cal_target in cal_distribution.items():
            nutrients_arr = self._predict_nutrients_raw(cal_target, meal_name)
            target_keys = self.meal_resources[meal_name]['targets']
            
            all_target_nutrients = {
                target_keys[i]: float(nutrients_arr[i]) 
                for i in range(len(target_keys))
            }
            
            # Filter Target Nutrisi (Output AI)
            filtered_target_nutrients = {
                k: v for k, v in all_target_nutrients.items() 
                if k in priority_nutrients
            }
            
            # Cari Resep
            recipes = self.select_meal_recipes(
                self.meal_resources[meal_name]['data'],
                cal_target,
                all_target_nutrients # Tetap cari pakai data lengkap biar akurat
            )

            # Filter Output Resep juga (biar JSON resepnya gak kepanjangan)
            filtered_recipes = []
            for r in recipes:
                recipe_data = {
                    "recipe_name": r['recipe_name'],
                    "calories": r['calories']
                }
                for nut in priority_nutrients:
                    if nut in r: 
                         recipe_data[nut] = r[nut]
                    # Note: Jika di select_meal_recipes kamu pakai row['Protein'], row['Fat'], maka kodenya aman.
                
                filtered_recipes.append(recipe_data)
            
            meal_plan[meal_name] = {
                "target_calories": float(round(cal_target, 2)),
                "target_nutrients": {k: float(round(v, 2)) for k,v in filtered_target_nutrients.items()},
                "recipes": filtered_recipes # Gunakan resep yang sudah disaring
            }

        return {
            "bmi": float(round(bmi, 2)),
            "bmr": float(round(bmr, 2)),
            "tdee": float(round(tdee, 2)),
            "recommended_calories": float(round(recommended_cal, 2)),
            "meal_plan": meal_plan
        }