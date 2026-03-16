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
VidMark - Internationalization (i18n)
"""
import os
from config import get_saved_language, save_language, LANGUAGE_FILE

_TRANSLATIONS = {
    "app_title": {
        "en": "VidMark v{version}",
        "ru": "VidMark v{version}",
    },
    "ready": {"en": "Ready", "ru": "Готово"},
    "cancel": {"en": "Cancel", "ru": "Отмена"},
    "close": {"en": "Close", "ru": "Закрыть"},
    "settings": {"en": " Settings", "ru": " Настройки"},
    "language": {"en": "Language", "ru": "Язык"},
    "language_short": {"en": "Lang", "ru": "Язык"},
    "start": {"en": " Start", "ru": " Старт"},
    "stop_short": {"en": " Stop", "ru": " Стоп"},
    "settings_short": {"en": " Settings", "ru": " Настройки"},
    "tab_embed": {"en": "Embed", "ru": "Встраивание"},
    "tab_extract": {"en": "Extract", "ru": "Извлечение"},
    "tab_attack": {"en": "Attack Test", "ru": "Тест атак"},
    "tab_metrics": {"en": "Metrics", "ru": "Метрики"},
    "tab_log": {"en": "Log", "ru": "Журнал"},
    "tab_about": {"en": "About", "ru": "О проекте"},
    "input_video": {"en": "INPUT VIDEO", "ru": "ВХОДНОЕ ВИДЕО"},
    "select_input_video": {
        "en": "Select input video file...",
        "ru": "Выберите входной видеофайл..."},
    "browse": {"en": " Browse", "ru": " Обзор"},
    "no_video_loaded": {"en": "No video loaded", "ru": "Видео не загружено"},
    "watermark_payload": {"en": "WATERMARK DATA", "ru": "ДАННЫЕ ВОДЯНОГО ЗНАКА"},
    "author_id": {"en": "Author ID:", "ru": "ID автора:"},
    "author_placeholder": {
        "en": "Enter author name/ID (or leave empty for auto UUID)",
        "ru": "Введите имя/ID автора (или оставьте пустым для авто UUID)"},
    "embedding_strength": {"en": "Embedding Strength", "ru": "Сила встраивания"},
    "mode": {"en": "Mode:", "ru": "Режим:"},
    "invisible_desc": {
        "en": "Invisible (PSNR > 48 dB, lower robustness)",
        "ru": "Невидимый (PSNR > 48 дБ, меньше устойчивость)"},
    "balanced_desc": {
        "en": "Balanced (PSNR ~44-46 dB, good robustness)",
        "ru": "Баланс (PSNR ~44-46 дБ, хорошая устойчивость)"},
    "robust_desc": {
        "en": "Robust (PSNR ~40-43 dB, maximum robustness)",
        "ru": "Устойчивый (PSNR ~40-43 дБ, максимальная устойчивость)"},
    "custom_delta": {
        "en": "Custom (set delta manually)",
        "ru": "Пользовательский (задать дельту вручную)"},
    "delta_value": {"en": "Delta value:", "ru": "Значение дельты:"},
    "output_quality": {"en": "Output Quality", "ru": "Качество вывода"},
    "quality": {"en": "Quality:", "ru": "Качество:"},
    "lossless_crf0": {"en": "Lossless (CRF=0)", "ru": "Без потерь (CRF=0)"},
    "high_crf4": {"en": "High (CRF=4)", "ru": "Высокое (CRF=4)"},
    "standard_crf18": {"en": "Standard (CRF=18)", "ru": "Стандартное (CRF=18)"},
    "custom_crf": {
        "en": "Custom (set CRF manually)",
        "ru": "Пользовательский (задать CRF вручную)"},
    "crf_value": {"en": "CRF value:", "ru": "Значение CRF:"},
    "crf_hint": {
        "en": "CRF: 0=lossless, 18=good, 23=default, 28=low, 51=worst",
        "ru": "CRF: 0=без потерь, 18=хорошо, 23=стандарт, 28=низкое, 51=худшее"},
    "preview": {"en": "PREVIEW", "ru": "ПРЕДПРОСМОТР"},
    "original": {"en": "Original", "ru": "Оригинал"},
    "watermarked": {"en": "Watermarked", "ru": "С водяным знаком"},
    "embed_watermark": {"en": " Embed Watermark", "ru": " Встроить водяной знак"},
    "stop": {"en": " Stop", "ru": " Стоп"},
    "save_watermarked_video": {
        "en": "Save Watermarked Video",
        "ru": "Сохранить видео с ЦВЗ"},
    "select_input_video_title": {
        "en": "Select Input Video", "ru": "Выберите входное видео"},
    "video_info_fmt": {
        "en": "{w}×{h} | {fps:.1f} FPS | {fc} frames | {dur:.1f}s | Audio: {audio}",
        "ru": "{w}×{h} | {fps:.1f} к/с | {fc} кадров | {dur:.1f}с | Аудио: {audio}"},
    "error_reading_video": {
        "en": "Error reading video: {e}",
        "ru": "Ошибка чтения видео: {e}"},
    "status_reading_video": {"en": "Reading video...", "ru": "Чтение видео..."},
    "status_processing_frame": {
        "en": "Frame {current}/{total}",
        "ru": "Кадр {current}/{total}"},
    "status_encoding": {"en": "Encoding...", "ru": "Кодирование..."},
    "status_verifying": {"en": "Verifying...", "ru": "Проверка..."},
    "status_done": {"en": "Done!", "ru": "Готово!"},
    "status_cancelled": {"en": "Cancelled", "ru": "Отменено"},
    "status_testing": {"en": "Testing: {name}", "ru": "Тест: {name}"},
    "status_complete": {"en": "Complete", "ru": "Завершено"},
    "status_extracting_frame": {
        "en": "Frame {current}/{total}",
        "ru": "Кадр {current}/{total}"},
    "instructions": {"en": "Instructions", "ru": "Инструкция"},
    "extraction": {"en": "Extraction", "ru": "Извлечение"},
    "extract_instructions_html": {
        "en": (
            "<h3>How to Extract and Verify a Watermark</h3>"
            "<b>Step 1.</b> Select the watermarked video file.<br>"
            "<b>Step 2.</b> Select the corresponding key file (.json).<br>"
            "<b>Step 3.</b> Click 'Extract & Verify'.<br><br>"
            "<h3>What the System Does</h3>"
            "• Extracts the hidden watermark from multiple frames<br>"
            "• Performs majority voting across frames<br>"
            "• Applies Reed-Solomon error correction<br>"
            "• Compares UUID and timestamp with the key file<br>"
            "• Verifies CRC integrity<br><br>"
            "<h3>Results</h3>"
            " <font color='#34c759'><b>VERIFIED</b></font> — All checks passed.<br>"
            " <font color='#ff9500'><b>MISMATCH</b></font> — Key file doesn't match.<br>"
            " <font color='#ff3b30'><b>NOT FOUND</b></font> — No watermark detected.<br><br>"
            "<b>Key file is REQUIRED</b> for extraction."
        ),
        "ru": (
            "<h3>Как извлечь и проверить водяной знак</h3>"
            "<b>Шаг 1.</b> Выберите видео с водяным знаком.<br>"
            "<b>Шаг 2.</b> Выберите ключевой файл (.json).<br>"
            "<b>Шаг 3.</b> Нажмите 'Извлечь и проверить'.<br><br>"
            "<h3>Что делает система</h3>"
            "• Извлекает водяной знак из нескольких кадров<br>"
            "• Выполняет мажоритарное голосование<br>"
            "• Применяет код Рида-Соломона<br>"
            "• Сравнивает UUID и временную метку с ключом<br>"
            "• Проверяет целостность CRC<br><br>"
            "<h3>Результаты</h3>"
            " <font color='#34c759'><b>ПОДТВЕРЖДЕНО</b></font> — Все проверки пройдены.<br>"
            " <font color='#ff9500'><b>НЕСОВПАДЕНИЕ</b></font> — Ключ не совпадает.<br>"
            " <font color='#ff3b30'><b>НЕ НАЙДЕН</b></font> — ЦВЗ не обнаружен.<br><br>"
            "<b>Ключевой файл ОБЯЗАТЕЛЕН</b> для извлечения."
        ),
    },
    "watermarked_video": {"en": "WATERMARKED VIDEO", "ru": "ВИДЕО С ЦВЗ"},
    "select_watermarked_video": {
        "en": "Select watermarked video...",
        "ru": "Выберите видео с ЦВЗ..."},
    "key_file": {"en": "KEY FILE (.json)", "ru": "КЛЮЧЕВОЙ ФАЙЛ (.json)"},
    "select_key_file": {
        "en": "Select key file...",
        "ru": "Выберите ключевой файл..."},
    "extract_verify": {"en": " Extract & Verify", "ru": " Извлечь и проверить"},
    "verification_results": {
        "en": "VERIFICATION RESULTS",
        "ru": "РЕЗУЛЬТАТЫ ПРОВЕРКИ"},
    "no_extraction": {
        "en": "No extraction performed yet",
        "ru": "Извлечение ещё не выполнено"},
    "author": {"en": "Author", "ru": "Автор"},
    "auto_uuid": {"en": "(auto UUID)", "ru": "(авто UUID)"},
    "uuid_video": {"en": "UUID (video):", "ru": "UUID (видео):"},
    "uuid_key": {"en": "UUID (key):", "ru": "UUID (ключ):"},
    "uuid_match": {"en": "UUID match:", "ru": "Совпадение UUID:"},
    "time_video": {"en": "Time (video):", "ru": "Время (видео):"},
    "time_key": {"en": "Time (key):", "ru": "Время (ключ):"},
    "time_match": {"en": "Time match:", "ru": "Совпадение времени:"},
    "yes": {"en": "YES", "ru": "ДА"},
    "no": {"en": "NO", "ru": "НЕТ"},
    "no_key_modified": {
        "en": "NO — key file may be modified!",
        "ru": "НЕТ — ключевой файл мог быть изменён!"},
    "crc": {"en": "CRC:", "ru": "CRC:"},
    "ecc": {"en": "ECC:", "ru": "ECC:"},
    "ecc_ok": {"en": "OK", "ru": "OK"},
    "ecc_failed": {"en": "Failed", "ru": "Ошибка"},
    "confidence": {"en": "Confidence:", "ru": "Достоверность:"},
    "sync": {"en": "Sync:", "ru": "Синхр.:"},
    "extracted_data": {"en": "Extracted Data", "ru": "Извлечённые данные"},
    "no_data": {"en": "No Data", "ru": "Нет данных"},
    "select_video_title": {"en": "Select Video", "ru": "Выберите видео"},
    "select_key_title": {"en": "Select Key", "ru": "Выберите ключ"},
    "status_verified": {
        "en": " WATERMARK VERIFIED — Author Confirmed!",
        "ru": " ВОДЯНОЙ ЗНАК ПОДТВЕРЖДЁН — Автор подтверждён!"},
    "status_ts_mismatch": {
        "en": " WATERMARK FOUND — Timestamp mismatch!",
        "ru": " ЦВЗ НАЙДЕН — Несовпадение времени!"},
    "status_uuid_mismatch": {
        "en": " WATERMARK FOUND — UUID mismatch!",
        "ru": " ЦВЗ НАЙДЕН — Несовпадение UUID!"},
    "status_damaged": {
        "en": " WATERMARK DAMAGED — CRC failed",
        "ru": " ЦВЗ ПОВРЕЖДЁН — Ошибка CRC"},
    "status_not_found": {
        "en": " WATERMARK NOT FOUND",
        "ru": " ВОДЯНОЙ ЗНАК НЕ НАЙДЕН"},
    "select_all": {"en": " Select All", "ru": " Выбрать все"},
    "deselect_all": {"en": " Deselect All", "ru": " Снять все"},
    "run_attack_tests": {"en": " Run Attack Tests", "ru": " Запустить тесты атак"},
    "select_attacks": {"en": "SELECT ATTACKS", "ru": "ВЫБЕРИТЕ АТАКИ"},
    "results": {"en": "RESULTS", "ru": "РЕЗУЛЬТАТЫ"},
    "attack": {"en": "Attack", "ru": "Атака"},
    "attack_psnr": {"en": "Attack PSNR (dB)", "ru": "PSNR атаки (дБ)"},
    "status": {"en": "Status", "ru": "Статус"},
    "save_extraction_results": {
        "en": "Save extraction results to folder",
        "ru": "Сохранить результаты извлечения в папку"},
    "save_type": {"en": "Save:", "ru": "Сохранить:"},
    "save_data_image": {"en": "Data visualization", "ru": "Визуализация данных"},
    "select_save_folder": {"en": "Select folder...", "ru": "Выберите папку..."},
    "browse_folder": {"en": " Folder", "ru": " Папка"},
    "select_folder_title": {"en": "Select Folder", "ru": "Выберите папку"},
    "wm_saved_to": {
        "en": "Extraction results saved to: {path}",
        "ru": "Результаты извлечения сохранены в: {path}"},
    "attack_test_complete": {
        "en": "Attack testing complete!",
        "ru": "Тестирование атак завершено!"},
    "cat_compression": {"en": "Compression", "ru": "Сжатие"},
    "cat_noise": {"en": "Noise", "ru": "Шум"},
    "cat_filtering": {"en": "Filtering", "ru": "Фильтрация"},
    "cat_geometric": {"en": "Geometric", "ru": "Геометрия"},
    "cat_color": {"en": "Color", "ru": "Цвет"},
    "cat_no_attack": {"en": "No Attack", "ru": "Без атаки"},
    "embedding_metrics": {"en": "Embedding Metrics", "ru": "Метрики встраивания"},
    "all_metrics": {"en": "All Metrics", "ru": "Все метрики"},
    "time_elapsed": {"en": "Time:", "ru": "Время:"},
    "video_information": {"en": "Video Information", "ru": "Информация о видео"},
    "no_video_info": {
        "en": "No video info yet. Embed first.",
        "ru": "Нет информации. Сначала встройте ЦВЗ."},
    "watermark_information": {
        "en": "Watermark Information",
        "ru": "Информация о ЦВЗ"},
    "copy_clipboard": {"en": " Copy to Clipboard", "ru": " Копировать"},
    "copy_table": {"en": "Copy Table", "ru": "Копировать таблицу"},
    "export_file": {"en": " Export to File", "ru": " Экспорт в файл"},
    "clear": {"en": " Clear", "ru": " Очистить"},
    "export_log_title": {"en": "Export Log", "ru": "Экспорт журнала"},

    "settings_title": {"en": "Settings", "ru": "Настройки"},
    "settings_tab_params": {"en": "⚙️ Parameters", "ru": "⚙️ Параметры"},
    "settings_tab_instructions": {"en": "📖 Instructions", "ru": "📖 Инструкция"},
    "preset": {"en": "Preset:", "ru": "Пресет:"},
    "custom": {"en": "Custom", "ru": "Пользовательский"},
    "wavelet_transform": {"en": "Wavelet Transform", "ru": "Вейвлет-преобразование"},
    "wavelet": {"en": "Wavelet:", "ru": "Вейвлет:"},
    "level": {"en": "Level:", "ru": "Уровень:"},
    "block": {"en": "Block:", "ru": "Блок:"},
    "security": {"en": "Security", "ru": "Безопасность"},
    "key": {"en": "Key:", "ru": "Ключ:"},
    "arnold_iter": {"en": "Arnold iter:", "ru": "Итер. Арнольда:"},
    "error_correction": {"en": "Error Correction", "ru": "Коррекция ошибок"},
    "rs_symbols": {"en": "RS symbols:", "ru": "RS символов:"},
    "frames": {"en": "Frames:", "ru": "Кадров:"},
    "good_combination": {"en": "Excellent combination", "ru": "Отличная комбинация"},
    "use_with_caution": {
        "en": "Doubtful — use with caution",
        "ru": "Сомнительно — используйте с осторожностью"},
    "not_recommended_may_fail": {
        "en": "Poor — NOT recommended, may fail!",
        "ru": "Плохо — НЕ рекомендуется, может не работать!"},
    "min_recommended_delta": {
        "en": "Min recommended delta:",
        "ru": "Мин. рекомендуемая дельта:"},
    "settings_instructions_html": {
        "en": (
            "<h3>Settings Guide</h3>"
            "<p>The DWT-DCT method embeds watermark bits into mid-frequency "
            "DCT coefficients of the DWT LL subband.</p>"
            "<table border='1' cellpadding='6' cellspacing='0' "
            "style='border-collapse:collapse;width:100%;'>"
            "<tr style='background:#f0f0f5;'><th>Parameter</th><th>Description</th>"
            "<th style='color:#34c759;'>Excellent</th>"
            "<th style='color:#ff9500;'>Doubtful</th>"
            "<th style='color:#ff3b30;'>Poor</th></tr>"
            "<tr><td><b>Wavelet</b></td><td>Transform type</td>"
            "<td style='color:#34c759;'>haar, db2</td>"
            "<td style='color:#ff9500;'>db4, bior4.4</td>"
            "<td style='color:#ff3b30;'>db6, coif2</td></tr>"
            "<tr><td><b>Level</b></td><td>Decomposition depth</td>"
            "<td style='color:#34c759;'>1</td>"
            "<td style='color:#ff9500;'>2</td>"
            "<td style='color:#ff3b30;'>3</td></tr>"
            "<tr><td><b>Delta</b></td><td>QIM step size</td>"
            "<td style='color:#34c759;'>30-50</td>"
            "<td style='color:#ff9500;'>15-29, 51-80</td>"
            "<td style='color:#ff3b30;'>&lt;10, &gt;100</td></tr>"
            "<tr><td><b>CRF</b></td><td>Output quality</td>"
            "<td style='color:#34c759;'>0-10</td>"
            "<td style='color:#ff9500;'>11-23</td>"
            "<td style='color:#ff3b30;'>&gt;23</td></tr>"
            "</table>"
        ),
        "ru": (
            "<h3>Руководство по настройкам</h3>"
            "<p>Метод DWT-DCT встраивает биты в среднечастотные "
            "DCT коэффициенты LL поддиапазона DWT.</p>"
            "<table border='1' cellpadding='6' cellspacing='0' "
            "style='border-collapse:collapse;width:100%;'>"
            "<tr style='background:#f0f0f5;'><th>Параметр</th><th>Описание</th>"
            "<th style='color:#34c759;'>Отлично</th>"
            "<th style='color:#ff9500;'>Сомнительно</th>"
            "<th style='color:#ff3b30;'>Плохо</th></tr>"
            "<tr><td><b>Вейвлет</b></td><td>Тип преобразования</td>"
            "<td style='color:#34c759;'>haar, db2</td>"
            "<td style='color:#ff9500;'>db4, bior4.4</td>"
            "<td style='color:#ff3b30;'>db6, coif2</td></tr>"
            "<tr><td><b>Уровень</b></td><td>Глубина разложения</td>"
            "<td style='color:#34c759;'>1</td>"
            "<td style='color:#ff9500;'>2</td>"
            "<td style='color:#ff3b30;'>3</td></tr>"
            "<tr><td><b>Дельта</b></td><td>Шаг QIM</td>"
            "<td style='color:#34c759;'>30-50</td>"
            "<td style='color:#ff9500;'>15-29, 51-80</td>"
            "<td style='color:#ff3b30;'>&lt;10, &gt;100</td></tr>"
            "<tr><td><b>CRF</b></td><td>Качество вывода</td>"
            "<td style='color:#34c759;'>0-10</td>"
            "<td style='color:#ff9500;'>11-23</td>"
            "<td style='color:#ff3b30;'>&gt;23</td></tr>"
            "</table>"
        ),
    },
    "log_embedding_start": {
        "en": "EMBEDDING WATERMARK", "ru": "ВСТРАИВАНИЕ ВОДЯНОГО ЗНАКА"},
    "log_extracting_start": {
        "en": "EXTRACTING WATERMARK", "ru": "ИЗВЛЕЧЕНИЕ ВОДЯНОГО ЗНАКА"},
    "log_video_info": {"en": "Video", "ru": "Видео"},
    "log_frames": {"en": "frames", "ru": "кадров"},
    "log_audio": {"en": "Audio", "ru": "Аудио"},
    "log_delta": {"en": "Delta", "ru": "Дельта"},
    "log_timestamp": {"en": "Timestamp", "ru": "Метка времени"},
    "log_payload": {"en": "Payload", "ru": "Данные"},
    "log_bits": {"en": "bits", "ru": "бит"},
    "log_after_ecc": {"en": "After ECC", "ru": "После ECC"},
    "log_wm_bits": {"en": "WM bits", "ru": "Бит ЦВЗ"},
    "log_embedder": {"en": "Embedder", "ru": "Встраиватель"},
    "log_warning": {"en": "WARNING", "ru": "ВНИМАНИЕ"},
    "log_note": {"en": "NOTE", "ru": "ПРИМЕЧАНИЕ"},
    "log_lossless_test": {
        "en": "Quick lossless test...", "ru": "Быстрый тест без потерь..."},
    "log_lossless_nc": {"en": "Lossless NC", "ru": "NC без потерь"},
    "log_low_nc": {
        "en": "LOW NC — consider haar wavelet!",
        "ru": "Низкий NC — рекомендуется haar!"},
    "log_processing_frames": {
        "en": "Processing frames...", "ru": "Обработка кадров..."},
    "log_cannot_open_video": {
        "en": "Cannot open video", "ru": "Не удалось открыть видео"},
    "log_frame": {"en": "Frame", "ru": "Кадр"},
    "log_output_nc": {"en": "Output NC", "ru": "NC на выходе"},
    "log_key_file": {"en": "Key file", "ru": "Ключевой файл"},
    "log_expected_author": {"en": "Expected author", "ru": "Ожидаемый автор"},
    "log_expected_uuid": {"en": "Expected UUID", "ru": "Ожидаемый UUID"},
    "log_expected_time": {"en": "Expected time", "ru": "Ожидаемое время"},
    "log_settings": {"en": "Settings", "ru": "Настройки"},
    "log_frames_to_extract": {
        "en": "Frames to extract", "ru": "Кадров для извлечения"},
    "log_expected_wm_bits": {
        "en": "Expected WM bits", "ru": "Ожидаемых бит ЦВЗ"},
    "log_majority_voting": {
        "en": "Majority voting...", "ru": "Мажоритарное голосование..."},
    "log_descrambling": {
        "en": "Descrambling...", "ru": "Дескремблирование..."},
    "log_ecc_decoding": {
        "en": "ECC decoding...", "ru": "Декодирование ECC..."},
    "log_parsing_payload": {
        "en": "Parsing payload...", "ru": "Разбор данных..."},
    "log_verification": {"en": "VERIFICATION", "ru": "ПРОВЕРКА"},
    "log_extracted_uuid": {"en": "Extracted UUID", "ru": "Извлечённый UUID"},
    "log_extracted_time": {"en": "Extracted time", "ru": "Извлечённое время"},
    "log_result": {"en": "RESULT", "ru": "РЕЗУЛЬТАТ"},
    "log_no_frames": {
        "en": "No frames extracted", "ru": "Кадры не извлечены"},
    "log_attack_testing": {
        "en": "ATTACK TESTING", "ru": "ТЕСТИРОВАНИЕ АТАК"},
    "log_attacks": {"en": "attacks", "ru": "атак"},
    "log_saving_wm_to": {
        "en": "Saving results to", "ru": "Сохранение результатов в"},
    "log_saved_original_wm": {
        "en": "Saved original watermark", "ru": "Сохранён оригинальный ЦВЗ"},
    "success": {"en": "Success", "ru": "Успех"},
    "error": {"en": "Error", "ru": "Ошибка"},
    "not_ready": {"en": "Not Ready", "ru": "Не готово"},
    "embed_first": {
        "en": "Embed a watermark first.",
        "ru": "Сначала встройте водяной знак."},
    "embed_success": {
        "en": "Watermark embedded successfully!",
        "ru": "Водяной знак успешно встроен!"},
    "about_description": {
        "en": "Video Watermark Shield — Invisible video watermarking tool using DWT-DCT with QIM.",
        "ru": "Video Watermark Shield — Инструмент невидимой маркировки видео методом DWT-DCT с QIM."},
    "about_method": {
        "en": "Method: DWT-DCT with QIM (Quantization Index Modulation)",
        "ru": "Метод: DWT-DCT с QIM (квантовая индексная модуляция)"},
    "about_features": {
        "en": "Features",
        "ru": "Возможности"},
    "about_feature_list": {
        "en": (
            "• High quality output (PSNR > 44 dB typically)\n"
            "• Robust against H.264/H.265 compression, noise, filtering\n"
            "• Reed-Solomon error correction\n"
            "• Multi-frame majority voting extraction\n"
            "• Comprehensive attack testing\n"
            "• Bilingual interface (EN/RU)"
        ),
        "ru": (
            "• Высокое качество (PSNR > 44 дБ)\n"
            "• Устойчивость к H.264/H.265, шуму, фильтрации\n"
            "• Коды Рида-Соломона для коррекции ошибок\n"
            "• Извлечение голосованием по нескольким кадрам\n"
            "• Комплексное тестирование атаками\n"
            "• Двуязычный интерфейс (EN/RU)"
        ),
    },
    "change_language": {
        "en": "Change Language",
        "ru": "Сменить язык"},
    "language_switched": {
        "en": "Language switched to English.",
        "ru": "Язык переключён на русский."},
    "reset": {"en": " Reset", "ru": " Сброс"},
    "reset_title": {"en": "Reset", "ru": "Сброс"},
    "reset_all": {"en": "Reset All", "ru": "Сбросить всё"},
    "reset_embed": {"en": "Reset Embed Tab", "ru": "Сбросить вкладку Встраивание"},
    "reset_extract": {"en": "Reset Extract Tab", "ru": "Сбросить вкладку Извлечение"},
    "reset_attack": {"en": "Reset Attack Tab", "ru": "Сбросить вкладку Атаки"},
    "reset_log": {"en": "Reset Log", "ru": "Сбросить журнал"},
    "save_attack_results": {"en": " Save Results", "ru": " Сохранить"},
    "save_results_title": {"en": "Save Attack Results", "ru": "Сохранить результаты атак"},
    "about_btn": {"en": " About", "ru": " О программе"},
    "about_title": {"en": "About", "ru": "О программе"},
    "no_results_to_save": {
        "en": "No results to save. Run attack tests first.",
        "ru": "Нет результатов для сохранения. Сначала запустите тесты атак."},
    "no_attacks_selected": {
        "en": "No attacks selected. Check at least one attack.",
        "ru": "Не выбрано ни одной атаки. Выберите хотя бы одну."},
    "no_video_selected": {
        "en": "No video file selected.",
        "ru": "Видеофайл не выбран."},
    "no_key_selected": {
        "en": "No key file selected.",
        "ru": "Ключевой файл не выбран."},
    "select_video_and_key": {
        "en": "Select both video and key file first.",
        "ru": "Сначала выберите видео и ключевой файл."},
    "ffplay_not_found": {
        "en": "ffplay not found. Install FFmpeg and ensure ffplay is in PATH.",
        "ru": "ffplay не найден. Установите FFmpeg и убедитесь что ffplay в PATH."},
    "preview_original_ffplay": {
        "en": " Preview Original (ffplay)",
        "ru": " Просмотр оригинала (ffplay)"},
    "preview_watermarked_ffplay": {
        "en": " Preview Watermarked (ffplay)",
        "ru": " Просмотр с ЦВЗ (ffplay)"},
    "no_save_folder": {
        "en": "Select a folder to save results first.",
        "ru": "Сначала выберите папку для сохранения."},
    "reset_confirm_title": {
        "en": "Confirm Reset",
        "ru": "Подтверждение сброса"},
    "reset_confirm_message": {
        "en": "Are you sure you want to reset this tab? All data will be lost.",
        "ru": "Вы уверены, что хотите сбросить эту вкладку? Все данные будут потеряны."},
    "reset_confirm_all_message": {
        "en": "Are you sure you want to reset ALL tabs? All data will be lost.",
        "ru": "Вы уверены, что хотите сбросить ВСЕ вкладки? Все данные будут потеряны."},
    "dont_show_again": {
        "en": "Don't show again, clear on click",
        "ru": "Больше не показывать, очистка по нажатию"},
    "clear_confirm_title": {
        "en": "Confirm Clear",
        "ru": "Подтверждение очистки"},
    "clear_confirm_message": {
        "en": "Are you sure you want to clear the log?",
        "ru": "Вы уверены, что хотите очистить журнал?"},
    "log_empty": {
        "en": "Log is empty.",
        "ru": "Журнал пуст."},
    "metric_parameter": {"en": "Parameter", "ru": "Параметр"},
    "metric_value": {"en": "Value", "ru": "Значение"},
    "metric_status_label": {"en": "Status", "ru": "Статус"},
    "reset_extract_tab": {
        "en": " Reset",
        "ru": " Сброс"},
    "reset_attack_tab": {
        "en": " Reset",
        "ru": " Сброс"},
    "status_copied": {
        "en": "Copied to clipboard!",
        "ru": "Скопировано в буфер обмена!"},
    "status_exported": {
        "en": "Exported to file: {path}",
        "ru": "Экспортировано в файл: {path}"},
    "status_log_cleared": {
        "en": "Log cleared",
        "ru": "Журнал очищен"},
    "status_reset_done": {
        "en": "Reset complete",
        "ru": "Сброс выполнен"},
    "status_settings_applied": {
        "en": "Settings applied",
        "ru": "Настройки применены"},
    "status_attacks_saved": {
        "en": "Attack results saved to: {path}",
        "ru": "Результаты атак сохранены в: {path}"},
    "status_folder_selected": {
        "en": "Folder selected: {path}",
        "ru": "Папка выбрана: {path}"},
    "status_video_loaded": {
        "en": "Video loaded: {name}",
        "ru": "Видео загружено: {name}"},
    "status_all_selected": {
        "en": "All attacks selected",
        "ru": "Все атаки выбраны"},
    "status_all_deselected": {
        "en": "All attacks deselected",
        "ru": "Все атаки сняты"},
    # FFmpeg/ffprobe missing
    "ffmpeg_not_found": {
        "en": "FFmpeg not found!\n\nPlease install FFmpeg and add it to your system PATH.\n\nDownload: https://ffmpeg.org/download.html\n\nThe application requires ffmpeg and ffprobe to function properly.",
        "ru": "FFmpeg не найден!\n\nПожалуйста, установите FFmpeg и добавьте его в системный PATH.\n\nСкачать: https://ffmpeg.org/download.html\n\nПриложение требует ffmpeg и ffprobe для корректной работы."},
}

# Load saved language (persisted from previous session)
_current_lang = get_saved_language()


def set_language(lang: str):
    global _current_lang
    _current_lang = lang
    save_language(lang)


def get_language() -> str:
    return _current_lang


def tr(key: str, **kwargs) -> str:
    entry = _TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(_current_lang, entry.get("en", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass
    return text