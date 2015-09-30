from readability.readability import Document
import requests
import re

from errbot import re_botcmd, BotPlugin
from itertools import chain

# the [^\s\x0f] at the end fixes IRC coloring issue,
# see https://github.com/mrshu/brutal-plugins/issues/38
URL_REGEX = '((:?https?|ftp)://[^\s/$.?#].[^\s\x0f]*)'
TAG_RE = re.compile(r'<[^>]+>')
WHITESPACE_RE = re.compile(r'\s\s+')

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
        readable_article = TAG_RE.sub('', readable_article)
        readable_article = WHITESPACE_RE.sub(' ', readable_article)
        readable_article = readable_article.replace('\n', ' ')
        readable_article = readable_article.replace('&#13;', '')

        if len(readable_article) > max_len:
            readable_article = readable_article[:max_len] + '...'

        readable_title = Document(html).short_title()

        return "> " + url + " > " + readable_title + " > " + readable_article
