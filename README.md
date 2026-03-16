<div align="center">

# 🛡️ VidMark — Video Watermark Shield

> Video watermarking tool using DWT-DCT with QIM.

**🌐 [Русская версия (Russian)](#-vidmark--Защита-Видео-Водяными-Знаками)**

<!-- Technologies -->
[![Release](https://img.shields.io/github/v/release/qexela/VidMark?logo=github&color=blue)](https://github.com/qexela/VidMark/releases)
[![License](https://img.shields.io/badge/License-GPLv3-blue?logo=gnu)](https://github.com/qexela/VidMark/blob/main/LICENSE)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-41CD52?logo=qt&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-5C3EE8?logo=opencv&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-007808?logo=ffmpeg&logoColor=white)

<!-- Stats -->
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?logo=windows&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-30%2B%20passed-34c759?logo=pytest&logoColor=white)

<img src="screenshots/embed.png" width="85%" alt="VidMark main window with embedded watermark preview">

</div>

---

## 📋 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Screenshots](#-screenshots)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Building EXE](#-building-exe)
- [Scripts](#-scripts)
- [FAQ](#-faq)
- [Platforms](#-platforms)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)

---

## 📖 About

**VidMark** is a desktop application for embedding digital watermarks into video files.
It uses a combination of **Discrete Wavelet Transform (DWT)** and **Discrete Cosine Transform (DCT)**
with **Quantization Index Modulation (QIM)** to hide digital signatures that survive common
video processing operations like compression, noise addition, and filtering.

This project was developed as part of a university facultative course. It demonstrates practical application of frequency-domain
watermarking techniques with a GUI, error correction, and attack robustness testing.

**Key highlights:**
1. **High visual quality** — PSNR typically > 44 dB (imperceptible to human eye)
2. **Robust extraction** — survives H.264/H.265 compression, noise, filtering, geometric transforms
3. **Reed-Solomon ECC** — corrects bit errors from lossy compression
4. **Multi-frame voting** — extracts watermark from multiple frames for reliability
5. **Comprehensive testing** — built-in attack simulator with 30+ distortion types
6. **Bilingual UI** — English and Russian interface

---

## ✨ Features

### 🔒 Watermarking
- **DWT-DCT-QIM** — frequency-domain embedding in LL subband DCT coefficients
- **Adjustable strength** — Invisible / Balanced / Robust presets or custom delta
- **Unique per-video seed** — XOR of base seed + UUID + timestamp for security
- **Auto key file generation** — JSON key file required for extraction

### 🔍 Extraction & Verification
- **Multi-frame majority voting** — extracts from N uniformly sampled frames
- **Reed-Solomon error correction** — recovers data from corrupted bits
- **CRC-16 integrity check** — validates payload after extraction
- **SYNC marker detection** — confirms watermark presence before parsing

### 🧪 Attack Testing
- **30+ attack types** — compression, noise, filtering, geometric, color transforms
- **H.264/H.265 simulation** — real FFmpeg encode/decode per frame
- **NC/BER/PSNR metrics** — per-attack quality and extraction metrics
- **CSV export** — save results for analysis

### 📊 Quality Metrics
- **PSNR** — Peak Signal-to-Noise Ratio
- **SSIM** — Structural Similarity Index
- **NC** — Normalized Correlation
- **BER** — Bit Error Rate

### 🎨 User Interface
- **Light macOS-inspired theme** — clean, modern QSS-based styling
- **Real-time preview** — original and watermarked frame comparison
- **Detailed logging** — timestamped operation log with export
- **Settings dialog** — wavelet/level/block/delta/CRF with compatibility hints

---

## 📸 Screenshots

<img src="screenshots/embed.png" width="80%" alt="embed">

*embed*

<details>
<summary>🖼️ <b>Show all screenshots (6)</b></summary>

### 🖼️ attacktest
<img src="screenshots/attacktest.png" width="80%" alt="attacktest">

### 🖼️ extract
<img src="screenshots/extract.png" width="80%" alt="extract">

### 🖼️ log
<img src="screenshots/log.png" width="80%" alt="log">

### 🖼️ settings
<img src="screenshots/settings.png" width="80%" alt="settings">

### 🖼️ success
<img src="screenshots/success.png" width="80%" alt="success">

</details>

---

## 📋 Requirements

| Component        | Version       | Purpose                                    |
|:-----------------|:--------------|:-------------------------------------------|
| Python           | 3.9+          | Runtime                                    |
| FFmpeg           | 4.4+          | Video encoding/decoding, audio handling    |
| ffprobe          | (with FFmpeg) | Video metadata extraction                  |
| ffplay           | (with FFmpeg) | Video preview playback (optional)          |

### ⚠️ FFmpeg is mandatory

VidMark requires **`ffmpeg`, `ffprobe` and `ffplay`** to be installed and available in your system `PATH`.
The application will show an error dialog and exit if FFmpeg is not found.

**FFmpeg is used for:**
- Encoding watermarked video with H.264/H.265/VP9 codecs
- Audio stream copy from original to watermarked video
- A/V timestamp normalization for problematic clips
- Attack simulation (H.264/H.265 compression attacks)
- Video metadata detection via ffprobe (audio streams, format, duration)
- Video preview playback via ffplay (optional, right-click on preview)

**Install FFmpeg:**

| Platform | Command                                                                    |
|:---------|:---------------------------------------------------------------------------|
| Windows  | Download from [ffmpeg.org](https://ffmpeg.org/download.html), add to PATH  |
| macOS    | `brew install ffmpeg`                                                      |
| Ubuntu   | `sudo apt install ffmpeg`                                                  |
| Arch     | `sudo pacman -S ffmpeg`                                                    |

---

## 🚀 Installation

```bash
git clone https://github.com/qexela/VidMark.git
cd VidMark

python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

---

## ⚡ Quick Start

```bash
ffmpeg -version
python main.py
```

### Embedding a watermark

1. Open the **Embed** tab
2. Click **Browse** and select a video file
3. *(Optional)* Enter author name/ID
4. Click **Start** and choose output file location
5. Wait for processing — metrics will appear in the preview panel
6. **Save the key file** (`.json`) — it's required for extraction! — ⚠️ Keep this safe! Verification is impossible without it.

### Extracting & verifying

1. Open the **Extract** tab
2. Select the watermarked video
3. Select the corresponding key file (`.json`)
4. Click **Extract & Verify**
5. Check the result: ✅ VERIFIED / ⚠️ MISMATCH / ❌ NOT FOUND

---

## 🔬 How It Works

```text
┌─────────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Input Frame │────▶│   DWT   │────▶│ LL band │────▶│  DCT    │
│  (Y channel)│     │ (Haar)  │     │         │     │ (8x8)   │
└─────────────┘     └─────────┘     └─────────┘     └────┬────┘
                                                         │
                    ┌─────────┐     ┌─────────┐     ┌────▼────┐
                    │ Output  │◀────│  IDWT   │◀────│  QIM    │
                    │  Frame  │     │         │     │ Embed   │
                    └─────────┘     └─────────┘     └─────────┘
```

### ⚠️ Key File is Critical

The key file stores the **exact embedding parameters** including the unique scramble seed.
Without it, the watermark **cannot be recovered**. **Always back up your key files!**

---

## 📂 Project Structure

<details>
<summary>📂 <b>Expand file tree</b></summary>

```text
VidMark/
├── 🚀 main.py                     # Application entry point
├── ⚙️ config.py                   # Global configuration
├── 🌐 i18n.py                     # Internationalization (EN/RU)
├── 📋 requirements.txt
├── 📖 README.md
├── 📜 LICENSE                     # GPLv3
├── 🙈 .gitignore
│
├── 📁 core/                       # Watermarking algorithms
│   ├── 🔧 embedder.py             # DWT-DCT-QIM embedding
│   ├── 🔍 extractor.py            # DWT-DCT-QIM extraction
│   ├── 🛡️ ecc.py                  # Reed-Solomon ECC
│   ├── 🔀 scrambler.py            # Bit scrambling
│   ├── 📦 payload.py              # Payload formation & parsing
│   ├── 📊 metrics.py              # PSNR, SSIM, NC, BER
│   ├── 🧪 attacks.py              # Attack simulator
│   └── 🔑 keyfile.py              # Key file management
│
├── 📁 ui/                         # PyQt5 GUI
│   ├── 🏠 main_window.py
│   ├── 📥 embed_tab.py
│   ├── 📤 extract_tab.py
│   ├── 🧪 attack_tab.py
│   ├── 📋 log_tab.py
│   └── ⚙️ settings_dialog.py
│
├── 📁 workers/                    # Background threads
│   └── 🔄 video_worker.py
│
├── 📁 utils/                      # Utilities
│   ├── 🎬 video_utils.py          # Video I/O, FFmpeg
│   └── 🖼️ image_utils.py          # Image conversion
│
├── 📁 assets/
│   ├── 🎨 icon.ico
│   └── 🎨 style.qss
│
├── 📁 scripts/
│   ├── 🔨 build.py
│   ├── 📖 generate_readme.py
│   └── 🧹 clean.bat / clean.sh / clean.ps1
│
├── 📁 tests/
│   └── 🧪 test_*.py (10 modules, 30+ tests)
│
└── 📁 screenshots/
```

</details>

---

## ⚙️ Configuration

### Strength Presets

| Preset        | Delta | PSNR (typical) | Robustness | Use Case              |
|:--------------|:-----:|:--------------:|:-----------|:----------------------|
| Invisible     | 20.0  | > 48 dB        | Lower      | Proof of ownership    |
| **Balanced**  | 35.0  | ~44-46 dB      | Good       | General (default)     |
| Robust        | 55.0  | ~40-43 dB      | Maximum    | Hostile environments  |

### Wavelet Compatibility

| Wavelet  | Level 1      | Level 2     | Min Delta  |
|:---------|:------------:|:-----------:|:----------:|
| **haar** | ✅ Excellent | ⚠️ Doubtful | 25+       |
| db2      | ✅ Excellent | ⚠️ Doubtful | 30+       |
| db4      | ⚠️ Doubtful  | ⚠️ Doubtful | 40+       |
| bior4.4  | ⚠️ Doubtful  | ✅ Excellent| 30+       |
| coif2    | ❌ Poor      | ❌ Poor     | 60+       |

---

## 🧪 Testing

```bash
pytest tests/ -v
python tests/test_cli.py
```

---

## 📦 Building EXE

```bash
python scripts/build.py              # Interactive menu
python scripts/build.py --build      # Direct build
python scripts/build.py --build --console  # With console
```

---

## 🧹 Scripts

```bash
./scripts/clean.sh          # Linux/macOS
scripts\clean.bat           # Windows CMD
```

---

## ❓ FAQ

### How do I install FFmpeg on Windows?
Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, add `bin/` to PATH.

### Why does extraction fail?
Wrong key file, heavy compression (CRF > 28), or large geometric attacks.

### Can I watermark audio?
No, VidMark watermarks video stream only. Audio is copied as-is.

### What if I lose the key file?
**The watermark cannot be recovered.** Always back up key files.

### Can I use this commercially?
Yes, provided you comply with the **GNU GPLv3** (e.g., disclosing source code).

---

## 💻 Platforms

| Platform           | Status | Notes                   |
|:-------------------|:------:|:------------------------|
| Windows 10/11      | ✅     | Full support, EXE build |
| macOS 12+          | ✅     | Full support            |
| Linux (Ubuntu 20+) | ✅     | Full support            |

---

## 🤝 Contributing

This project was created as a university assignment and is open for educational contributions.

1. Fork the repository
2. Create your branch: `git checkout -b feature/improvement`
3. Commit: `git commit -m 'Add improvement'`
4. Push: `git push origin feature/improvement`
5. Open a Pull Request

---

## 📜 License

**GNU General Public License v3.0**

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ⚠️ Disclose Source

See [LICENSE](LICENSE) for full text.

---

## 🙏 Acknowledgements

- [PyWavelets](https://pywavelets.readthedocs.io/) — wavelet transforms
- [SciPy](https://scipy.org/) — DCT/IDCT
- [OpenCV](https://opencv.org/) — video I/O
- [FFmpeg](https://ffmpeg.org/) — video encoding
- [reedsolo](https://github.com/tomerfiliba/reedsolomon) — Reed-Solomon ECC
- [PyQt5](https://riverbankcomputing.com/software/pyqt/) — GUI framework (GPLv3 licensed)
- [QtAwesome](https://github.com/spyder-ide/qtawesome) — icon fonts
- [Big Buck Bunny](https://peach.blender.org/) — sample video (CC BY 3.0)

---

<div align="center">

*© 2026 [qexela](https://github.com/qexela) — Licensed under GPLv3*

</div>

---

<div align="center">

# VidMark — Защита Видео Водяными Знаками

> Инструмент встраивания ЦВЗ в видео методом DWT-DCT с QIM.

**🌐 [English version](#️-vidmark--video-watermark-shield)**

</div>

---

## 📋 Содержание

- [О проекте](#-о-проекте)
- [Возможности](#-возможности)
- [Скриншоты](#-скриншоты-1)
- [Требования](#-требования)
- [Установка](#-установка)
- [Быстрый старт](#-быстрый-старт)
- [Как это работает](#-как-это-работает)
- [Структура проекта](#-структура-проекта)
- [Конфигурация](#-конфигурация)
- [Тестирование](#-тестирование)
- [Сборка EXE](#-сборка-exe)
- [Скрипты](#-скрипты)
- [FAQ](#-faq-1)
- [Платформы](#-платформы)
- [Участие в проекте](#-участие-в-проекте)
- [Лицензия](#-лицензия)
- [Благодарности](#-благодарности)

---

## 📖 О проекте

**VidMark** — десктопное приложение для встраивания цифровых водяных знаков в видеофайлы.
Используется комбинация **дискретного вейвлет-преобразования (DWT)** и **дискретного косинусного
преобразования (DCT)** с **квантовой индексной модуляцией (QIM)** для скрытия цифровых подписей,
устойчивых к сжатию, шуму и фильтрации.

Проект создан в рамках университетского факультатива. Демонстрирует практическое применение
частотных методов ЦВЗ с графическим интерфейсом, коррекцией ошибок и тестированием устойчивости к атакам.

**Ключевые особенности:**
1. **Высокое визуальное качество** — PSNR обычно > 44 дБ (незаметно для глаза)
2. **Устойчивое извлечение** — выдерживает H.264/H.265 сжатие, шум, фильтрацию, геометрические преобразования
3. **Коды Рида-Соломона** — исправляют битовые ошибки после сжатия с потерями
4. **Голосование по кадрам** — извлечение из нескольких кадров для надёжности
5. **Комплексное тестирование** — встроенный симулятор с 30+ типами атак
6. **Двуязычный интерфейс** — английский и русский

---

## ✨ Возможности

### 🔒 Встраивание
- **DWT-DCT-QIM** — встраивание в частотной области в коэффициенты DCT подполосы LL
- **Настраиваемая интенсивность** — пресеты Невидимый / Баланс / Устойчивый или ручная дельта
- **Уникальный seed** — XOR базового seed + UUID + timestamp для безопасности
- **Автоматическая генерация ключа** — JSON-файл ключа обязателен для извлечения

### 🔍 Извлечение и проверка
- **Мажоритарное голосование** — извлечение из N равномерно выбранных кадров
- **Коды Рида-Соломона** — восстановление данных из повреждённых бит
- **Проверка CRC-16** — валидация целостности после извлечения
- **SYNC-маркер** — подтверждение наличия водяного знака перед парсингом

### 🧪 Тестирование устойчивости к атакам
- **30+ типов атак** — сжатие, шум, фильтрация, геометрия, цветовые преобразования
- **Симуляция H.264/H.265** — реальное кодирование/декодирование через FFmpeg
- **Метрики NC/BER/PSNR** — для каждой атаки
- **Экспорт в CSV** — сохранение результатов для анализа

### 📊 Метрики качества
- **PSNR** — пиковое отношение сигнал/шум
- **SSIM** — индекс структурного сходства
- **NC** — нормализованная корреляция
- **BER** — коэффициент битовых ошибок

### 🎨 Интерфейс
- **Светлая тема в стиле macOS** — чистый, современный QSS-стиль
- **Предпросмотр в реальном времени** — сравнение оригинала и водяного знака
- **Подробное журналирование** — журнал операций с временными метками и экспортом
- **Диалог настроек** — вейвлет/уровень/блок/дельта/CRF с подсказками совместимости

---

## 📸 Скриншоты

<img src="screenshots/embed.png" width="80%" alt="embed">

*embed*

<details>
<summary>🖼️ <b>Показать все скриншоты (6)</b></summary>

### 🖼️ attacktest
<img src="screenshots/attacktest.png" width="80%" alt="attacktest">

### 🖼️ extract
<img src="screenshots/extract.png" width="80%" alt="extract">

### 🖼️ log
<img src="screenshots/log.png" width="80%" alt="log">

### 🖼️ settings
<img src="screenshots/settings.png" width="80%" alt="settings">

### 🖼️ success
<img src="screenshots/success.png" width="80%" alt="success">

</details>

---

## 📋 Требования

| Компонент   | Версия        | Назначение                                |
|:------------|:--------------|:------------------------------------------|
| Python      | 3.9+          | Среда выполнения                          |
| FFmpeg      | 4.4+          | Кодирование/декодирование видео           |
| ffprobe     | (с FFmpeg)    | Извлечение метаданных видео               |
| ffplay      | (с FFmpeg)    | Предпросмотр видео (опционально)          |

### ⚠️ FFmpeg обязателен

VidMark требует **`ffmpeg`, `ffprobe` и `ffplay`** в системном `PATH`.
Приложение покажет ошибку и завершится, если FFmpeg не найден.

**FFmpeg используется для:**
- Кодирования видео кодеками H.264/H.265/VP9
- Копирования аудиодорожки из оригинала
- Нормализации временных меток A/V для проблемных клипов
- Симуляции атак сжатием (H.264/H.265)
- Определения метаданных видео через ffprobe (аудиопотоки, формат, длительность)
- Предпросмотра видео через ffplay (опционально, правый клик на превью)

**Установка FFmpeg:**

| Платформа | Команда                                                                   |
|:----------|:--------------------------------------------------------------------------|
| Windows   | Скачать с [ffmpeg.org](https://ffmpeg.org/download.html), добавить в PATH |
| macOS     | `brew install ffmpeg`                                                     |
| Ubuntu    | `sudo apt install ffmpeg`                                                 |
| Arch      | `sudo pacman -S ffmpeg`                                                   |

---

## 🚀 Установка

```bash
git clone https://github.com/qexela/VidMark.git
cd VidMark

python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

---

## ⚡ Быстрый старт

```bash
ffmpeg -version
python main.py
```

### Встраивание водяного знака

1. Откройте вкладку **Встраивание**
2. Нажмите **Обзор** и выберите видеофайл
3. *(Опционально)* Введите имя/ID автора
4. Нажмите **Старт** и выберите путь для сохранения
5. Дождитесь обработки — метрики появятся на панели предпросмотра
6. **Сохраните файл ключа** (`.json`) — он необходим для извлечения! — ⚠️ Не теряйте его! Без этого файла подтвердить авторство невозможно.

### Извлечение и проверка

1. Откройте вкладку **Извлечение**
2. Выберите видео с водяным знаком
3. Выберите соответствующий файл ключа (`.json`)
4. Нажмите **Извлечь и проверить**
5. Проверьте результат: ✅ ПОДТВЕРЖДЕНО / ⚠️ НЕСОВПАДЕНИЕ / ❌ НЕ НАЙДЕН

---

## 🔬 Как это работает

```text
┌─────────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Входной     │────▶│   DWT   │────▶│ LL полоса│────▶│  DCT  │
│ кадр (Y)    │     │ (Haar)  │     │         │     │ (8x8)   │
└─────────────┘     └─────────┘     └─────────┘     └────┬────┘
                                                         │
                    ┌─────────┐     ┌─────────┐     ┌────▼────┐
                    │ Выходной│◀────│  IDWT   │◀────│  QIM   │
                    │  кадр   │     │         │     │ Встр.   │
                    └─────────┘     └─────────┘     └─────────┘
```

### ⚠️ Файл с ключами критически важен

файл ключа хранит **точные параметры встраивания**, включая уникальный seed скремблирования.
Без него водяной знак **невозможно восстановить**. **Всегда создавайте резервные копии!**

---

## 📂 Структура проекта

<details>
<summary>📂 <b>Развернуть дерево файлов</b></summary>

```text
VidMark/
├── 🚀 main.py                     # Точка входа
├── ⚙️ config.py                   # Глобальная конфигурация
├── 🌐 i18n.py                     # Интернационализация (EN/RU)
├── 📋 requirements.txt
├── 📖 README.md
├── 📜 LICENSE                     # GPLv3
├── 🙈 .gitignore
│
├── 📁 core/                       # Алгоритмы ЦВЗ
│   ├── 🔧 embedder.py             # Встраивание DWT-DCT-QIM
│   ├── 🔍 extractor.py            # Извлечение DWT-DCT-QIM
│   ├── 🛡️ ecc.py                  # Коды Рида-Соломона
│   ├── 🔀 scrambler.py            # Скремблирование бит
│   ├── 📦 payload.py              # Формирование и разбор полезной нагрузки
│   ├── 📊 metrics.py              # PSNR, SSIM, NC, BER
│   ├── 🧪 attacks.py              # Симулятор атак
│   └── 🔑 keyfile.py              # Управление ключевыми файлами
│
├── 📁 ui/                         # Интерфейс PyQt5
│   ├── 🏠 main_window.py
│   ├── 📥 embed_tab.py
│   ├── 📤 extract_tab.py
│   ├── 🧪 attack_tab.py
│   ├── 📋 log_tab.py
│   └── ⚙️ settings_dialog.py
│
├── 📁 workers/                    # Фоновые потоки
│   └── 🔄 video_worker.py
│
├── 📁 utils/                      # Утилиты
│   ├── 🎬 video_utils.py          # Видео I/O, FFmpeg
│   └── 🖼️ image_utils.py          # Конвертация изображений
│
├── 📁 assets/
│   ├── 🎨 icon.ico
│   └── 🎨 style.qss
│
├── 📁 scripts/
│   ├── 🔨 build.py
│   ├── 📖 generate_readme.py
│   └── 🧹 clean.bat / clean.sh / clean.ps1
│
├── 📁 tests/
│   └── 🧪 test_*.py (10 модулей, 30+ тестов)
│
└── 📁 screenshots/
```

</details>

---

## ⚙️ Конфигурация

### Пресеты силы

| Пресет        | Дельта | PSNR (типично) | Устойчивость | Применение                 |
|:--------------|:------:|:--------------:|:-------------|:---------------------------|
| Невидимый     | 20.0   | > 48 дБ        | Ниже         | Доказательство авторства   |
| **Баланс**    | 35.0   | ~44-46 дБ      | Хорошая      | Общее (по умолчанию)       |
| Устойчивый    | 55.0   | ~40-43 дБ      | Максимальная | Агрессивные условия        |

### Совместимость вейвлетов

| Вейвлет  | Уровень 1      | Уровень 2       | Мин. дельта |
|:---------|:--------------:|:---------------:|:-----------:|
| **haar** | ✅ Отлично     | ⚠️ Сомнительно  | 25+         |
| db2      | ✅ Отлично     | ⚠️ Сомнительно  | 30+         |
| db4      | ⚠️ Сомнительно | ⚠️ Сомнительно  | 40+         |
| bior4.4  | ⚠️ Сомнительно | ✅ Отлично      | 30+         |
| coif2    | ❌ Плохо       | ❌ Плохо        | 60+         |

---

## 🧪 Тестирование

```bash
pytest tests/ -v
python tests/test_cli.py
```

---

## 📦 Сборка EXE

```bash
python scripts/build.py              # Интерактивное меню
python scripts/build.py --build      # Прямая сборка
python scripts/build.py --build --console  # С консолью
```

---

## 🧹 Скрипты

```bash
./scripts/clean.sh          # Linux/macOS
scripts\clean.bat           # Windows CMD
```

---

## ❓ FAQ

### Как установить FFmpeg на Windows?
Скачайте с [ffmpeg.org](https://ffmpeg.org/download.html), распакуйте, добавьте `bin/` в PATH.

### Почему извлечение не работает?
Неверный файл ключа, сильное сжатие (CRF > 28) или большие геометрические искажения.

### Можно ли ставить водяной знак на аудио?
Нет, VidMark работает только с видеопотоком. Аудио копируется как есть.

### Что если я потеряю файл с ключами?
**Водяной знак будет невозможно восстановить.** Всегда делайте резервные копии.

### Можно ли использовать коммерчески?
Да, при соблюдении условий **GNU GPLv3** (например, открытие исходного кода).

---

## 💻 Платформы

| Платформа          | Статус | Примечания                 |
|:-------------------|:------:|:---------------------------|
| Windows 10/11      | ✅     | Полная поддержка, EXE-сборка |
| macOS 12+          | ✅     | Полная поддержка           |
| Linux (Ubuntu 20+) | ✅     | Полная поддержка           |

---

## 🤝 Участие в проекте

Проект создан как университетское задание и открыт для образовательных вкладов.

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/improvement`
3. Коммит: `git commit -m 'Добавлено улучшение'`
4. Пуш: `git push origin feature/improvement`
5. Откройте Pull Request

---

## 📜 Лицензия

**GNU General Public License v3.0**

- ✅ Коммерческое использование
- ✅ Модификация
- ✅ Распространение
- ✅ Частное использование
- ⚠️ Раскрытие исходного кода

См. [LICENSE](LICENSE).

---

## 🙏 Благодарности

- [PyWavelets](https://pywavelets.readthedocs.io/) — вейвлет-преобразования
- [SciPy](https://scipy.org/) — DCT/IDCT
- [OpenCV](https://opencv.org/) — работа с видео
- [FFmpeg](https://ffmpeg.org/) — кодирование видео
- [reedsolo](https://github.com/tomerfiliba/reedsolomon) — коды Рида-Соломона
- [PyQt5](https://riverbankcomputing.com/software/pyqt/) — GUI-фреймворк (GPLv3 лицензия)
- [QtAwesome](https://github.com/spyder-ide/qtawesome) — шрифты иконок
- [Big Buck Bunny](https://peach.blender.org/) — тестовое видео (CC BY 3.0)

---

<div align="center">

*© 2026 [qexela](https://github.com/qexela) — Лицензия GPLv3*

</div>
