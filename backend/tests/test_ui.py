import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def test_streamlit_dashboard_loads():
    """Тестуємо, чи успішно завантажується UI інтерфейс"""
    
    # Налаштовуємо "безголовий" режим браузера (без візуального вікна)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Streamlit за замовчуванням працює на порту 8501
        print("\n🌐 Відкриваємо веб-інтерфейс...")
        driver.get("http://localhost:8501")
        
        # Даємо Streamlit кілька секунд на повне рендерення графіків
        time.sleep(3)
        
        # QA Перевірка: перевіряємо, чи сторінка не пуста і чи має правильний заголовок
        page_title = driver.title
        page_source = driver.page_source
        
        assert page_title != "", "Сторінка завантажилась, але заголовок порожній!"
        assert "Енергомонітор" in page_source or "Журнал подій" in page_source, "Не знайдено елементів дашборду на сторінці!"        
        print(f"✅ Інтерфейс успішно завантажено! Заголовок: {page_title}")
        
    finally:
        # Обов'язково закриваємо браузер після тесту
        driver.quit()