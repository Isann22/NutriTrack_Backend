import os
from datetime import  timedelta

class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/iot")
    
    ESP32_IP = os.getenv('ESP32_IP')
    ESP32_API_KEY = os.getenv("ESP32_API_KEY")
    ESP32_URL = f"http://{ESP32_IP}/getWeight" if ESP32_IP else None

    CALORIE_NINJA_API_URL = os.getenv("CALORIE_NINJA_API_URL")
    CALORIE_NINJA_API_KEY = os.getenv("CALORIE_NINJA_API_KEY")
    JWT_SECRET_KEY = "ini rahasia"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

