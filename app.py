import os
import json
import hashlib
import random
from datetime import datetime
from flask import Flask, request, render_template, session, redirect, url_for
import requests

app = Flask(__name__)
app.secret_key = "your_secret_key_here_12345"

# Папка для логов
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Словарь для перевода названий стран с русского на английский
RUSSIAN_TO_ENGLISH = {
    "россия": "russia",
    "рф": "russia",
    "сша": "usa",
    "америка": "usa",
    "соединенные штаты": "usa",
    "германия": "germany",
    "франция": "france",
    "великобритания": "uk",
    "англия": "uk",
    "италия": "italy",
    "испания": "spain",
    "китай": "china",
    "япония": "japan",
    "индия": "india",
    "бразилия": "brazil",
    "канада": "canada",
    "австралия": "australia"
}

# Интересные факты (для скрапинга, если Wikipedia не доступна)
INTERESTING_FACTS_DB = {
    "russia": "🇷🇺 Россия — самая большая страна в мире, занимающая 1/8 часть суши. Здесь находится самое глубокое озеро Байкал, содержащее 20% всей пресной воды на планете!",
    "usa": "🇺🇸 США — третья по численности населения страна в мире. Здесь находится самое большое количество миллиардеров.",
    "germany": "🇩🇪 Германия — первая страна в мире, где перешли на летнее время.",
    "france": "🇫🇷 Франция — самая посещаемая страна в мире (около 90 млн туристов в год).",
    "japan": "🇯🇵 Япония состоит из более чем 6800 островов.",
    "china": "🇨🇳 Китай изобрёл бумагу, компас, порох и книгопечатание.",
    "uk": "🇬🇧 Великобритания — единственная страна, у которой нет письменной конституции.",
    "india": "🇮🇳 Индия — самая большая демократия в мире.",
    "brazil": "🇧🇷 Бразилия — единственная страна в Южной Америке, где говорят на португальском.",
    "australia": "🇦🇺 Австралия — одновременно страна и континент.",
    "canada": "🇨🇦 Канада имеет самую длинную береговую линию в мире.",
    "italy": "🇮🇹 Италия имеет 55 объектов Всемирного наследия ЮНЕСКО.",
    "spain": "🇪🇸 Испания — вторая по величине страна в Европе."
}

def get_country_name_english(query):
    """Переводит русское название страны на английский"""
    query_lower = query.lower().strip()
    if query_lower in RUSSIAN_TO_ENGLISH:
        return RUSSIAN_TO_ENGLISH[query_lower]
    return query

def get_interesting_fact(country_name):
    """Возвращает интересный факт о стране"""
    country_lower = country_name.lower()
    for key, fact in INTERESTING_FACTS_DB.items():
        if key in country_lower or country_lower in key:
            return fact
    return f"🌟 {country_name} — удивительная страна с богатой историей и уникальными традициями!"

def get_country_description(country_name):
    """Возвращает описание страны"""
    return get_interesting_fact(country_name)

