# 🦈 Attack Shark Mouse Battery Notifier (RU)

**Небольшая утилита**, которая спасает от самого раздражающего момента — когда мышь внезапно разряжается в разгар работы или игры.
<img width="1280" height="960" alt="Mouse Notifier" src="https://github.com/user-attachments/assets/9951f5b4-7913-4b44-9868-bc7788423a97" />

---

## ⚙️ Описание

Данная микро-утилита создана для тех, кто:

* не любит, когда мышь разряжается в самый неподходящий момент 😤
* не хочет постоянно вручную проверять уровень заряда

Программа автоматически следит за состоянием батареи и уведомляет вас заранее.

---

## 🧠 Логика работы

* Вы задаёте несколько порогов заряда (в процентах)
* При достижении этих значений появляются уведомления 🔔
* В уведомлении отображается текущий уровень заряда

👉 Всё просто: настроил один раз — и забыл

---

## ✨ Дополнительные возможности

* 📊 **Просмотр заряда**
  Просто наведите курсор на иконку в трее, чтобы увидеть текущий процент

* 🖥️ **GUI-интерфейс**
  Уровень заряда также отображается в окне программы

* ⏱️ **Статистика работы**
  Отслеживание времени работы мыши от одного заряда

  > При зарядке выше 95% статистика автоматически сбрасывается

* 💬 **Кастомный текст уведомлений**
  Можно задать свой текст, который будет отображаться вместе с процентом заряда

* 🦈 **Иконка акулы**
  Потому что… ну а почему бы и нет 🙂

---

## 🔌 Поддержка устройств

На данный момент утилита работает с мышками от **Attack Shark**, а также, *в теории*, с аналогичными устройствами на том же железе.

---

## 🚧 Планы на будущее

Поддержка других мышек возможна, но сейчас идёт разбор того, как это корректно реализовать.
Так что всё ещё в процессе — но направление есть.

---

## 📦 Зависимости

### Для работы скрипта:

* **hid** — взаимодействие с USB-устройствами
* **pystray** — работа с иконкой и меню в системном трее
* **Pillow** — обработка изображений (иконки)

### Для сборки в `.exe`:

* **pyinstaller** — компиляция скрипта в исполняемый файл

### 🚀 Быстрая установка:

```bash
pip install hid pystray Pillow pyinstaller
```

### 📄 requirements.txt:

```txt
hid
pystray
Pillow
```

---

# 🦈 Attack Shark Mouse Battery Notifier (EN)

**A small utility** that saves you from the most annoying moment — when your mouse suddenly dies during work or gaming.

---

## ⚙️ Description

This micro-utility is designed for those who:

* hate when their mouse runs out of battery at the worst possible time 😤
* don’t want to constantly check the battery level manually

The program automatically monitors the battery status and notifies you in advance.

---

## 🧠 How it works

* You set several battery thresholds (in percentages)
* Notifications appear when those levels are reached 🔔
* The current battery level is shown in the notification

👉 Simple: set it once — forget about it

---

## ✨ Features

* 📊 **Battery status preview**
  Hover over the tray icon to see the current percentage

* 🖥️ **GUI interface**
  Battery level is also displayed in the application window

* ⏱️ **Usage statistics**
  Tracks mouse usage time per charge

  > Resets automatically after charging above 95%

* 💬 **Custom notification text**
  Set your own message to display with the battery percentage

* 🦈 **Shark icon**
  Because… why not 🙂

---

## 🔌 Device Support

Currently supports **Attack Shark** mice and, *in theory*, similar devices with the same hardware.

---

## 🚧 Future Plans

Support for other mice may be added later.
Currently exploring how to implement this properly.

---

## 📦 Requirements

### For running the script:

* **hid** — USB device interaction
* **pystray** — system tray icon and menu
* **Pillow** — image processing (icons)

### For building `.exe`:

* **pyinstaller** — compile the script into an executable

### 🚀 Quick install:

```bash
pip install hid pystray Pillow pyinstaller
```

### 📄 requirements.txt:

```txt
hid
pystray
Pillow
```

---

# 🦈 Attack Shark Mouse Battery Notifier (UA)

**Невелика утиліта**, яка рятує від найнеприємнішого моменту — коли миша раптово розряджається під час роботи або гри.

---

## ⚙️ Опис

Ця мікро-утиліта створена для тих, хто:

* не любить, коли миша розряджається у найневдаліший момент 😤
* не хоче постійно вручну перевіряти рівень заряду

Програма автоматично відстежує стан батареї та завчасно повідомляє вас.

---

## 🧠 Як це працює

* Ви задаєте кілька порогів заряду (у відсотках)
* При досягненні цих значень з’являються сповіщення 🔔
* У сповіщенні відображається поточний рівень заряду

👉 Все просто: налаштував один раз — і забув

---

## ✨ Можливості

* 📊 **Перегляд заряду**
  Наведіть курсор на іконку в треї, щоб побачити поточний відсоток

* 🖥️ **GUI-інтерфейс**
  Рівень заряду також відображається у вікні програми

* ⏱️ **Статистика роботи**
  Відстеження часу роботи миші від одного заряду

  > Скидається автоматично після зарядки вище 95%

* 💬 **Кастомний текст сповіщень**
  Можна задати власний текст разом із відсотком заряду

* 🦈 **Іконка акули**
  Бо… чому б і ні 🙂

---

## 🔌 Підтримка пристроїв

Наразі утиліта працює з мишками **Attack Shark**, а також, *теоретично*, з подібними пристроями на тому ж залізі.

---

## 🚧 Плани на майбутнє

Можлива підтримка інших мишок у майбутньому.
Зараз триває дослідження, як це правильно реалізувати.

---

## 📦 Залежності

### Для роботи скрипта:

* **hid** — взаємодія з USB-пристроями
* **pystray** — робота з іконкою та меню в системному треї
* **Pillow** — обробка зображень (іконки)

### Для збірки в `.exe`:

* **pyinstaller** — компіляція скрипта у виконуваний файл

### 🚀 Швидке встановлення:

```bash
pip install hid pystray Pillow pyinstaller
```

### 📄 requirements.txt:

```txt
hid
pystray
Pillow
```
