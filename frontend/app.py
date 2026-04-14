import streamlit as st
import sqlite3
import pandas as pd
import time
import requests

# Налаштування сторінки
st.set_page_config(page_title="Енергомонітор ESP32", page_icon="⚡", layout="wide")
DB_NAME = "backend/energy_data.db" # Вкажи правильний шлях до бази даних

# --- ФУНКЦІЇ ---
def get_telemetry():
    try:
        conn = sqlite3.connect(DB_NAME)
        # Беремо останні 50 записів для графіка
        df = pd.read_sql_query("SELECT * FROM telemetry ORDER BY id DESC LIMIT 50", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def get_alerts():
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT timestamp, message FROM alerts ORDER BY id DESC LIMIT 5", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# --- ІНТЕРФЕЙС (UI) ---
st.title("⚡ Панель керування енергоспоживанням")

# Бокова панель (Sidebar)
with st.sidebar:
    st.header("⚙️ Налаштування системи")
    
    # Читаємо поточний ліміт з БД
    try:
        conn = sqlite3.connect(DB_NAME)
        current_limit = conn.cursor().execute("SELECT value FROM settings WHERE key='power_threshold'").fetchone()[0]
        conn.close()
    except:
        current_limit = 5.0
        
    new_limit = st.number_input("Ліміт потужності (кВт)", value=float(current_limit), step=0.1)
    
    # Використовуємо твій існуючий Flask API для оновлення!
    if st.button("Оновити ліміт", type="primary"):
        try:
            # Відправляємо POST запит на твій server.py
            response = requests.post('http://127.0.0.1:5000/api/threshold', json={'threshold': new_limit})
            if response.status_code == 200:
                st.success("✅ Ліміт успішно оновлено!")
        except Exception as e:
            st.error(f"Помилка з'єднання з бекендом: {e}")

    st.markdown("---")
    st.markdown("💡 *Дані оновлюються автоматично*")

# Створюємо порожні контейнери для Real-time оновлення
metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
power_placeholder = metrics_col1.empty()
temp_placeholder = metrics_col2.empty()
status_placeholder = metrics_col3.empty()

st.subheader("📊 Графік показників у реальному часі")
chart_placeholder = st.empty()

st.subheader("🚨 Журнал подій (Останні 5)")
alerts_placeholder = st.empty()

# --- REAL-TIME ЦИКЛ ---
# Цей цикл створює ефект "живого" дашборда без оновлення сторінки
while True:
    df = get_telemetry()
    alerts_df = get_alerts()
    
    if not df.empty:
        # Беремо найсвіжіший запис (перший рядок)
        latest = df.iloc[0]
        p = latest['filtered_power']
        t = latest['temperature']
        
        # Оновлюємо красиві метрики
        power_placeholder.metric("Поточна потужність", f"{p} кВт")
        temp_placeholder.metric("Температура пристрою", f"{t} °C")
        
        # Логіка статусу
        if p >= current_limit or t >= 60.0:
            status_placeholder.error("КРИТИЧНО 🛑")
        elif p >= (current_limit * 0.85):
            status_placeholder.warning("ПОПЕРЕДЖЕННЯ ⚠️")
        else:
            status_placeholder.success("НОРМА ✅")
            
        # Оновлюємо графік (Streamlit робить це дуже плавно)
        chart_data = df.set_index('timestamp')[['filtered_power', 'temperature']]
        chart_placeholder.line_chart(chart_data)
        
    if not alerts_df.empty:
        alerts_placeholder.dataframe(alerts_df, hide_index=True, use_container_width=True)

    # Мінімальна затримка для оновлення (2 рази на секунду)
    time.sleep(0.5)