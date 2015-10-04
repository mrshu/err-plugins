from readability.readability import Document
import requests
from metadata_parser import MetadataParser
import re

from errbot import re_botcmd, BotPlugin
from itertools import chain

# the [^\s\x0f] at the end fixes IRC coloring issue,
# see https://github.com/mrshu/brutal-plugins/issues/38
URL_REGEX = '((:?https?|ftp)://[^\s/$.?#].[^\s\x0f]*)'
TAG_RE = re.compile(r'<[^>]+>')
WHITESPACE_RE = re.compile(r'\s+')

CONFIG_TEMPLATE = {
    'DOC_MAX_LEN': 75,
    'DOC_MAX_SIZE': 5e6
}


class UrlMatcher(BotPlugin):
    def configure(self, configuration):
        if configuration is not None and configuration != {}:
            config = dict(chain(CONFIG_TEMPLATE.items(),
                                configuration.items()))
        else:
            config = CONFIG_TEMPLATE

        super(UrlMatcher, self).configure(config)

    def get_configuration_template(self):
        return CONFIG_TEMPLATE

    def text_cleanup(self, text):
        text = TAG_RE.sub('', text)
        text = WHITESPACE_RE.sub(' ', text)
        text = text.replace('&#13;', '')
        return text

    @re_botcmd(pattern=URL_REGEX, prefixed=False)
    def url_matcher(self, msg, match):
        url = match.group(0)
        r = requests.head(url)
        max_size = self.config['DOC_MAX_SIZE']
        max_len = self.config['DOC_MAX_LEN']

        # files that are too big cause trouble. Let's just ignore them.
        if 'content-length' in r.headers and \
           int(r.headers['content-length']) > max_size:
            return

        html = requests.get(url).text
        readable_article = Document(html).summary()
        readable_article = self.text_cleanup(readable_article)

        if len(readable_article) > max_len:
            readable_article = readable_article[:max_len] + '...'

        readable_title = Document(html).short_title()

        page = MetadataParser(html=html)
        readable_description = page.get_metadata('description')

        if readable_description is None:
            readable_description = ''

        readable_description = self.text_cleanup(readable_description)

        description = ''
        if len(readable_description) > len(readable_article):
            description = readable_description
        else:
            description = readable_article

        return "~> {}\n~> {}\n~> {}".format(url,
                                            readable_title,
                                            description)
