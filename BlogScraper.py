from datetime import datetime
from bs4 import BeautifulSoup
import os, requests, time, re

from requests import HTTPError

ASTRAL_CODEX_CONFIG = {
    'blog_title': 'Astral Codex Ten',
    'archive_url': 'https://astralcodexten.substack.com/archive',
    'url_selector': '.post-preview-title.newsletter',
    'article_title_selector': '.post .post-header h1',
    'article_subtitle': True,
    'article_subtitle_selector': '.subtitle',
    'article_body_selector': '.body.markup',
    'publish_date_selector': '#entry .main.use-theme-bg div > script',
    'base_url': 'https://astralcodexten.substack.com'
}

MARK_MANSON_CONFIG = {
    'blog_title': "Mark Manson: Life Advice that Doesn't Suck",
    'archive_url': 'https://markmanson.net/archive',
    'url_selector': '.container table tbody tr td a',
    'article_title_selector': 'title',
    'article_subtitle': False,
    'article_subtitle_selector': '',
    'article_body_selector': '.pf-content p',
    'publish_date_selector': 'script[type="application/ld+json"]',
    'base_url': 'https://markmanson.net'
}

PUT_A_NUM_CONFIG = {
    'blog_title': "Put A Number On It!",
    'archive_url': 'https://putanumonit.com/full-archive/',
    'url_selector': '.entry-content p a',
    'article_title_selector': '.entry-title',
    'article_subtitle': False,
    'article_subtitle_selector': '',
    'article_body_selector': '.hentry-wrapper .entry-content',
    'publish_date_selector': '.entry-footer .posted-on .entry-date.published',
    'base_url': 'https://putanumonit.com/'
}

MONTH_DICTIONARY = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'Sepember',
    10: 'October',
    11: 'November',
    12: 'December'
}

TODAY_ISO = str(datetime.now()).split(' ')[0]
CONFIG_LIST = [
    ASTRAL_CODEX_CONFIG,
    MARK_MANSON_CONFIG,
    PUT_A_NUM_CONFIG,
]


def get_page_soup(url):
    res = requests.get(url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    return soup


def get_url_elements(config):
    archive_url = config['archive_url']
    url_selector = config['url_selector']
    soup = get_page_soup(archive_url)
    url_elements = soup.select(url_selector)
    return url_elements


# todo: include for AC10 when applicable
def filter_paid_articles(url_elements):
    filtered_url_elements = []
    for i, element in enumerate(url_elements):
        if 'subscribe' in str(element):
            target_element = url_elements[i - 1]
            filtered_url_elements.remove(target_element)
        else:
            filtered_url_elements.append(element)
    return filtered_url_elements


def url_from_element(element):
    element = str(element)
    target_index_1 = element.index('href="') + len('href="')
    pre_url = element[target_index_1:]
    target_index_2 = pre_url.index('"')
    url = pre_url[:target_index_2]
    return url


def title_from_element(element):
    str_element = str(element)
    target_index_1 = str_element.index('>') + 1
    pre_title = str_element[target_index_1:]
    target_index_2 = pre_title.index('<')
    penultimate_title = pre_title[:target_index_2]
    title = penultimate_title.replace('/', '|||')
    return title


def convert_date_from_ISO(iso_date):
    year, month, day = iso_date.split('-')
    month_spelled = MONTH_DICTIONARY[int(month)]
    date = f'{month_spelled} {day}, {year}'
    return date


def get_article_title_elements(soup, config):
    title_element = soup.select(config['article_title_selector'])[0]
    subtitle_element = ''
    if config['article_subtitle']:
        subtitle_element = soup.select(config['article_subtitle_selector'])
    return title_element, subtitle_element


def get_article_publish_date(soup, config):
    publish_date_element = str(soup.select(config['publish_date_selector'])[0])
    datetime_regex = re.compile(r"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d")
    match_object = datetime_regex.search(publish_date_element)
    publish_date = str(match_object.group()).split('T')[0]
    return publish_date


def get_article_content(soup, config):
    title_element, subtitle_element = get_article_title_elements(soup, config)
    article_title = title_from_element(title_element)
    article_subtitle = ''
    if subtitle_element:
        article_subtitle = title_from_element(subtitle_element)
    article_body_elements = soup.select(config['article_body_selector'])
    str_article_body_elements = [str(element) for element in article_body_elements]
    publish_date = get_article_publish_date(soup, config)
    return article_title, article_subtitle, publish_date, str_article_body_elements, config


def format_content_html(article_content):
    config = article_content[4]
    article_title = article_content[0]
    article_subtitle = article_content[1]
    publish_date = convert_date_from_ISO(article_content[2])
    blog_title = config['blog_title']
    title_element = [f'<h1>{article_title}</h1>']
    subtitle_element = [f'<h2>{article_subtitle}</h2>']
    meta_data_element = [f'<i>Published {publish_date} on {blog_title}.</i>']
    article_body_elements = article_content[3]
    pre_concatenated_elements = title_element + subtitle_element + meta_data_element + article_body_elements
    concatenated_elements = ''
    for element in pre_concatenated_elements:
        concatenated_elements += element
    soup = BeautifulSoup(concatenated_elements, 'html.parser')
    return soup.prettify() + '\n<meta charset="utf-8">'


def scrape_article(url, config):
    soup = get_page_soup(url)
    article_content = get_article_content(soup, config)
    title = title_from_element(get_article_title_elements(soup, config)[0])
    formatted_article = format_content_html(article_content)
    return title, formatted_article


def update_digest(config):
    url_element_list = get_url_elements(config)
    filtered_url_element_list = filter_paid_articles(url_element_list)
    url_list = []
    for url_element in filtered_url_element_list:
        url = url_from_element(url_element)
        if config['base_url'] not in url:
            url = config['base_url'] + url
        url_list.append(url)
    os.makedirs(config['blog_title'], exist_ok=True)
    os.makedirs(f"{config['blog_title']}/Articles", exist_ok=True)

    try:
        with open(f'{config["blog_title"]}/archived_urls.txt', 'r') as file:
            archived_urls = file.readlines()
    except FileNotFoundError:
        with open(f'{config["blog_title"]}/archived_urls.txt', 'x') as file:
            archived_urls = []
            pass

    new_article_urls = []
    for i, url in enumerate(url_list):
        if (url + '\n') not in archived_urls:
            new_article_urls.append(url)
            with open(f'{config["blog_title"]}/archived_urls.txt', 'a') as file:
                file.write((url + '\n'))

    for i, url in enumerate(new_article_urls):
        print(f'attempting: {url}')
        try:
            article_title, article_html = scrape_article(url, config)
            current_date = convert_date_from_ISO(TODAY_ISO)
            os.makedirs(f'_Digest/{current_date}', exist_ok=True)
            with open(f'_Digest/{current_date}/{article_title}.html', 'x') as file:
                file.write(article_html)
            with open(f'{config["blog_title"]}/Articles/{article_title}.html', 'x') as file:
                file.write(article_html)
            time.sleep(6)
        except HTTPError as exeption:
            print(exeption)
