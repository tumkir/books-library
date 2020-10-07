# Парсер книг с сайта tululu.org

Парсер скачивает книги (**.txt** файлы) выбранного жанра с сайта [tululu.org](https://tululu.org/). Дополнительно скачиваются комментарии к книге и обложка. В финале генерируется **.json** файл, где собрана вся информация о скаченных книгах.

### Как установить

Python3 должен быть уже установлен.
Затем используйте `pip` (или `pip3`, если есть конфликт с Python2) для установки зависимостей:

```bash
pip install -r requirements.txt
```

### Аргументы

При запуске скрипта можно указать опциональные аргументы, которые позволяют настроить различные параметры скачивания.

* `--start_page` — страница категории с которой начинать скачивание книг. По умолчанию `1`
* `--end_page` — страница категории (включительно) до которой скачивать книги. Если аргумент не указан, то скачаются все книги до конца категории
* `--category_id` — id категории (жанра). Укажите цифры из URL-адреса (например, (https://tululu.org/l55/)). По умолчанию `55` (Научная фантастика)
* `--dest_folder` — путь к папке с результатами парсинга: обложкам, текстам книг, JSON. По умолчанию `.` (текущая папка), т.е. папка с **.txt** текстами книг, папка с обложками и **.json** файл появится в папке со скриптом
* `--skip_imgs` — не скачивать обложки книг
* `--skip_txt` — не скачивать тексты книг
* `--json_path` — путь до папки, в которой создастся **.json** файл с результатами

### Примеры запуска

Скачиваем книги только с первой страницы жанра *Морские приключения* (https://tululu.org/l54/), **.txt** тексты книг, обложки и **.json** файл складываем в папку `media`:
```bash
python3 parser_tululu.py --end_page 1 --dest_folder ./media/ --category_id 54
```
Скачиваем книги со страницы 10, 11, 12 жанра *Научная фантастика* (https://tululu.org/l55/), **.txt** тексты книг положить в папку `book_data`, обложки не скачивать, а **.json** файл сохранить в папку `json`:
```bash
python3 parser_tululu.py --start_page 10 --end_page 12 --dest_folder ./book_data/ --skip_imgs --json_path ./json
```

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).