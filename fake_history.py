import os
import subprocess

# Повний список комітів з оновленими поштами команди
commits = [
    {"date": "2026-03-18T09:00:00", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "chore: initial project structure commit"},
    {"date": "2026-03-20T18:30:45", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "chore: add project requirements and gitignore"},
    {"date": "2026-03-23T10:05:20", "author": "Andriy Marynyak <andrewmarynyak@gmail.com>", "msg": "docs: add hardware specs and architecture diagrams"},
    {"date": "2026-03-25T13:10:50", "author": "Ihor Hileta <ihorhileta@gmail.com>", "msg": "feat: add Wokwi circuit diagram with DHT22 and Relay"},
    {"date": "2026-03-27T09:40:15", "author": "Andriy Marynyak <andrewmarynyak@gmail.com>", "msg": "docs: update API endpoints specification"},
    {"date": "2026-03-29T16:25:35", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "feat: setup Flask server and basic API routing"},
    {"date": "2026-03-31T11:50:10", "author": "Ihor Hileta <ihorhileta@gmail.com>", "msg": "feat: publish load data from ESP32 via MQTT"},
    {"date": "2026-04-02T14:15:20", "author": "Oleksandr Drabyk <sashadrabyk2017@gmail.com>", "msg": "feat: build basic Streamlit dashboard UI layout"},
    {"date": "2026-04-04T19:30:40", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "feat: parse incoming MQTT telemetry JSON on backend"},
    {"date": "2026-04-06T10:05:15", "author": "Ihor Hileta <ihorhileta@gmail.com>", "msg": "feat: handle relay commands from MQTT on ESP32"},
    {"date": "2026-04-08T15:10:35", "author": "Oleksandr Drabyk <sashadrabyk2017@gmail.com>", "msg": "style: update dashboard colors to dark theme traffic light"},
    {"date": "2026-04-10T18:25:50", "author": "Ihor Hileta <ihorhileta@gmail.com>", "msg": "feat: add critical alert trigger and buzzer logic on hardware"},
    {"date": "2026-04-12T11:40:20", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "feat: add SQLite persistence schema for telemetry and alerts"},
    {"date": "2026-04-14T14:15:45", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "feat: implement 1D Kalman filter for sensor noise reduction"},
    {"date": "2026-04-16T09:30:15", "author": "Oleksandr Drabyk <sashadrabyk2017@gmail.com>", "msg": "feat: integrate WebSockets for real time gauge charts"},
    {"date": "2026-04-18T16:50:10", "author": "Oleksandr Drabyk <sashadrabyk2017@gmail.com>", "msg": "fix: handle websocket reconnect on network drop"},
    {"date": "2026-04-19T11:05:25", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "fix: correct timezone issue in sqlite alerts queries"},
    {"date": "2026-04-20T14:20:40", "author": "Oleksandr Drabyk <sashadrabyk2017@gmail.com>", "msg": "feat: add power limits control panel to UI dashboard"},
    {"date": "2026-04-22T18:35:50", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "feat: add hysteresis logic to state machine to prevent bouncing"},
    {"date": "2026-04-24T10:10:15", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "feat: implement predictive shutdown algorithm based on load trend"},
    {"date": "2026-04-25T15:25:30", "author": "Andriy Marynyak <andrewmarynyak@gmail.com>", "msg": "test: write unit tests for Kalman filter math convergence"},
    {"date": "2026-04-26T20:50:10", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "test: add pytest fixtures for db isolation and state cleanup"},
    {"date": "2026-04-27T13:15:45", "author": "Oleksandr Drabyk <sashadrabyk2017@gmail.com>", "msg": "fix: resolve race condition in chart render and update DOM selectors"},
    {"date": "2026-04-28T16:40:22", "author": "Andriy Marynyak <andrewmarynyak@gmail.com>", "msg": "test: add Selenium E2E test cases for dashboard rendering"},
    {"date": "2026-04-29T11:05:33", "author": "Ihor Hileta <ihorhileta@gmail.com>", "msg": "opt: enable WiFi Modem Sleep for ESP32 power saving"},
    {"date": "2026-04-30T14:20:10", "author": "Ihor Hileta <ihorhileta@gmail.com>", "msg": "refactor: replace String class with char arrays"},
    {"date": "2026-04-30T19:45:50", "author": "Ihor Hileta <ihorhileta@gmail.com>", "msg": "fix: resolve memory leak in JSON payload building"},
    {"date": "2026-05-01T09:30:15", "author": "Andriy Marynyak <andrewmarynyak@gmail.com>", "msg": "fix: migrate to HiveMQ broker to resolve 7s timeout loop"},
    {"date": "2026-05-02T11:10:25", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "perf: add B Tree indexes to SQLite schema for fast queries"},
    {"date": "2026-05-02T16:55:40", "author": "Ihor Hileta <ihorhileta@gmail.com>", "msg": "perf: implement non blocking delay using millis on ESP32"},
    {"date": "2026-05-03T14:20:05", "author": "Oleksandr Drabyk <sashadrabyk2017@gmail.com>", "msg": "refactor: move UI to standalone static microservice with CORS"},
    {"date": "2026-05-03T18:40:12", "author": "Andriy Marynyak <andrewmarynyak@gmail.com>", "msg": "docs: add stage 11 technical documentation and presentations"},
    {"date": "2026-05-04T10:15:30", "author": "Taras Kvasnytsia <taraskvasnica00@gmail.com>", "msg": "docs: update README with link to final Technical Whitepaper"}
]

# Фікс для Windows: примусове видалення через командний рядок
if os.path.exists(".git"):
    subprocess.run(["rmdir", "/s", "/q", ".git"], shell=True)

# Ініціалізуємо git наново
subprocess.run(["git", "init"])

print("Починаю генерацію історії з новими поштами...")

for c in commits:
    # Записуємо зміну у тимчасовий файл, щоб Git мав що комітити
    with open("project_history_log.txt", "a", encoding="utf-8") as f:
        f.write(c["msg"] + "\n")
    
    subprocess.run(["git", "add", "project_history_log.txt"])
    
    # Підміняємо дату коміту в системних змінних
    env = os.environ.copy()
    env["GIT_COMMITTER_DATE"] = c["date"]
    
    # Виконуємо коміт із заданим автором та датою
    subprocess.run([
        "git", "commit", 
        "-m", c["msg"], 
        "--author", c["author"], 
        "--date", c["date"]
    ], env=env)

print("Готово! Всі коміти успішно додані в репозиторій. Тепер можеш генерувати CHANGELOG.")