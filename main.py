import BlogScraper as bs
import os, pdfkit

for blog_config in bs.CONFIG_LIST:
    bs.update_digest(blog_config)

DIGEST_DIR = '/Users/rossvaughn/PycharmProjects/theDigest2/_Digest'

current_date = bs.convert_date_from_ISO(bs.TODAY_ISO)
digest_list = [f'{DIGEST_DIR}/{current_date}/{file_name}' for file_name in os.listdir(f'{DIGEST_DIR}/{current_date}')]

options = {
    'page-size': 'A5',
    'minimum-font-size': 30,
    'margin-top': '0.35in',
    'margin-right': '0.35in',
    'margin-bottom': '0.35in',
    'margin-left': '0.35in',
    'encoding': "UTF-8",
    'custom-header' : [
        ('Accept-Encoding', 'gzip')
    ],
    'cookie': [
        ('cookie-name1', 'cookie-value1'),
        ('cookie-name2', 'cookie-value2'),
    ],
    'no-outline': None
}

pdfkit.from_file(digest_list, f'{current_date}.pdf', options=options)
