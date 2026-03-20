# VidMark
# Copyright (C) 2026 qexela
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Project build script for VidMark EXE generation.
Automatically finds dependencies, generates icon, builds EXE and computes checksums.
Supports Russian and English languages.
"""

import os
import sys
import shutil
import subprocess
import hashlib
import time
import struct
import argparse
import re
import locale
from datetime import datetime
from typing import List, Optional, Dict

# ════════════════════ CONFIGURATION ════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
ICON_NAME = "icon.ico"
ICON_PATH = os.path.join(ASSETS_DIR, ICON_NAME)

# Add project root to path for config import
sys.path.insert(0, PROJECT_ROOT)

# Attempt to load config (safe: config no longer creates dirs on import)
try:
    from config import APP_NAME
    PROJECT_NAME = APP_NAME
except ImportError:
    PROJECT_NAME = os.path.basename(PROJECT_ROOT) or "VidMark"

# Executable extension
EXE_EXT = ".exe" if sys.platform.startswith("win") else ""
EXE_NAME = f"{PROJECT_NAME}{EXE_EXT}"
EXE_PATH = os.path.join(DIST_DIR, EXE_NAME)

# Icon settings
ICON_COLOR = (52, 152, 219)  # #3498db
ICON_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

# Subdirectories to scan for imports
PROJECT_PACKAGES = ["core", "ui", "utils", "workers"]


def default_ui_mode() -> str:
    """Choose default UI mode based on platform.
    Windows -> windowed (no console), Linux/macOS -> console."""
    return "windowed" if sys.platform.startswith("win") else "console"


def resolve_ui_mode(args) -> str:
    """Resolve UI mode. Priority: explicit flag > debug > platform default."""
    if getattr(args, "console", False):
        return "console"
    if getattr(args, "windowed", False):
        return "windowed"
    if getattr(args, "debug", False):
        return "console"
    return default_ui_mode()


# ════════════════════ LOCALIZATION ════════════════════

CURRENT_LANG = "en"

LANG: Dict[str, Dict[str, str]] = {
    "ru": {
        "menu_title": "Сборщик проекта",
        "menu_root": "Корень",
        "menu_entry": "Вход",
        "menu_icon": "Иконка",
        "menu_exe": "EXE",
        "menu_choice": "Ваш выбор",
        "opt_build": "Собрать EXE",
        "opt_regen_icon": "Перегенерировать иконку",
        "opt_clean_build": "Очистить build/ (временные файлы)",
        "opt_clean_dist": "Очистить dist/ (готовые файлы)",
        "opt_clean_all": "Очистить всё",
        "opt_checksums": "Показать SHA-256 хеши",
        "opt_change_lang": "Change language / Сменить язык",
        "opt_exit": "Выход",
        "status_yes": "Есть",
        "status_no": "Нет",
        "status_not_built": "не собран",
        "status_not_found": "НЕ НАЙДЕН",
        "checking_pyinstaller": "Проверка PyInstaller...",
        "pyinstaller_found": "PyInstaller найден",
        "pyinstaller_not_found": "PyInstaller не найден!",
        "pyinstaller_install_prompt": "Установить автоматически через pip? (y/n)",
        "pyinstaller_installed": "PyInstaller установлен",
        "pyinstaller_install_failed": "Не удалось установить PyInstaller",
        "generating_icon": "Генерация иконки",
        "icon_created_pillow": "Иконка создана (Pillow)",
        "icon_created_fallback": "Иконка создана (Fallback struct)",
        "icon_create_failed": "Не удалось создать иконку",
        "cleaning_build": "Очистка build/ и кэша...",
        "cleaning_dist": "Очистка dist/...",
        "temp_files_cleaned": "Временные файлы очищены",
        "dist_cleaned": "Папка dist очищена",
        "clean_error": "Ошибка очистки",
        "starting_pyinstaller": "ЗАПУСК PYINSTALLER",
        "building": "Сборка",
        "entry_point": "Точка входа",
        "icon_label": "Иконка",
        "yes": "Да",
        "no": "Нет",
        "build_complete": "Сборка завершена за",
        "sec": "сек",
        "file_label": "Файл",
        "size_label": "Размер",
        "build_error": "Сборка завершилась с ошибкой!",
        "last_errors": "ПОСЛЕДНИЕ ОШИБКИ (STDERR)",
        "full_log": "Полный лог",
        "build_timeout": "Превышено время ожидания сборки (10 мин)",
        "critical_error": "Критическая ошибка",
        "entry_not_found": "Точка входа (main.py) не найдена!",
        "press_enter": "Нажмите Enter для продолжения...",
        "goodbye": "До свидания!",
        "ready_files": "Готовые файлы здесь",
        "invalid_choice": "Неверный выбор",
        "select_language": "Выберите язык / Select language",
        "lang_option_ru": "Русский",
        "lang_option_en": "English",
        "operation_cancelled": "Операция прервана пользователем",
        "scanning_imports": "Сканирование импортов...",
        "found_imports": "Найдено скрытых импортов",
        "checksum_title": "SHA-256 КОНТРОЛЬНЫЕ СУММЫ",
        "checksum_saved": "Сохранено в",
        "checksum_no_files": "В dist/ нет файлов",
        "checksum_no_dist": "Папка dist/ не найдена. Сначала соберите EXE",
        "checksum_computing": "Вычисление контрольных сумм...",
        "checksum_github": "Для GitHub Release Notes",
        "checksum_verify_ps": "Проверка (PowerShell)",
        "checksum_verify_bash": "Проверка (Linux/macOS)",
    },
    "en": {
        "menu_title": "Project Builder",
        "menu_root": "Root",
        "menu_entry": "Entry",
        "menu_icon": "Icon",
        "menu_exe": "EXE",
        "menu_choice": "Your choice",
        "opt_build": "Build EXE",
        "opt_regen_icon": "Regenerate icon",
        "opt_clean_build": "Clean build/ (temp files)",
        "opt_clean_dist": "Clean dist/ (output files)",
        "opt_clean_all": "Clean all",
        "opt_checksums": "Show SHA-256 checksums",
        "opt_change_lang": "Change language / Сменить язык",
        "opt_exit": "Exit",
        "status_yes": "Yes",
        "status_no": "No",
        "status_not_built": "not built",
        "status_not_found": "NOT FOUND",
        "checking_pyinstaller": "Checking PyInstaller...",
        "pyinstaller_found": "PyInstaller found",
        "pyinstaller_not_found": "PyInstaller not found!",
        "pyinstaller_install_prompt": "Install automatically via pip? (y/n)",
        "pyinstaller_installed": "PyInstaller installed",
        "pyinstaller_install_failed": "Failed to install PyInstaller",
        "generating_icon": "Generating icon",
        "icon_created_pillow": "Icon created (Pillow)",
        "icon_created_fallback": "Icon created (Fallback struct)",
        "icon_create_failed": "Failed to create icon",
        "cleaning_build": "Cleaning build/ and cache...",
        "cleaning_dist": "Cleaning dist/...",
        "temp_files_cleaned": "Temp files cleaned",
        "dist_cleaned": "Dist folder cleaned",
        "clean_error": "Clean error",
        "starting_pyinstaller": "STARTING PYINSTALLER",
        "building": "Building",
        "entry_point": "Entry point",
        "icon_label": "Icon",
        "yes": "Yes",
        "no": "No",
        "build_complete": "Build complete in",
        "sec": "sec",
        "file_label": "File",
        "size_label": "Size",
        "build_error": "Build finished with error!",
        "last_errors": "LAST ERRORS (STDERR)",
        "full_log": "Full log",
        "build_timeout": "Build timeout exceeded (10 min)",
        "critical_error": "Critical error",
        "entry_not_found": "Entry point (main.py) not found!",
        "press_enter": "Press Enter to continue...",
        "goodbye": "Goodbye!",
        "ready_files": "Ready files here",
        "invalid_choice": "Invalid choice",
        "select_language": "Выберите язык / Select language",
        "lang_option_ru": "Русский",
        "lang_option_en": "English",
        "operation_cancelled": "Operation cancelled by user",
        "scanning_imports": "Scanning imports...",
        "found_imports": "Hidden imports found",
        "checksum_title": "SHA-256 CHECKSUMS",
        "checksum_saved": "Saved to",
        "checksum_no_files": "No files in dist/",
        "checksum_no_dist": "dist/ not found. Build EXE first",
        "checksum_computing": "Computing checksums...",
        "checksum_github": "For GitHub Release Notes",
        "checksum_verify_ps": "Verify (PowerShell)",
        "checksum_verify_bash": "Verify (Linux/macOS)",
    }
}


def t(key: str) -> str:
    """Get localized string by key."""
    return LANG.get(CURRENT_LANG, LANG["en"]).get(key, key)


def detect_system_language() -> str:
    """Detect system language based on locale or keyboard layouts."""
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            num_layouts = user32.GetKeyboardLayoutList(0, None)
            if num_layouts > 0:
                layout_ids = (ctypes.c_void_p * num_layouts)()
                user32.GetKeyboardLayoutList(num_layouts, layout_ids)
                for lid in layout_ids:
                    if (lid & 0xFFFF if lid else 0) == 0x0419:
                        return "ru"
        except Exception:
            pass

    try:
        loc = locale.getdefaultlocale()[0] or ""
        if loc.lower().startswith("ru"):
            return "ru"
    except Exception:
        pass

    return "en"


def set_language(lang: str):
    """Set current language."""
    global CURRENT_LANG
    if lang in LANG:
        CURRENT_LANG = lang


def prompt_language_selection():
    """Prompt user to select language."""
    print(f"\n🌐 {t('select_language')}")
    print(f"   [1] {t('lang_option_ru')}")
    print(f"   [2] {t('lang_option_en')}")
    choice = input("   > ").strip()
    if choice == "1":
        set_language("ru")
    elif choice == "2":
        set_language("en")


# ════════════════════ UI HELPERS ════════════════════

def clear_screen():
    """Clear console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(text: str):
    """Print header with decorations."""
    print(f"\n{'═' * 60}")
    print(f"   {text}")
    print(f"{'═' * 60}")


