import argparse
import json
import os
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from tqdm import tqdm, trange


def get_books_urls_from_category(category_url, start_page, end_page):
    books_urls = []

    for page in trange(start_page, end_page + 1, desc='Получаем ссылки на книги со страниц жанра'):
        url = f'{category_url}{page}'
        response = requests.get(url, allow_redirects=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        books_table_container = soup.select('table.d_book')
        for book in books_table_container:
            book_postfix_url = book.select_one('div.bookimage a')['href']
            books_urls.append(urljoin(url, book_postfix_url))

    return books_urls


def download_txt(url, filename, dest_folder='.'):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    if response.status_code == 200:
        Path(f'{dest_folder}/books').mkdir(parents=True, exist_ok=True)
        filepath = os.path.join(dest_folder, 'books/', sanitize_filename(filename))
        with open(filepath, 'w') as book:
            book.write(response.text)
        return filepath
    else:
        return ('.txt файла книги нет')


def download_image(url, filename, dest_folder='.'):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    Path(f'{dest_folder}/images').mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(dest_folder, 'images/', sanitize_filename(filename))
    with open(filepath, 'wb') as image:
        image.write(response.content)
    return filepath


def download_comment(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    comments = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        comments_block = soup.select('div.texts span.black')
        for comment in comments_block:
            comments.append(comment.text)
    return comments


def receive_book_data(url, skip_imgs=False, skip_txt=False, dest_folder='.'):
    book_id = url.split('/')[-2][1:]
    book = {}
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')

    book['title'] = soup.select_one('h1').text.split('::')[0].strip()
    book['author'] = soup.select_one('h1').text.split('::')[1].strip()

    if not skip_imgs:
        image_url = urljoin(url, soup.select_one('div.bookimage img')['src'])
        book['image_src'] = download_image(image_url, image_url.split('/')[-1], dest_folder)

    if not skip_txt:
        book['book_path'] = download_txt(f'http://tululu.org/txt.php?id={book_id}', f'{book_id}_{book["title"]}.txt', dest_folder)

    book['comments'] = download_comment(url)

    genres_block = soup.select('span.d_book a')
    book['genres'] = []
    for genre in genres_block:
        book['genres'].append(genre.text)

    return dict(book)


def create_json_file(books_data, json_path='.'):
    Path(json_path).mkdir(parents=True, exist_ok=True)

    with open(os.path.join(json_path, 'books_data.json'), 'w', encoding='utf8') as file:
        json.dump(books_data, file, ensure_ascii=False)


def parse_args():
    parser = argparse.ArgumentParser(description='Программа позволяет скачать книги с сайта http://tululu.org/')
    parser.add_argument('--start_page', default=1, type=int, help='С какой страницы категории начинать скачивание книг')
    parser.add_argument('--end_page', type=int, help='До какой странице категории скачивать книги')
    parser.add_argument('--category_id', default=55, type=int, help='ID категории (жанра)')
    parser.add_argument('--dest_folder', default='.', type=str, help='Путь к каталогу с результатами парсинга: картинкам, книгам, JSON')
    parser.add_argument('--skip_imgs', action='store_true', help='Не скачивать картинки')
    parser.add_argument('--skip_txt', action='store_true', help='Не скачивать книги')
    parser.add_argument('--json_path', type=str, help='Cвой путь к *.json файлу с результатами')

    args = parser.parse_args()

    if args.end_page and args.end_page < args.start_page:
        parser.error('Значение аргумента --end_page не может быть меньше значения --start_page')

    return args


if __name__ == '__main__':
    args = parse_args()

    start_page, end_page, category_id = args.start_page, args.end_page, args.category_id
    dest_folder, json_path = args.dest_folder, args.json_path
    skip_imgs, skip_txt = args.skip_imgs, args.skip_txt

    category_url = f'http://tululu.org/l{category_id}/'

    if not end_page:
        response = requests.get(f'{category_url}{start_page}', allow_redirects=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        end_page = int(soup.select('a.npage')[-1].text)
        if end_page < start_page:
            end_page = start_page

    books_urls = get_books_urls_from_category(category_url, start_page, end_page)
    books_data = []

    for book_url in tqdm(books_urls, desc='Скачиваем книги и данные о них'):
        books_data.append(receive_book_data(book_url, skip_imgs, skip_txt, dest_folder))

    if json_path:
        create_json_file(books_data, json_path)
    else:
        create_json_file(books_data, dest_folder)