# ---------- Функции логирования ----------
def get_user_log_file(username):
    safe_username = "".join(c for c in username if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return os.path.join(LOG_DIR, f"{safe_username}.log")

def log_action(username, action, details):
    log_file = get_user_log_file(username)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {action}: {details}\n")
    
    print(f"Лог: {username} - {action}")

# ---------- Функции получения данных через API ----------
def get_country_info_by_api(country_name):
    """Получает данные о стране через REST Countries API"""
    country_name_eng = get_country_name_english(country_name)
    
    urls = [
        f"https://restcountries.com/v3.1/name/{country_name_eng}?fullText=true",
        f"https://restcountries.com/v3.1/name/{country_name_eng}"
    ]
    
    for url in urls:
        try:
            print(f"API запрос: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()[0]
                currencies = data.get("currencies", {})
                currency_name = list(currencies.values())[0].get("name", "N/A") if currencies else "N/A"
                
                capital = data.get("capital", ["N/A"])
                capital_name = capital[0] if capital else "N/A"
                
                return {
                    "name": data["name"]["common"],
                    "official_name": data["name"].get("official", "N/A"),
                    "capital": capital_name,
                    "population": f"{data['population']:,}",
                    "area": f"{data.get('area', 0):,}",
                    "currency": currency_name,
                    "languages": ", ".join(data.get("languages", {}).values()),
                    "flag_url": data.get("flags", {}).get("png", ""),
                    "region": data.get("region", "N/A"),
                    "subregion": data.get("subregion", "N/A")
                }
        except Exception as e:
            print(f"API Error: {e}")
            continue
    
    return None

def get_random_country():
    """Получает случайную страну через API"""
    try:
        # Получаем ВСЕ страны (без фильтрации полей)
        url = "https://restcountries.com/v3.1/all"
        print("Загрузка случайной страны через API...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, timeout=15, headers=headers)
        
        if response.status_code == 200:
            all_countries = response.json()
            print(f"Загружено {len(all_countries)} стран")
            
            # Выбираем случайную страну
            random_country = random.choice(all_countries)
            
            # Извлекаем данные
            currencies = random_country.get("currencies", {})
            currency_name = "N/A"
            if currencies:
                currency_name = list(currencies.values())[0].get("name", "N/A")
            
            capital = random_country.get("capital", ["N/A"])
            capital_name = capital[0] if capital else "N/A"
            
            country_data = {
                "name": random_country["name"]["common"],
                "official_name": random_country["name"].get("official", "N/A"),
                "capital": capital_name,
                "population": f"{random_country.get('population', 0):,}",
                "area": f"{random_country.get('area', 0):,}",
                "currency": currency_name,
                "languages": ", ".join(random_country.get("languages", {}).values()),
                "flag_url": random_country.get("flags", {}).get("png", ""),
                "region": random_country.get("region", "N/A"),
                "subregion": random_country.get("subregion", "N/A")
            }
            
            print(f"Случайная страна: {country_data['name']} (столица: {country_data['capital']})")
            return country_data
        else:
            print(f"API ошибка: статус {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Random country error: {e}")
        return None

def search_by_capital(capital_name):
    """Ищет страну по названию столицы"""
    try:
        url = f"https://restcountries.com/v3.1/capital/{capital_name}"
        print(f"Поиск по столице: {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()[0]
            return get_country_info_by_api(data["name"]["common"])
    except Exception as e:
        print(f"Capital search error: {e}")
    return None

# ---------- Маршруты ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if username:
            session["username"] = username
            log_action(username, "ВХОД В СИСТЕМУ", "Пользователь вошёл в систему")
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Пожалуйста, введите ваше имя")
    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    if "username" in session:
        username = session["username"]
        log_action(username, "ВЫХОД ИЗ СИСТЕМЫ", "Пользователь вышел из системы")
        session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    
    username = session["username"]
    result = None
    query = ""
    compare_country2 = ""

    if request.method == "POST":
        action = request.form.get("action")
        query = request.form.get("query", "").strip()
        compare_country2 = request.form.get("compare_country2", "").strip()

        # Функция 1: Поиск по названию страны
        if action == "search_by_name" and query:
            print(f"{username} ищет: {query}")
            log_action(username, "ПОИСК ПО НАЗВАНИЮ", query)
            
            country_data = get_country_info_by_api(query)
            if country_data:
                country_data["description"] = get_country_description(country_data["name"])
                result = country_data
                log_action(username, "РЕЗУЛЬТАТ ПОИСКА", country_data['name'])
            else:
                result = {"error": f"❌ Страна '{query}' не найдена"}
                log_action(username, "ОШИБКА ПОИСКА", query)

        # Функция 2: Поиск по столице
        elif action == "search_by_capital" and query:
            print(f"{username} ищет по столице: {query}")
            log_action(username, "ПОИСК ПО СТОЛИЦЕ", query)
            
            country_data = search_by_capital(query)
            if country_data:
                country_data["description"] = get_country_description(country_data["name"])
                result = country_data
                log_action(username, "РЕЗУЛЬТАТ ПО СТОЛИЦЕ", country_data['name'])
            else:
                result = {"error": f"❌ Страна со столицей '{query}' не найдена"}
                log_action(username, "ОШИБКА ПОИСКА СТОЛИЦЫ", query)

        # Функция 3: Сравнение двух стран
        elif action == "compare" and query and compare_country2:
            print(f"{username} сравнивает: {query} vs {compare_country2}")
            log_action(username, "СРАВНЕНИЕ", f"{query} vs {compare_country2}")
            
            c1 = get_country_info_by_api(query)
            c2 = get_country_info_by_api(compare_country2)
            if c1 and c2:
                c1["description"] = get_country_description(c1["name"])
                c2["description"] = get_country_description(c2["name"])
                result = {"compare": True, "country1": c1, "country2": c2}
                log_action(username, "РЕЗУЛЬТАТ СРАВНЕНИЯ", f"{c1['name']} vs {c2['name']}")
            else:
                result = {"error": "❌ Одна или обе страны не найдены"}
                log_action(username, "ОШИБКА СРАВНЕНИЯ", f"{query} vs {compare_country2}")

        # Функция 4: Случайная страна (ЧЕРЕЗ API)
        elif action == "random_country":
            print(f"{username} запросил случайную страну")
            log_action(username, "ЗАПРОС СЛУЧАЙНОЙ СТРАНЫ", "API запрос")
            
            country_data = get_random_country()
            if country_data:
                country_data["description"] = get_country_description(country_data["name"])
                result = country_data
                log_action(username, "СЛУЧАЙНАЯ СТРАНА", country_data['name'])
                print(f"Случайная страна через API: {country_data['name']}")
            else:
                result = {"error": "❌ API временно недоступен. Попробуйте ещё раз через несколько секунд."}
                log_action(username, "ОШИБКА API", "Случайная страна не получена")

    return render_template("index.html", result=result, username=username, query=query, compare_country2=compare_country2)

if __name__ == "__main__":
    print("=" * 50)
    print("🌍 Гид по странам мира - запущен")
    print("📡 Используется REST Countries API")
    print("📁 Логи: папка logs/")
    print("=" * 50)
    app.run(debug=True)