def print_section(text: str):
    """Print section divider."""
    print(f"\n{'─' * 60}")
    print(f" {text}")
    print(f"{'─' * 60}")


def print_success(text: str):
    print(f"✅ {text}")


def print_error(text: str):
    print(f"❌ {text}")


def print_warn(text: str):
    print(f"⚠  {text}")


def print_info(text: str):
    print(f"ℹ️  {text}")


def pause():
    """Wait for user to press Enter."""
    input(f"\n⏎ {t('press_enter')}")


def get_file_info(path: str) -> str:
    """Get file info string (size and modification date)."""
    if not os.path.exists(path):
        return t("status_not_built")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    mtime = os.path.getmtime(path)
    date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    return f"{size_mb:.2f} MB | {date_str}"


# ════════════════════ CHECKSUM ════════════════════

def sha256_file(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_checksums(show_github: bool = True) -> bool:
    """Compute and display SHA-256 checksums for all files in dist/.
    Saves checksums.txt and optionally prints GitHub-ready format."""
    if not os.path.exists(DIST_DIR):
        print_error(t("checksum_no_dist"))
        return False

    files = sorted([
        f for f in os.listdir(DIST_DIR)
        if os.path.isfile(os.path.join(DIST_DIR, f))
        and not f.endswith(".txt")
    ])

    if not files:
        print_error(t("checksum_no_files"))
        return False

    print_info(f"⏳ {t('checksum_computing')}")
    print_section(t("checksum_title"))

    lines = []
    for filename in files:
        filepath = os.path.join(DIST_DIR, filename)
        file_hash = sha256_file(filepath)
        size_mb = os.path.getsize(filepath) / (1024 * 1024)

        line = f"{file_hash}  {filename}"
        lines.append(line)

        print(f"\n  📦 {filename}")
        print(f"  🔑 {file_hash}")
        print(f"  📏 {size_mb:.1f} MB")

    # Save checksums.txt
    checksum_path = os.path.join(DIST_DIR, "checksums.txt")
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n{'─' * 60}")
    print_success(f"{t('checksum_saved')}: {checksum_path}")

    if show_github:
        print(f"\n📋 {t('checksum_github')}:\n")
        print("```text")
        for line in lines:
            print(line)
        print("```")

        print(f"\n{t('checksum_verify_ps')}:")
        print("```powershell")
        for filename in files:
            print(f'Get-FileHash "{filename}" -Algorithm SHA256 | Format-List')
        print("```")

        print(f"\n{t('checksum_verify_bash')}:")
        print("```bash")
        print("sha256sum -c checksums.txt")
        print("```")

    return True


# ════════════════════ BUILD LOGIC ════════════════════

def find_entry_point() -> Optional[str]:
    """Find entry point (main.py, __main__.py, or vidmark.py)."""
    candidates = ["main.py", "__main__.py", "vidmark.py"]
    for c in candidates:
        path = os.path.join(PROJECT_ROOT, c)
        if os.path.exists(path):
            return path
    return None


def check_pyinstaller() -> bool:
    """Check PyInstaller availability and offer to install if missing."""
    print_info(f"⏳ {t('checking_pyinstaller')}")
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True, check=True
        )
        print_success(t("pyinstaller_found"))
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warn(t("pyinstaller_not_found"))
        choice = input(f"   {t('pyinstaller_install_prompt')}: ").strip().lower()
        if choice in ('y', 'д', 'yes', 'да'):
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "pyinstaller"],
                    check=True
                )
                print_success(t("pyinstaller_installed"))
                return True
            except subprocess.CalledProcessError:
                print_error(t("pyinstaller_install_failed"))
                return False
        return False


