import os
import sqlite3
import pytest
import sys

# Додаємо кореневу папку backend до шляхів, щоб Python міг імпортувати server.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server 

# --- ТЕСТ 1: Перевірка Фільтра Калмана ---
def test_kalman_filter_smoothing():
    """Перевіряємо, чи фільтр згладжує різкі стрибки (шум сенсора)"""
    kf = server.KalmanFilter1D(process_noise=0.8, measurement_noise=0.1)
    
    # Симулюємо стабільні показники
    kf.update(5.0)
    kf.update(5.1)
    
    # Симулюємо різкий стрибок (шум)
    noisy_value = kf.update(10.0)
    
    # Фільтр не повинен одразу пропустити 10.0, він має згладити стрибок
    assert noisy_value < 10.0, "Фільтр Калмана не згладив різкий стрибок!"
    assert noisy_value > 5.1, "Фільтр Калмана занадто сильно заблокував сигнал!"

# --- ТЕСТ 2: Перевірка ініціалізації БД ---
def test_database_initialization():
    """Перевіряємо, чи створюється база даних і таблиці"""
    # Тимчасова база для тестів, щоб не зламати основну
    server.DB_NAME = "test_energy_data.db" 
    
    if os.path.exists(server.DB_NAME):
        os.remove(server.DB_NAME)
        
    server.init_db()
    
    assert os.path.exists(server.DB_NAME), "Файл бази даних не був створений!"
    
    # Перевіряємо, чи записався стандартний ліміт
    threshold = server.get_threshold()
    assert threshold == 5.0, f"Стандартний ліміт має бути 5.0, а отримано {threshold}"

# --- ТЕСТ 3: Перевірка збереження даних (CRUD) ---
def test_save_data():
    """Перевіряємо, чи коректно записується телеметрія в базу"""
    server.DB_NAME = "test_energy_data.db"
    server.init_db()
    
    # Записуємо тестові дані
    server.save_data('telemetry', raw_power=4.5, filtered_power=4.4, temperature=25.0)
    
    # Відкриваємо базу і перевіряємо
    conn = sqlite3.connect(server.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT raw_power, temperature FROM telemetry ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None, "Дані не записалися в таблицю telemetry!"
    assert row[0] == 4.5, "Помилка запису raw_power"
    assert row[1] == 25.0, "Помилка запису temperature"

    # Прибираємо за собою після тестів
    if os.path.exists(server.DB_NAME):
        os.remove(server.DB_NAME)