import sys
import os
import sqlite3
import pytest

# Додаємо кореневу папку в шлях для імпорту server.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server import KalmanFilter1D, get_threshold, init_db, DB_NAME

# 1. Unit Test: Перевірка роботи фільтра Калмана
def test_kalman_filter_smoothing():
    kf = KalmanFilter1D(process_noise=0.05, measurement_noise=0.3)
    # Симулюємо різкий стрибок напруги (шум)
    result1 = kf.update(2.0)
    result2 = kf.update(6.0) # Шум!
    
    # Фільтр має згладити стрибок, значення має бути меншим за 6.0
    assert result2 < 6.0
    assert result2 > result1

# 2. Integration Test: Перевірка роботи з базою даних
def test_database_threshold_logic():
    # Ініціалізуємо тестову БД
    init_db()
    
    # Перевіряємо значення за замовчуванням
    threshold = get_threshold()
    assert threshold == 5.0
    
    # Тестова зміна значення
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE settings SET value = 4.2 WHERE key = 'power_threshold'")
    conn.commit()
    conn.close()
    
    # Перевіряємо, чи оновилось
    new_threshold = get_threshold()
    assert new_threshold == 4.2