def generate_icon_pillow(path: str) -> bool:
    """Generate application icon using Pillow library."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False

    try:
        img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([10, 10, 246, 246], radius=40, fill=ICON_COLOR)

        letter = PROJECT_NAME[0].upper()
        try:
            font = ImageFont.truetype("arial.ttf", 180)
        except IOError:
            font = ImageFont.load_default()

        draw.text((128, 128), letter, font=font, fill="white", anchor="mm")
        img.save(path, format='ICO', sizes=ICON_SIZES)
        return True
    except Exception as e:
        print_warn(f"Pillow error: {e}")
        return False


def generate_icon_fallback(path: str) -> bool:
    """Create simple valid ICO file without Pillow (32x32 solid color)."""
    header = struct.pack('<HHH', 0, 1, 1)
    w, h = 32, 32
    bmp_header_size = 40
    pixel_data_size = w * h * 4
    total_size = bmp_header_size + pixel_data_size
    offset = 22

    entry = struct.pack('<BBBBHHII', w, h, 0, 0, 1, 32, total_size, offset)
    bmp_info = struct.pack(
        '<IIIHHIIIIII',
        bmp_header_size, w, h * 2, 1, 32, 0,
        pixel_data_size, 0, 0, 0, 0
    )
    pixel = struct.pack('BBBB', 219, 152, 52, 255)
    pixels = pixel * (w * h)

    try:
        with open(path, 'wb') as f:
            f.write(header + entry + bmp_info + pixels)
        return True
    except Exception as e:
        print_error(f"Fallback icon error: {e}")
        return False


def ensure_assets():
    """Ensure assets directory and icon exist."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    if os.path.exists(ICON_PATH) and os.path.getsize(ICON_PATH) > 0:
        return

    print_info(f"⏳ {t('generating_icon')} {ICON_NAME}...")
    if generate_icon_pillow(ICON_PATH):
        print_success(t("icon_created_pillow"))
    elif generate_icon_fallback(ICON_PATH):
        print_success(t("icon_created_fallback"))
    else:
        print_error(t("icon_create_failed"))


