from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_web_dashboard():
    # Ініціалізація браузера (Chrome)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # Запуск без відкриття вікна
    driver = webdriver.Chrome(options=options)
    
    try:
        # Відкриваємо наш локальний дашборд
        driver.get("http://127.0.0.1:5000")
        
        # Перевіряємо заголовок сторінки
        assert "Energy Saver" in driver.title
        
        # Перевіряємо наявність блоку статусу
        status_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "status-val"))
        )
        assert status_element.text != ""
        
        # Перевіряємо взаємодію з інпутом ліміту
        limit_input = driver.find_element(By.ID, "limit")
        limit_input.clear()
        limit_input.send_keys("3.5")
        
        button = driver.find_element(By.XPATH, "//button[contains(text(), 'Застосувати')]")
        button.click()
        
        print("E2E Тест UI: УСПІШНО ПРОЙДЕНО")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_web_dashboard()