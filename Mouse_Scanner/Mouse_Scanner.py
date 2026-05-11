import os
import sys
import time
import json
import threading
import hid
import tkinter as tk
from tkinter import ttk, messagebox

# База популярных запросов (отмычек) для китайских контроллеров
MAGIC_PACKETS = [
    [0x05, 0x11, 0x01, 0x00, 0x00], # Compx / Beken (Attack Shark, Ajazz, Lamzu)
    [0x05, 0x11, 0x02, 0x00, 0x00], # Альтернативный Compx
    [0x05, 0x10, 0x01, 0x00, 0x00], 
    [0x04, 0x02, 0x01, 0x02, 0x01], # SinoWealth (некоторые модели VGN)
    [0x04, 0x00, 0x00, 0x00, 0x00], 
    [0x00, 0x00, 0x00, 0x00, 0x00], # Пустой запрос (пинг)
]

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class MouseScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Mouse Scanner")
        self.root.geometry("550x450")
        self.root.resizable(False, False)
        
        # Данные профиля
        self.target_vid = None
        self.target_pid = None
        self.snapshot_offline = set()
        self.candidates = []
        self.selected_profile = None
        
        self.build_ui()
        
    def build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка 1: Поиск устройства
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="1. Идентификация (VID/PID)")
        self.setup_tab1()
        
        # Вкладка 2: Эвристика
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="2. Поиск заряда", state="disabled")
        self.setup_tab2()
        
        # Вкладка 3: Финал
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab3, text="3. Сохранение", state="disabled")
        self.setup_tab3()

    # --- ВКЛАДКА 1: Поиск VID / PID ---
    def setup_tab1(self):
        self.lbl_t1_status = ttk.Label(self.tab1, text="Подключите мышь к ПК.\nКогда будете готовы, нажмите Старт.", font=("Arial", 11), justify="center")
        self.lbl_t1_status.pack(pady=20)
        
        self.lbl_t1_timer = ttk.Label(self.tab1, text="", font=("Arial", 24, "bold"), foreground="#d9534f")
        self.lbl_t1_timer.pack(pady=10)
        
        self.btn_t1_start = ttk.Button(self.tab1, text="Начать (Запустится таймер)", command=self.start_vid_pid_test)
        self.btn_t1_start.pack(pady=5)
        
        self.btn_t1_ok = ttk.Button(self.tab1, text="Я вставил ресивер обратно -> ОК", command=self.finish_vid_pid_test)
        
        self.lbl_t1_result = ttk.Label(self.tab1, text="", font=("Courier", 12, "bold"), foreground="green")

    def get_current_devices(self):
        return {(d['vendor_id'], d['product_id']) for d in hid.enumerate()}

    def start_vid_pid_test(self):
        self.btn_t1_start.config(state=tk.DISABLED)
        self.lbl_t1_result.config(text="")
        self.lbl_t1_status.config(text="ВЫТАЩИТЕ USB-ресивер из компьютера!", foreground="#d9534f")
        self.t1_counter = 10
        self.update_t1_timer()

    def update_t1_timer(self):
        if self.t1_counter > 0:
            self.lbl_t1_timer.config(text=f"00:{self.t1_counter:02d}")
            self.t1_counter -= 1
            self.root.after(1000, self.update_t1_timer)
        else:
            self.lbl_t1_timer.config(text="00:00")
            self.snapshot_offline = self.get_current_devices()
            self.lbl_t1_status.config(text="Слепок сделан.\nВСТАВЬТЕ ресивер обратно, подождите 3 сек и нажмите ОК.", foreground="#5cb85c")
            self.btn_t1_ok.pack(pady=10)

    def finish_vid_pid_test(self):
        self.root.update()
        current_devices = self.get_current_devices()
        new_devices = current_devices - self.snapshot_offline
        
        if not new_devices:
            messagebox.showwarning("Ошибка", "Новые устройства не найдены. Попробуйте еще раз.")
            self.btn_t1_start.config(state=tk.NORMAL)
            self.btn_t1_ok.pack_forget()
            return
            
        vid, pid = list(new_devices)[0]
        self.target_vid, self.target_pid = vid, pid
        
        self.btn_t1_ok.pack_forget()
        self.lbl_t1_timer.config(text="")
        self.lbl_t1_status.config(text="Устройство успешно найдено!", foreground="black")
        self.lbl_t1_result.pack(pady=10)
        self.lbl_t1_result.config(text=f"VID: {hex(vid)} | PID: {hex(pid)}")
        
        self.notebook.tab(self.tab2, state="normal")
        self.notebook.select(self.tab2)

    # --- ВКЛАДКА 2: Эвристический анализ ---
    def setup_tab2(self):
        ttk.Label(self.tab2, text="Сейчас программа попытается найти байт заряда батареи.", font=("Arial", 11, "bold")).pack(pady=10)
        
        lbl_instruct = ttk.Label(self.tab2, text="Инструкция:\n1. Нажмите кнопку «Начать сканирование».\n2. В течение следующих 7 секунд АКТИВНО шевелите мышью\nи нажимайте все кнопки (это отфильтрует лишний шум).", justify="center")
        lbl_instruct.pack(pady=10)
        
        ttk.Label(self.tab2, text="Если знаете текущий заряд (из родной программы), введите его:\n(если не знаете — просто оставьте поле пустым)", justify="center").pack(pady=(10, 0))
        self.entry_known_bat = ttk.Entry(self.tab2, width=10, justify="center")
        self.entry_known_bat.pack(pady=5)
        
        self.lbl_t2_timer = ttk.Label(self.tab2, text="", font=("Arial", 20, "bold"), foreground="#007bff")
        self.lbl_t2_timer.pack(pady=5)
        
        self.btn_t2_start = ttk.Button(self.tab2, text="Начать сканирование", command=self.start_heuristic)
        self.btn_t2_start.pack(pady=10)
        
        self.progress = ttk.Progressbar(self.tab2, mode="indeterminate")

    def start_heuristic(self):
        self.btn_t2_start.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, padx=20, pady=10)
        self.progress.start(10)
        
        known_str = self.entry_known_bat.get().strip()
        self.target_battery_val = int(known_str) if known_str.isdigit() else None
        
        # Запускаем в отдельном потоке, чтобы не вешать GUI
        threading.Thread(target=self.run_scan_logic, daemon=True).start()

    def run_scan_logic(self):
        devices = hid.enumerate(self.target_vid, self.target_pid)
        # Отсекаем стандартные мыши (обычно usage_page = 1, 2, 9)
        suspects = [d for d in devices if d['usage_page'] > 0x09]
        
        if not suspects:
            self.root.after(0, self.fail_heuristic, "Не найдено сервисных каналов (Usage Page).")
            return
            
        found_candidates_dict = {}
        
        for duration in range(7, 0, -1):
            self.root.after(0, self.lbl_t2_timer.config, {"text": f"Шевелите мышью! Осталось: {duration} сек"})
            time.sleep(1)
            
        self.root.after(0, self.lbl_t2_timer.config, {"text": "Анализ данных..."})

        # Эвристика: перебираем каналы и отмычки
        for dev in suspects:
            try:
                h = hid.device()
                h.open_path(dev['path'])
                h.set_nonblocking(True)
                
                for packet in MAGIC_PACKETS:
                    stable_bytes = {i: {"val": None, "noise": False} for i in range(64)}
                    
                    # Спамим запросом и читаем 2 секунды
                    end_time = time.time() + 2.0
                    got_data = False
                    
                    while time.time() < end_time:
                        h.write(packet)
                        time.sleep(0.05)
                        
                        while True:
                            data = h.read(64)
                            if not data: break
                            got_data = True
                            
                            for i, val in enumerate(data):
                                if stable_bytes[i]["noise"]: continue
                                if stable_bytes[i]["val"] is None:
                                    stable_bytes[i]["val"] = val
                                elif stable_bytes[i]["val"] != val:
                                    stable_bytes[i]["noise"] = True # Значение прыгает -> это шум
                                    
                    # Если канал ответил, фильтруем результаты
                    if got_data:
                        report_id = stable_bytes[0]["val"]
                        
                        # Ищем только в первых 12 байтах. Дальше идет системный мусор
                        for i in range(1, 12):
                            if not stable_bytes[i]["noise"]:
                                val = stable_bytes[i]["val"]
                                # Заряд от 2 до 100 (1 отбрасываем, это часто просто флаг)
                                if val is not None and 2 <= val <= 100:
                                    # Жесткий фильтр, если юзер вписал заряд
                                    if self.target_battery_val is not None:
                                        if abs(val - self.target_battery_val) > 1:
                                            continue
                                    
                                    # Уникальный ключ: Страница + Индекс байта + Значение
                                    # Это убирает дубликаты, если разные отмычки выдают один и тот же мусор!
                                    key = (dev['usage_page'], i, val)
                                    
                                    if key not in found_candidates_dict:
                                        # Считаем "рейтинг доверия" (эвристика)
                                        score = 0
                                        # Типичный Compx / Beken (Report ID 3, Байт 4)
                                        if report_id == 3 and i == 4: score += 10
                                        # Типичный SinoWealth (Report ID 4, Байт 3, 4 или 6)
                                        elif report_id == 4 and i in [3, 4, 6]: score += 8
                                        # В целом заряд чаще в первых 8 байтах
                                        elif i < 8: score += 2
                                        
                                        found_candidates_dict[key] = {
                                            "usage_page": dev['usage_page'],
                                            "packet": packet,
                                            "index": i,
                                            "value": val,
                                            "report_id": report_id,
                                            "score": score
                                        }
                h.close()
            except Exception as e:
                continue

        self.root.after(0, self.finish_heuristic, found_candidates_dict)

    def fail_heuristic(self, reason):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn_t2_start.config(state=tk.NORMAL)
        self.lbl_t2_timer.config(text="")
        messagebox.showerror("Ошибка сканирования", reason)

    def finish_heuristic(self, candidates_dict):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn_t2_start.config(state=tk.NORMAL)
        self.lbl_t2_timer.config(text="Готово!")
        
        # Превращаем словарь в список и сортируем по рейтингу доверия (лучшие сверху)
        cands = list(candidates_dict.values())
        cands.sort(key=lambda x: x["score"], reverse=True)
        
        self.candidates = cands
        
        if not self.candidates:
            self.fail_heuristic("Программа не смогла найти стабильный байт заряда (2-100%).\nВозможно, мышь была в спящем режиме.")
            return
            
        self.notebook.tab(self.tab3, state="normal")
        self.notebook.select(self.tab3)
        self.populate_tab3()

    # --- ВКЛАДКА 3: Сохранение профиля ---
    def setup_tab3(self):
        ttk.Label(self.tab3, text="Найдены возможные значения заряда:", font=("Arial", 11, "bold")).pack(pady=10)
        ttk.Label(self.tab3, text="Программа отсортировала вероятные значения (звездочки - лучшие).\nВыберите правильный вариант и нажмите Сохранить.", justify="center").pack()
        
        self.listbox = tk.Listbox(self.tab3, font=("Courier", 11), height=8)
        self.listbox.pack(fill=tk.BOTH, padx=20, pady=10, expand=True)
        
        self.btn_save = ttk.Button(self.tab3, text="Сохранить профиль мыши", command=self.save_profile)
        self.btn_save.pack(pady=10)

    def populate_tab3(self):
        self.listbox.delete(0, tk.END)
        for i, c in enumerate(self.candidates):
            # Добавляем звездочки для рекомендуемых вариантов
            if c['score'] >= 10:
                prefix = "[★ ИДЕАЛЬНО]"
            elif c['score'] >= 8:
                prefix = "[⭐ ХОРОШО]  "
            else:
                prefix = "[?] Сомнение  "
                
            text = f"{prefix} Вариант {i+1} | Заряд: {c['value']}% (Байт {c['index']})"
            self.listbox.insert(tk.END, text)
            
            # Раскрашиваем идеальные варианты в зеленый/синий
            if c['score'] >= 10:
                self.listbox.itemconfig(i, {'fg': 'green'})
            elif c['score'] >= 8:
                self.listbox.itemconfig(i, {'fg': 'blue'})
                
        # Автоматически выбираем первый (самый вероятный) вариант
        if self.candidates:
            self.listbox.selection_set(0)

    def save_profile(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите один из вариантов в списке!")
            return
            
        idx = selection[0]
        chosen = self.candidates[idx]
        
        profile = {
            "vid": self.target_vid,
            "pid": self.target_pid,
            "usage_page": chosen['usage_page'],
            "magic_packet": chosen['packet'],
            "battery_index": chosen['index']
        }
        
        save_path = os.path.join(get_base_path(), "mouse_profile.json")
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=4)
            messagebox.showinfo("Успех", f"Профиль успешно сохранен в файл:\n{save_path}\n\nТеперь можно закрыть сканер и настроить основную программу.")
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Ошибка записи", f"Не удалось сохранить файл: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MouseScannerApp(root)
    root.mainloop()