def scan_hidden_imports() -> List[str]:
    """Scan project .py files for imports.
    Scans root AND subdirectory packages (core/, ui/, utils/, workers/)."""
    print_info(f"⏳ {t('scanning_imports')}")
    imports = set()

    # Always-needed hidden imports for PyInstaller
    imports.update([
        "PyQt5.sip", "PyQt5.QtSvg",
        "numpy", "cv2", "pywt",
        "pywt._extensions._pywt",
        "scipy", "scipy.fft", "scipy.fft._pocketfft",
        "qtawesome", "reedsolo",
    ])

    # Standard library and local modules to skip
    stdlib_skip = {
        'os', 'sys', 're', 'time', 'json', 'math', 'hashlib', 'secrets',
        'logging', 'traceback', 'subprocess', 'shutil', 'tempfile', 'uuid',
        'struct', 'argparse', 'locale', 'csv', 'datetime', 'enum',
        'dataclasses', 'typing', '__future__',
        'core', 'ui', 'utils', 'workers', 'config', 'i18n',
    }

    # Collect all .py files from root and subpackages
    py_files = []
    for file in os.listdir(PROJECT_ROOT):
        if file.endswith(".py"):
            py_files.append(os.path.join(PROJECT_ROOT, file))

    for pkg in PROJECT_PACKAGES:
        pkg_dir = os.path.join(PROJECT_ROOT, pkg)
        if os.path.isdir(pkg_dir):
            for file in os.listdir(pkg_dir):
                if file.endswith(".py"):
                    py_files.append(os.path.join(pkg_dir, file))

    # Extract import statements
    for filepath in py_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(r'^(?:from|import)\s+([\w.]+)', content, re.MULTILINE)
                for m in matches:
                    top_level = m.split('.')[0]
                    if top_level not in stdlib_skip:
                        imports.add(m)
        except Exception:
            pass

    result = sorted(imports)
    print_info(f"   {t('found_imports')}: {len(result)}")
    return result


