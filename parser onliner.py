import requests
import datetime
import time
from bs4 import BeautifulSoup
import json

URL = "https://people.onliner.by"
KEY_WORD = "коронавирус"
COMMENTS_URL = "https://comments.api.onliner.by/news/people.post/{0}/comments?limit=10"


def get_comments(id):
    request = requests.get(COMMENTS_URL.format(id))
    result_comments = []

    if request.status_code == 200:
        soup = BeautifulSoup(request.text, 'html.parser')
        comments = json.loads(str(soup))['comments']

        for comment in comments:
            temp_comment = {}

            temp_comment['author'] = comment['author']['name']
            temp_comment['created_at'] = comment['created_at']
            temp_comment['text'] = comment['text']

            result_comments.append(temp_comment)

    return result_comments

def get_author(items):
    for item in items:
        if item.attrs.setdefault('name', None) == "author":
            return item.attrs['content']

def parse_post(link):
    request = requests.get(URL + link)
    post = {}

    if request.status_code == 200:
        soup = BeautifulSoup(request.text, 'html.parser')
        items = soup.find_all("div", class_="news-text")[0]

        text = ""
        contents = items.find_all_next("p", style="")
        for content in contents:
            if content.text:
                text += content.text.strip() + "\n"

        post['description'] = text

        news_id = soup.find_all("span", class_="news_view_count")[0].attrs['news_id']
        post['comments'] = get_comments(news_id)
        post['author'] = get_author(soup.find_all("meta"))

    return post

def write_posts(posts):
    with open("posts.txt", "w", encoding="utf8") as file:
        for post in posts:
            file.write(post['title'] + "\n\n")
            file.write(post['description'] + "\n")
            file.write("Ссылка на статью: " + URL + post['link'] + "\n")
            file.write("Автор: " + post['author'] + "\n")
            file.write("Просмотров статьи: " + post['views'] + "\n")
            file.write("Опубликовано: " + post['create_at'] + "\n\n")
            file.write("Количество символов в заголовке: " + str(post['symbol_in_title']) + "\n")
            file.write("Количество слов в заголовке: " + str(post['word_in_title']) + "\n")
            file.write("Количество символов в статье: " + str(post['symbol_in_desc']) + "\n")
            file.write("Количество слов в статье: " + str(post['word_in_desc']) + "\n")
            file.write("Количество вхождений ключевого слова '{0}' в заголовок: ".format(KEY_WORD) + str(post['keyword_in_title']) + "\n")
            file.write("Количество вхождений ключевого слова '{0}' в текст статьи: ".format(KEY_WORD) + str(post['keyword_in_desc']) + "\n")
            file.write("Плотность ключевого слова '{0}' в заголовке: ".format(KEY_WORD) + str(post['density_keyword_in_title']) + "%\n")
            file.write("Плотность ключевого слова '{0}' в статье: ".format(KEY_WORD) + str(post['density_keyword_in_desc']) + "%\n\n")

            file.write("Комментарии:\n")
            for comment in post['comments']:
                created_at = comment['created_at'].split('.')[0].replace("T", " ")
                file.write(comment['author'] + " (" + created_at + "): " + comment['text'] + "\n\n")

            file.write("\n\n\n\n\n")

date = datetime.datetime.now()
current = time.mktime(date.timetuple())
interval = time.mktime(date.timetuple()) - 604800

posts = []

while True:
    request = requests.get(URL, params={'fromDate': int(current)})

    if request.status_code == 200:
        soup = BeautifulSoup(request.text, 'html.parser')
        items = soup.find_all("div", class_="news-tidings__item news-tidings__item_1of3 news-tidings__item_condensed")

        current = int(items[-1].attrs['data-post-date'])

        for item in items:
            title = item.find_next("span", class_="news-helpers_hide_mobile-small").text
            description = item.find_next("div", class_="news-tidings__speech news-helpers_hide_mobile-small").text
            detail = item.find_next("div", class_="news-tidings__control")

            if title.lower().find(KEY_WORD) != -1 or description.lower().find(KEY_WORD) != -1:
                link = item.find_next("a", class_="news-tidings__link").attrs['href']

                post = parse_post(link)

                post['link'] = link
                post['title'] = title
                post['create_at'] = detail.find("div", class_="news-tidings__time").text.strip()
                post['views'] = detail.find("div", class_="news-tidings__group").contents[1].contents[0].strip()

                post['symbol_in_title'] = len(title)
                post['word_in_title'] = len(title.split(" "))
                post['symbol_in_desc'] = len(post['description'])
                post['word_in_desc'] = len(post['description'].split(" "))
                post['keyword_in_title'] = title.lower().count(KEY_WORD)
                post['keyword_in_desc'] = post['description'].lower().count(KEY_WORD)
                post['density_keyword_in_title'] = post['keyword_in_title'] / post['word_in_title'] * 100
                post['density_keyword_in_desc'] = post['keyword_in_desc'] / post['word_in_desc'] * 100

                posts.append(post)

        if current < interval:
            break

write_posts(posts)
