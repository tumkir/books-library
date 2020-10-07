import argparse
import json
import os
import sys
from pathlib import Path
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from tqdm import tqdm, trange


def request_without_redirect(url):
    response = requests.get(url, allow_redirects=False)
    if response.status_code != 200:
        raise requests.HTTPError(f'Код ответа HTTP {response.status_code}. Требуется 200.')
    return response


def get_books_urls_from_category(category_url, start_page, end_page):
    books_urls = []

    for page in trange(start_page, end_page + 1, desc='Получаем ссылки на книги со страниц жанра'):
        url = f'{category_url}{page}'
        response = request_without_redirect(url)
        soup = BeautifulSoup(response.text, 'lxml')
        books_table_container = soup.select('table.d_book')
        book_postfix_urls = [book.select_one('div.bookimage a')['href'] for book in books_table_container]
        books_urls = [urljoin(url, book_postfix_url) for book_postfix_url in book_postfix_urls]

    return books_urls


def download_txt(url, filename, dest_folder='.'):
    response = requests.get(url, allow_redirects=False)
    try:
        response = request_without_redirect(url)
    except requests.HTTPError:
        return

    Path(f'{dest_folder}/books').mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(dest_folder, 'books/', sanitize_filename(filename))
    with open(filepath, 'w') as book:
        book.write(response.text)
    return filepath


def download_image(url, filename, dest_folder='.'):
    response = request_without_redirect(url)
    Path(f'{dest_folder}/images').mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(dest_folder, 'images/', sanitize_filename(filename))
    with open(filepath, 'wb') as image:
        image.write(response.content)
    return filepath


def download_comment(url):
    response = request_without_redirect(url)
    soup = BeautifulSoup(response.text, 'lxml')
    comments_block = soup.select('div.texts span.black')
    comments = [comment.text for comment in comments_block]
    return comments


def receive_book_data(url, skip_imgs=False, skip_txt=False, dest_folder='.'):
    book_id = url.split('/')[-2][1:]
    book = {}
    response = request_without_redirect(url)
    soup = BeautifulSoup(response.text, 'lxml')

    book['title'], book['author'] = soup.select_one('h1').text.split(' \xa0 :: \xa0 ')

    if not skip_imgs:
        image_url = urljoin(url, soup.select_one('div.bookimage img')['src'])
        book['image_src'] = download_image(image_url, image_url.split('/')[-1], dest_folder)

    if not skip_txt:
        book['book_path'] = download_txt(f'https://tululu.org/txt.php?id={book_id}', f'{book_id}_{book["title"]}.txt', dest_folder)

    book['comments'] = download_comment(url)

    genres_block = soup.select('span.d_book a')
    book['genres'] = [genre.text for genre in genres_block]

    return book


def create_json_file(books_data, json_path='.'):
    Path(json_path).mkdir(parents=True, exist_ok=True)

    with open(os.path.join(json_path, 'books_data.json'), 'w', encoding='utf8') as file:
        json.dump(books_data, file, ensure_ascii=False)


def parse_args():
    parser = argparse.ArgumentParser(description='Программа позволяет скачать книги с сайта https://tululu.org/')
    parser.add_argument('--start_page', default=1, type=int, help='С какой страницы категории начинать скачивание книг')
    parser.add_argument('--end_page', type=int, help='До какой странице категории скачивать книги')
    parser.add_argument('--category_id', default=55, type=int, help='ID категории (жанра)')
    parser.add_argument('--dest_folder', default='.', type=str, help='Путь к папке с результатами парсинга: обложкам, текстам книг, JSON')
    parser.add_argument('--skip_imgs', action='store_true', help='Не скачивать обложки книг')
    parser.add_argument('--skip_txt', action='store_true', help='Не скачивать тексты книг')
    parser.add_argument('--json_path', type=str, help='Путь до папки, в которой создастся .json файл с результатами')

    args = parser.parse_args()

    if args.end_page and args.end_page < args.start_page:
        parser.error('Значение аргумента --end_page не может быть меньше значения --start_page')

    return args


if __name__ == '__main__':
    args = parse_args()

    start_page, end_page, category_id = args.start_page, args.end_page, args.category_id
    dest_folder, json_path = args.dest_folder, args.json_path
    skip_imgs, skip_txt = args.skip_imgs, args.skip_txt

    category_url = f'https://tululu.org/l{category_id}/'

    if not end_page:
        response = request_without_redirect(f'{category_url}{start_page}')
        soup = BeautifulSoup(response.text, 'lxml')
        end_page = int(soup.select('a.npage')[-1].text)
        if end_page < start_page:
            end_page = start_page

    try:
        books_urls = get_books_urls_from_category(category_url, start_page, end_page)
    except requests.exceptions.ConnectionError:
        print('Ошибка сети. Проверьте подключение к интернету и попробуйте скачать книги позже')
        raise SystemExit()
    books_data = []

    for book_url in tqdm(books_urls, desc='Скачиваем книги и данные о них'):
        try:
            books_data.append(receive_book_data(book_url, skip_imgs, skip_txt, dest_folder))
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            tqdm.write(f'Ошибка сети. Книга {book_url} пропущена, пробуем скачать следующую книгу', file=sys.stderr)
            sleep(5)
            continue

    create_json_file(books_data, json_path or dest_folder)