def clean_build_dir():
    """Clean temporary build files, spec files, and Python caches."""
    print_info(f"⏳ {t('cleaning_build')}")
    try:
        if os.path.exists(BUILD_DIR):
            shutil.rmtree(BUILD_DIR)
        for file in os.listdir(PROJECT_ROOT):
            if file.endswith(".spec"):
                os.remove(os.path.join(PROJECT_ROOT, file))
        for root, dirs, files in os.walk(PROJECT_ROOT):
            for d in dirs:
                if d in ("__pycache__", ".pytest_cache", ".mypy_cache"):
                    shutil.rmtree(os.path.join(root, d), ignore_errors=True)
        print_success(t("temp_files_cleaned"))
    except Exception as e:
        print_error(f"{t('clean_error')}: {e}")


def clean_dist_dir():
    """Clean output folder containing built EXE."""
    print_info(f"⏳ {t('cleaning_dist')}")
    try:
        if os.path.exists(DIST_DIR):
            shutil.rmtree(DIST_DIR)
        print_success(t("dist_cleaned"))
    except Exception as e:
        print_error(f"{t('clean_error')}: {e}")


def build_exe(args=None) -> bool:
    """Main build process: scan imports, run PyInstaller, compute checksums."""
    entry_point = find_entry_point()
    if not entry_point:
        print_error(t("entry_not_found"))
        return False

    if not check_pyinstaller():
        return False

    ensure_assets()

    if args is None:
        class _A:
            debug = False
            console = False
            windowed = False
        args = _A()

    ui_mode = resolve_ui_mode(args)
    sep = ";" if sys.platform.startswith("win") else ":"

    hidden_imports = scan_hidden_imports()
    hidden_args = []
    for imp in hidden_imports:
        hidden_args.extend(["--hidden-import", imp])

    add_data = [f"{ASSETS_DIR}{sep}assets"]

    # Check for QSS stylesheet
    style_qss = os.path.join(ASSETS_DIR, "style.qss")
    if not os.path.exists(style_qss):
        print_warn("assets/style.qss not found — app will use default Qt styling")

    # Build PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onefile", "--clean",
        "--name", PROJECT_NAME,
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        "--specpath", BUILD_DIR,
        "--paths", PROJECT_ROOT,
    ]

    cmd.append("--windowed" if ui_mode == "windowed" else "--console")

    if getattr(args, "debug", False):
        cmd += ["--log-level", "DEBUG"]

    if os.path.exists(ICON_PATH):
        cmd.extend(["--icon", ICON_PATH])

    # Collect package data for libraries with runtime files
    cmd += ["--collect-all", "qtawesome"]
    cmd += ["--collect-data", "pywt"]

    cmd.extend(hidden_args)

    for data in add_data:
        cmd.extend(["--add-data", data])

    cmd.append(entry_point)

    # Print build info
    print_section(t("starting_pyinstaller"))
    print(f"🔨 {t('building')}: {PROJECT_NAME}")
    print(f"📂 {t('entry_point')}: {os.path.basename(entry_point)}")
    print(f"🖼️  {t('icon_label')}: {t('yes') if os.path.exists(ICON_PATH) else t('no')}")
    print(f"🎨 style.qss: {'✅' if os.path.exists(style_qss) else '⚠️  missing'}")
    print(f"🧰 UI mode: {ui_mode}")
    print(f"🐞 Debug: {'YES' if getattr(args, 'debug', False) else 'NO'}")
    print(f"📦 Hidden imports: {len(hidden_imports)}")

    os.makedirs(BUILD_DIR, exist_ok=True)
    log_file = os.path.join(BUILD_DIR, "build.log")

    start_time = time.time()

    try:
        with open(log_file, "w", encoding="utf-8") as log:
            process = subprocess.run(
                cmd,
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                timeout=600
            )
            log.write(process.stdout)
            log.write("\n=== STDERR ===\n")
            log.write(process.stderr)

        if process.returncode == 0:
            elapsed = time.time() - start_time
            print_success(f"{t('build_complete')} {elapsed:.1f} {t('sec')}!")
            print(f"📂 {t('file_label')}: {EXE_PATH}")
            if os.path.exists(EXE_PATH):
                size = os.path.getsize(EXE_PATH) / (1024 * 1024)
                print(f"📦 {t('size_label')}: {size:.2f} MB")

            # Auto-compute checksums after successful build
            print()
            compute_checksums(show_github=True)
            return True

        print_error(t("build_error"))
        print_section(t("last_errors"))
        for line in process.stderr.splitlines()[-20:]:
            print(f"  {line}")
        print_info(f"{t('full_log')}: {log_file}")
        return False

    except subprocess.TimeoutExpired:
        print_error(t("build_timeout"))
        return False
    except Exception as e:
        print_error(f"{t('critical_error')}: {e}")
        return False


