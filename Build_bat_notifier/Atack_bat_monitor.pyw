import os
import sys
import time
import threading
import json
import hid
import pystray
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw

# --- НАСТРОЙКИ ПУТЕЙ И ЛОГОВ ---
def get_base_path():
    """Возвращает папку, где лежит EXE или скрипт"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
LOG_FILE = os.path.join(BASE_DIR, "mouse_monitor.log")
CONFIG_FILE = os.path.join(BASE_DIR, "settings.json")
UPTIME_FILE = os.path.join(BASE_DIR, "uptime.json")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

# --- ПАРАМЕТРЫ УСТРОЙСТВА ---
VID = 0x1d57
PID = 0xfa60
TARGET_USAGE_PAGE = 0xa

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---
current_battery = "???"
running = True
first_run_notification = True 
global_icon = None
menu_lock = threading.Lock()
show_settings_flag = False

# Защита от мусорных данных
battery_history = []
STABILITY_THRESHOLD = 3 
CHECK_INTERVAL = 3600

# Глобальные переменные аптайма
accumulated_uptime = 0.0
last_saved_battery_level = 100

# --- ЛОГИКА АПТАЙМА ---
def load_uptime():
    global accumulated_uptime, last_saved_battery_level
    if os.path.exists(UPTIME_FILE):
        try:
            with open(UPTIME_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                accumulated_uptime = data.get("accumulated_uptime", 0.0)
                last_saved_battery_level = data.get("last_battery_level", 100)
        except Exception as e:
            logging.error(f"Ошибка загрузки аптайма: {e}")

def save_uptime():
    try:
        with open(UPTIME_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "accumulated_uptime": accumulated_uptime,
                "last_battery_level": last_saved_battery_level
            }, f)
    except Exception as e:
        logging.error(f"Ошибка сохранения аптайма: {e}")

def get_uptime_string():
    d = int(accumulated_uptime // 86400)
    h = int((accumulated_uptime % 86400) // 3600)
    m = int((accumulated_uptime % 3600) // 60)
    return f"{d}д:{h}ч:{m}м"

# --- ЛОГИКА ПРАВИЛ УВЕДОМЛЕНИЙ ---
default_rules = [
    {"threshold": 50, "repeats": 1, "interval_min": 0},
    {"threshold": 20, "repeats": 3, "interval_min": 10},
    {"threshold": 10, "repeats": 5, "interval_min": 5},
    {"threshold": 5,  "repeats": 99, "interval_min": 5}
]

rules = []
current_zone_index = -1
custom_message = "Ахтунг!! Ахтунг!! Садится батарейка: {percent}%"

def load_settings():
    global rules, custom_message
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    rules = data
                else:
                    rules = data.get("rules", default_rules.copy())
                    custom_message = data.get("custom_message", custom_message)
        except Exception as e:
            logging.error(f"Ошибка чтения настроек: {e}")
            rules = default_rules.copy()
    else:
        rules = default_rules.copy()
    
    for r in rules:
        r['current_count'] = 0
        r['last_time'] = 0

def save_settings(new_rules, new_msg):
    global rules, current_zone_index, custom_message
    try:
        save_rules = [{"threshold": r["threshold"], "repeats": r["repeats"], "interval_min": r["interval_min"]} for r in new_rules]
        save_data = {
            "rules": save_rules,
            "custom_message": new_msg
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False)
        
        for r in new_rules:
            r['current_count'] = 0
            r['last_time'] = 0
        rules = new_rules
        custom_message = new_msg
        current_zone_index = -1 
        logging.info("Настройки сохранены.")
    except Exception as e:
        logging.error(f"Ошибка сохранения настроек: {e}")

# --- ФУНКЦИИ УВЕДОМЛЕНИЙ ---
def send_notification(icon, percent, is_test=False):
    if icon is None:
        logging.warning("Попытка отправить уведомление, но icon не инициализирован")
        return
    
    title = "Настройка X11" if is_test else "Attack Shark X11"
    
    if "{percent}" in custom_message:
        msg = custom_message.replace("{percent}", str(percent))
    else:
        msg = f"{custom_message} {percent}%"
        
    if is_test:
        msg = f"[ТЕСТ] {msg}"
    
    try:
        icon.notify(msg, title)
        logging.info(f"Уведомление отправлено (через pystray): {title} - {msg}")
    except Exception as e:
        logging.error(f"Ошибка при вызове notify: {e}")

def process_battery_rules(battery_level, icon):
    global current_zone_index
    current_time = time.time()
    
    new_zone_index = -1
    for i, rule in enumerate(rules):
        if battery_level <= rule['threshold']:
            new_zone_index = i
            
    if new_zone_index != current_zone_index:
        current_zone_index = new_zone_index
        if current_zone_index != -1:
            rules[current_zone_index]['current_count'] = 0
            rules[current_zone_index]['last_time'] = 0
            logging.info(f"Переход в зону заряда: <= {rules[current_zone_index]['threshold']}%")

    if current_zone_index != -1:
        active_rule = rules[current_zone_index]
        
        if active_rule['current_count'] < active_rule['repeats']:
            time_since_last = current_time - active_rule['last_time']
            required_interval_sec = active_rule['interval_min'] * 60
            
            if time_since_last >= required_interval_sec:
                send_notification(icon, battery_level)
                active_rule['current_count'] += 1
                active_rule['last_time'] = current_time
                logging.info(f"Сработало правило {active_rule['threshold']}% ({active_rule['current_count']}/{active_rule['repeats']})")

# --- GUI (TKINTER) ---
class SettingsWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Настройки Attack Shark X11")
        self.root.geometry("460x420")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        self.entries = []
        self.uptime_label = None
        self.battery_label = None
        self.msg_entry = None
        
        self.build_ui()
        self.populate_ui()
        
    def build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.battery_label = ttk.Label(status_frame, text="Текущий заряд: ???", font=("Arial", 16, "bold"), foreground="#2e8b57")
        self.battery_label.pack()
        
        self.uptime_label = ttk.Label(status_frame, text="В работе: 0д:0ч:0м", font=("Arial", 11))
        self.uptime_label.pack(pady=(5, 0))
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        msg_frame = ttk.Frame(main_frame)
        msg_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(msg_frame, text="Текст оповещения (тег {percent} обязателен):", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.msg_entry = ttk.Entry(msg_frame, width=50)
        self.msg_entry.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        rules_frame = ttk.Frame(main_frame)
        rules_frame.pack(fill=tk.BOTH, expand=True)
        
        headers = ["Порог заряда (%)", "Кол-во оповещений", "Интервал (мин)"]
        for col, text in enumerate(headers):
            ttk.Label(rules_frame, text=text, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=10, pady=5)
        
        for row in range(4):
            row_entries = {}
            e_thresh = ttk.Entry(rules_frame, width=10, justify="center")
            e_thresh.grid(row=row+1, column=0, padx=10, pady=5)
            row_entries['threshold'] = e_thresh
            
            e_rep = ttk.Entry(rules_frame, width=10, justify="center")
            e_rep.grid(row=row+1, column=1, padx=10, pady=5)
            row_entries['repeats'] = e_rep
            
            e_int = ttk.Entry(rules_frame, width=10, justify="center")
            e_int.grid(row=row+1, column=2, padx=10, pady=5)
            row_entries['interval_min'] = e_int
            
            self.entries.append(row_entries)
            
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        save_btn = ttk.Button(btn_frame, text="Сохранить настройки", command=self.save_data)
        save_btn.pack()

    def populate_ui(self):
        if self.msg_entry:
            self.msg_entry.delete(0, tk.END)
            self.msg_entry.insert(0, custom_message)
            
        for i, rule in enumerate(rules):
            if i < len(self.entries):
                self.entries[i]['threshold'].insert(0, str(rule.get('threshold', '')))
                self.entries[i]['repeats'].insert(0, str(rule.get('repeats', '')))
                self.entries[i]['interval_min'].insert(0, str(rule.get('interval_min', '')))

    def save_data(self):
        new_rules = []
        try:
            for row in self.entries:
                t_str = row['threshold'].get()
                if not t_str: continue 
                
                new_rules.append({
                    "threshold": int(t_str),
                    "repeats": int(row['repeats'].get()),
                    "interval_min": int(row['interval_min'].get()),
                    "current_count": 0,
                    "last_time": 0
                })
            
            new_rules = sorted(new_rules, key=lambda x: x['threshold'], reverse=True)
            
            new_msg = self.msg_entry.get().strip()
            if not new_msg:
                new_msg = "Низкий заряд батареи: {percent}%!"
                
            save_settings(new_rules, new_msg)
            messagebox.showinfo("Успех", "Настройки сохранены!", parent=self.root)
            self.hide_window()
        except ValueError:
            messagebox.showerror("Ошибка", "Вводите только целые числа в поля правил.", parent=self.root)

    def update_dynamic_ui(self, time_str, bat_str):
        if self.uptime_label:
            self.uptime_label.config(text=f"Время работы мыши: {time_str}")
        if self.battery_label:
            self.battery_label.config(text=f"Текущий заряд: {bat_str}")

    def hide_window(self):
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

# --- СИСТЕМНЫЙ ТРЕЙ И ИКОНКА ---
def create_fin_image():
    """Резервная отрисовка серого плавника акулы, если картинка не найдена"""
    width, height = 64, 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    fin_color = (130, 130, 130) # Серый цвет
    # Рисуем плавник (треугольник с изгибом)
    dc.polygon([(15, 55), (35, 10), (50, 55), (35, 45)], fill=fin_color)
    
    return image

def get_tray_image():
    """Сначала ищет tray_ico.png внутри EXE (если вшита), потом рядом, иначе рисует плавник"""
    icon_to_load = None
    
    # 1. Если программа собрана в EXE через PyInstaller с --add-data, ищем во временной папке
    if getattr(sys, 'frozen', False):
        embedded_icon = os.path.join(sys._MEIPASS, "tray_ico.png")
        if os.path.exists(embedded_icon):
            icon_to_load = embedded_icon
            
    # 2. Если внутри нет (или это просто запуск скрипта), ищем рядом с EXE/скриптом
    if not icon_to_load:
        external_icon = os.path.join(BASE_DIR, "tray_ico.png")
        if os.path.exists(external_icon):
            icon_to_load = external_icon

    if icon_to_load:
        try:
            img = Image.open(icon_to_load).convert("RGBA")
            resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
            img = img.resize((64, 64), resample_filter)
            logging.info(f"Иконка успешно загружена из: {icon_to_load}")
            return img
        except Exception as e:
            logging.error(f"Ошибка загрузки картинки {icon_to_load}: {e}")
    else:
        logging.warning("Файл tray_ico.png не найден. Используем резервный серый плавник.")
            
    return create_fin_image()

def trigger_settings_show(icon, item=None):
    global show_settings_flag
    show_settings_flag = True

def update_menu(icon):
    if icon is None: return
    with menu_lock:
        try:
            display_val = current_battery.replace('%', '')
            icon.menu = pystray.Menu(
                pystray.MenuItem("⚙ Настройки", trigger_settings_show, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(f"Заряд: {current_battery}", lambda: None, enabled=False),
                pystray.MenuItem(f"В работе: {get_uptime_string()}", lambda: None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Тестовое оповещение", lambda: send_notification(icon, display_val, is_test=True)),
                pystray.MenuItem("Открыть лог", lambda: os.startfile(LOG_FILE)),
                pystray.MenuItem("Выход", on_quit)
            )
        except Exception as e:
            logging.error(f"Ошибка обновления меню: {e}")

def on_quit(icon, item):
    global running
    logging.info("Выход через меню")
    running = False
    save_uptime()
    icon.stop()

# --- ЛОГИКА МОНИТОРИНГА ---
def send_battery_request(device_handle):
    try:
        device_handle.write([0x05, 0x11, 0x01, 0x00, 0x00])
    except Exception as e:
        pass

def battery_listener():
    global current_battery, running, first_run_notification, battery_history, global_icon
    global accumulated_uptime, last_saved_battery_level
    
    last_request_time = 0
    last_tick_time = time.time()
    last_save_time = time.time()
    device_handle = None
    
    logging.info("Поток мониторинга запущен")

    while running:
        if device_handle is None:
            try:
                devices = hid.enumerate(VID, PID)
                target = next((d for d in devices if d['usage_page'] == TARGET_USAGE_PAGE), None)
                if target:
                    device_handle = hid.device()
                    device_handle.open_path(target['path'])
                    device_handle.set_nonblocking(True)
                    send_battery_request(device_handle)
                    last_request_time = time.time()
                else:
                    time.sleep(5)
                    last_tick_time = time.time() 
                    continue
            except Exception as e:
                time.sleep(5)
                last_tick_time = time.time()
                continue

        try:
            current_time = time.time()
            
            delta = current_time - last_tick_time
            last_tick_time = current_time
            accumulated_uptime += delta
            
            if current_time - last_save_time > 60:
                save_uptime()
                last_save_time = current_time
            
            if current_time - last_request_time > CHECK_INTERVAL:
                send_battery_request(device_handle)
                last_request_time = current_time

            data = device_handle.read(64)
            if data and data[0] == 3:
                level = data[4]
                if 0 <= level <= 100:
                    battery_history.append(level)
                    if len(battery_history) > STABILITY_THRESHOLD:
                        battery_history.pop(0)
                    
                    if len(battery_history) == STABILITY_THRESHOLD and len(set(battery_history)) == 1:
                        confirmed_level = battery_history[0]
                        
                        if confirmed_level >= 95 and last_saved_battery_level < 95:
                            accumulated_uptime = 0.0
                            logging.info("Мышь заряжена! Счетчик аптайма сброшен.")
                        
                        if confirmed_level != last_saved_battery_level:
                            last_saved_battery_level = confirmed_level
                            save_uptime()

                        if current_battery != f"{confirmed_level}%":
                            current_battery = f"{confirmed_level}%"
                            if global_icon:
                                global_icon.title = f"Attack Shark X11: {current_battery}"
                        
                        if first_run_notification:
                            send_notification(global_icon, confirmed_level, is_test=True)
                            first_run_notification = False
                        
                        if global_icon:
                            process_battery_rules(confirmed_level, global_icon)
            
            if int(current_time) % 15 == 0:
                update_menu(global_icon)
                
        except Exception as e:
            if device_handle:
                try: device_handle.close()
                except: pass
            device_handle = None
            
        time.sleep(1)

# --- ГЛАВНЫЙ ЦИКЛ (СВЯЗКА GUI И ТРЕЯ) ---
def main():
    global global_icon, running, show_settings_flag
    
    load_settings()
    load_uptime()
    
    root = tk.Tk()
    app = SettingsWindow(root)
    root.withdraw() 
    
    global_icon = pystray.Icon("mouse_monitor", get_tray_image(), "X11 Monitor")
    update_menu(global_icon)
    
    threading.Thread(target=battery_listener, daemon=True).start()
    threading.Thread(target=global_icon.run, daemon=True).start()
    
    def check_flags():
        global show_settings_flag, running
        if not running:
            root.quit()
            return
            
        if show_settings_flag:
            app.show_window()
            show_settings_flag = False
            
        app.update_dynamic_ui(get_uptime_string(), current_battery)
        root.after(500, check_flags)
        
    root.after(500, check_flags)
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"ФАТАЛЬНАЯ ОШИБКА: {e}")