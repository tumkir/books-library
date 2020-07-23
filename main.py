import json
import os
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def get_books_urls_from_category(category_url, page_count):
    books_urls = []

    for i in range(1, page_count + 1):
        url = f'{category_url}{i}'
        response = requests.get(url, allow_redirects=False)
        response.raise_for_status()
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            books_table_container = soup.find_all('table', class_='d_book')
            for book in books_table_container:
                book_postfix_url = book.find('div', class_='bookimage').find('a')['href']
                books_urls.append(urljoin(url, book_postfix_url))

    return books_urls


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    if response.status_code == 200:
        Path(folder).mkdir(parents=True, exist_ok=True)
        filepath = os.path.join(folder, sanitize_filename(filename))
        with open(filepath, "w") as book:
            book.write(response.text)
        return filepath


def download_image(url, filename, folder='images/'):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    Path(folder).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(folder, sanitize_filename(filename))
    with open(filepath, "wb") as image:
        image.write(response.content)
    return filepath


def download_comment(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    comments = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        comments_block = soup.find_all('div', class_='texts')
        for comment in comments_block:
            comments.append(comment.find("span", class_='black').text)
    return comments


def receive_book_data(url):
    book_id = url.split('/')[-2][1:]
    book = {}
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')

        book['title'] = soup.find('h1').text.split("::")[0].strip()
        book['author'] = soup.find('h1').text.split("::")[1].strip()

        image_url = urljoin(url, soup.find('div', class_='bookimage').find('img')['src'])
        book['image_src'] = download_image(image_url, image_url.split('/')[-1])

        book['book_path'] = download_txt(f'http://tululu.org/txt.php?id={book_id}', f'{book_id}_{book["title"]}.txt')

        book['comments'] = download_comment(url)

        genres_block = soup.find('span', class_='d_book').find_all('a')
        book['genres'] = []

        for genre in genres_block:
            book['genres'].append(genre.text)

        print(f'Скачана книга: {book["title"]} — {book["author"]}')

        return dict(book)


def main(category_url, page_count):
    books_urls = get_books_urls_from_category(category_url, page_count)
    books = []

    for book_url in books_urls:
        books.append(receive_book_data(book_url))

    with open("books.json", "w", encoding='utf8') as my_file:
        json.dump(books, my_file, ensure_ascii=False)


main('http://tululu.org/l55/', 1)