# ════════════════════ MENU ════════════════════

def interactive_menu():
    """Interactive text menu for build operations."""
    while True:
        clear_screen()
        entry = find_entry_point()
        entry_name = os.path.basename(entry) if entry else f"{t('status_not_found')} ❌"

        icon_status = f"✅ {t('status_yes')}" if os.path.exists(ICON_PATH) else f"❌ {t('status_no')}"
        exe_info = get_file_info(EXE_PATH)
        lang_indicator = "🇷🇺 RU" if CURRENT_LANG == "ru" else "🇬🇧 EN"

        print_header(f"{t('menu_title')}: {PROJECT_NAME} [{lang_indicator}]")
        print(f" 📂 {t('menu_root')}: {PROJECT_ROOT}")
        print(f" 🐍 {t('menu_entry')}:   {entry_name}")
        print(f" 🖼️  {t('menu_icon')}: {icon_status}")
        print(f" 📦 {t('menu_exe')}:    {exe_info}")
        print("-" * 60)
        print(f" 1. 🔨 {t('opt_build')}")
        print(f" 2. 🖼️  {t('opt_regen_icon')}")
        print(f" 3. 🔑 {t('opt_checksums')}")
        print(f" 4. 🧹 {t('opt_clean_build')}")
        print(f" 5. 🧹 {t('opt_clean_dist')}")
        print(f" 6. 🗑  {t('opt_clean_all')}")
        print(f" 7. 🌐 {t('opt_change_lang')}")
        print(f" q. 👋 {t('opt_exit')}")
        print("-" * 60)

        choice = input(f" {t('menu_choice')}: ").strip().lower()

        if choice == '1':
            build_exe()
            pause()
        elif choice == '2':
            if os.path.exists(ICON_PATH):
                os.remove(ICON_PATH)
            ensure_assets()
            pause()
        elif choice == '3':
            compute_checksums(show_github=True)
            pause()
        elif choice == '4':
            clean_build_dir()
            pause()
        elif choice == '5':
            clean_dist_dir()
            pause()
        elif choice == '6':
            clean_build_dir()
            clean_dist_dir()
            pause()
        elif choice == '7':
            prompt_language_selection()
        elif choice in ('q', 'й'):
            print(f"\n👋 {t('goodbye')}")
            if os.path.exists(DIST_DIR) and os.listdir(DIST_DIR):
                print(f"📂 {t('ready_files')}: {DIST_DIR}")
                if sys.platform == 'win32':
                    os.startfile(DIST_DIR)
            break
        else:
            print_warn(t("invalid_choice"))
            time.sleep(1)


def main():
    """Entry point: parse CLI args or launch interactive menu."""
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} Builder")
    parser.add_argument("--build", action="store_true", help="Build EXE without menu")
    parser.add_argument("--clean", action="store_true", help="Clean build folder")
    parser.add_argument("--clean-all", action="store_true", help="Clean everything")
    parser.add_argument("--checksums", action="store_true", help="Show SHA-256 checksums")
    parser.add_argument("--lang", choices=["ru", "en"], help="Set language (ru/en)")
    parser.add_argument("--debug", action="store_true", help="Debug build (forces console mode)")
    ui_group = parser.add_mutually_exclusive_group()
    ui_group.add_argument("--console", action="store_true", help="Force console mode")
    ui_group.add_argument("--windowed", action="store_true", help="Force windowed mode (no console)")

    args = parser.parse_args()

    if args.lang:
        set_language(args.lang)
    else:
        set_language(detect_system_language())

    os.makedirs(ASSETS_DIR, exist_ok=True)

    if args.build:
        build_exe(args)
    elif args.clean:
        clean_build_dir()
    elif args.clean_all:
        clean_build_dir()
        clean_dist_dir()
    elif args.checksums:
        compute_checksums(show_github=True)
    else:
        prompt_language_selection()
        interactive_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n👋 {t('operation_cancelled')}")
        sys.exit(0)