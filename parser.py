import requests
from bs4 import BeautifulSoup
import feedparser

URL = "https://news.tut.by/rss/"
KEY_WORD = "коронавирус"

def get_rss(url):
    rss = feedparser.parse(url)

    return rss

def get_html(url, page=None):
    request = requests.get(url, data={'page': page})

    return request

def get_content(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    items = soup.find_all("div", id="article_body")[0]

    article = ""
    for content in items.contents:
        if content.name == "blockquote":
            break
        if content.name == "p":
            if len(content) > 1:
                for text in content.contents:
                    try:
                        article += text
                    except Exception:
                        article += text.text
                article += "\n"
            else:
                try:
                    if content.text:
                        article += content.text + "\n"
                except Exception:
                    pass

    return article

def get_count_pages(url):
    html = get_html(url)

    if html.status_code == 200:
        soup = BeautifulSoup(html.text, 'html.parser')

        pages = soup.find("span", class_="prev_next")
        if pages:
            pages = int(pages.find_previous().text)
        else:
            pages = 1

    return pages

def get_comments(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    items = soup.find("a", class_="b-add_comments")

    url = items.attrs['href']

    count_pages = get_count_pages(url)

    comments = parse_comments(url, count_pages=count_pages)

    return comments

def parse_comments(url, page=1, count_pages=1):
    comments = []
    while True:
        html = get_html(url, page=page)

        if html.status_code == 200:
            soup = BeautifulSoup(html.text, 'html.parser')
            items = soup.find_all("table", class_="themaCommentTable")[0]
            left = items.find_all_next("td", class_="themaCommentLeft")
            right = items.find_all_next("td", class_="themaCommentRight")

            for i in range(1, len(left)):
                comments.append({
                    'author': left[i].find_next("a", class_="username").text,
                    'text': right[i].find_next("div", class_="row-content-tut").text
                })

            page += 1
            if page > count_pages:
                break
        else:
            return "Не удалось отправить GET запрос"

    return comments

def get_authors(list_authors):
    authors = ""

    for author in list_authors:
        authors += author["name"]
        if author.setdefault("href", None):
            authors += " (" + author["href"] + "), "
        else:
            authors += ", "

    return authors[:-2]

def get_tags(list_tags):
    tags = ""

    for tag in list_tags:
        tags += tag["term"] + ", "

    return tags[:-2]

def _is_substring(title, description):
    is_substring = False
    if title.lower().find(KEY_WORD) != -1:
        is_substring = True
    if description.lower().find(KEY_WORD) != -1:
        is_substring = True

    return is_substring

def parse():
    rss = get_rss(URL)
    posts = []

    for post in rss.entries:
        http = get_html(post.link)

        if http.status_code == 200:
            is_substring = _is_substring(post.title, post.description)

            if is_substring:
                posts.append({
                    'title': post.title,
                    'content': get_content(http),
                    'published': post.published,
                    'link': post.link,
                    'authors': get_authors(post.authors),
                    'tags': get_tags(post.tags),
                    'comments': get_comments(http)
                })
        else:
            print("Не удалось отправить GET запрос")

    return posts

def task(posts):
    for post in posts:
        url = post["link"]
        title = post['title']
        description = post['content']

        post["characters_count_url"] = len(url)
        post["word_count_title"] = len(title.split(" "))
        post["characters_count_title"] = len(title)
        post["word_count_description"] = len(description.split(" "))
        post["characters_count_description"] = len(description)
        post["count_keyword_searches_title"] = title.lower().count(KEY_WORD)
        post["count_keyword_searches_description"] = description.lower().count(KEY_WORD)
        post["density_keyword_title"] = post["count_keyword_searches_title"] / post["word_count_title"] * 100
        post["density_keyword_description"] = post["count_keyword_searches_description"] / post["word_count_description"] * 100

def write_comments(file, comments):
    for comment in comments:
        comment['text'] = comment['text'].strip()
        comment['text'] = comment['text'].replace("\n", "")
        comment['text'] = comment['text'].replace("\r", "")
        comment['author'] = comment['author'].replace("\t", "")
        comment['author'] = comment['author'].replace("\n", "")
        comment['author'] = comment['author'].replace("\r", "")

        text = "     " + comment['author'] + ": " + comment['text'] + "\n\n"
        file.write(text)

def write_posts(posts):
    with open("output.txt", "w") as file:
        for post in posts:
            file.write("Заголовок:\n")
            file.write(post['title'])
            file.write("\n\nТекст статьи:\n")
            file.write(post["content"])
            file.write("\n\nДата публикации: {0}\n".format(post["published"]))
            file.write("\n\nАвтор(ы): {0}\n".format(post["authors"]))
            file.write("\n\nИсточник: {0}\n".format(post["link"]))
            file.write("\n\nТеги: {0}\n".format(post["tags"]))
            file.write("\n\nКолличество символов в url: {0}\n".format(post['characters_count_url']))
            file.write("Колличество символов в title: {0}\n".format(post['characters_count_title']))
            file.write("Колличество слов в title: {0}\n".format(post['word_count_title']))
            file.write("Колличество символов в description: {0}\n".format(post['characters_count_description']))
            file.write("Колличество слов в description: {0}\n".format(post['word_count_description']))
            file.write("Колличество вхождений ключевого слова {0} в title: {1}\n".format(KEY_WORD, post['count_keyword_searches_title']))
            file.write("Колличество вхождений ключевого слова {0} в description: {1}\n".format(KEY_WORD, post['count_keyword_searches_description']))
            file.write("Плотность ключевого слова в title: {0}%\n".format(post['density_keyword_title']))
            file.write("Плотность ключевого слова в description: {0}%\n".format(post['density_keyword_description']))
            file.write("\n\nКомментарии:\n")
            write_comments(file, post['comments'])

            file.write("\n\n\n_________________________________________________________________\n\n\n")

if __name__ == "__main__":
    posts = parse()

    task(posts)

    write_posts(posts)