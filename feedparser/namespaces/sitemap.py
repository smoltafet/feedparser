# Support for XML sitemaps and the Google News sitemap extension
# Copyright 2010-2025 Kurt McKee <contactme@kurtmckee.org>
# Copyright 2002-2008 Mark Pilgrim
# All rights reserved.
#
# This file is a part of feedparser.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer in the LICENSE file.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 'AS IS'
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from ..datetimes import _parse_date
from ..util import FeedParserDict


class Namespace:
    """Parse XML sitemaps as feeds.

    A sitemap's ``<urlset>`` maps to the feed, and each ``<url>`` maps to an
    entry: ``<loc>`` becomes the entry link, ``<lastmod>`` its updated date,
    and ``<changefreq>``/``<priority>`` are stored verbatim on the entry.
    A sitemap index (``<sitemapindex>``) is handled the same way, with each
    ``<sitemap>`` child becoming an entry.

    The Google News extension
    (``http://www.google.com/schemas/sitemap-news/0.9``) is exposed as a
    nested ``news`` dictionary on each entry, and its title, publication
    date, and keywords are additionally mapped onto the standard entry
    ``title``, ``published``/``published_parsed``, and ``tags`` keys so
    that news sitemaps work with feed-oriented consumers.
    """

    supported_namespaces = {
        "http://www.sitemaps.org/schemas/sitemap/0.9": "sitemap",
        "http://www.google.com/schemas/sitemap-news/0.9": "news",
    }

    def __init__(self):
        self.insitemap = 0
        self.innews = 0
        self.inpublication = 0
        super().__init__()

    # -- sitemap document structure -------------------------------------

    def _start_urlset(self, attrs_d):
        self.insitemap = 1
        self.infeed = 1
        self.version = "sitemap"
        self.push("urlset", 0)

    def _end_urlset(self):
        self.pop("urlset")
        self.insitemap = 0
        self.infeed = 0

    _start_sitemap_urlset = _start_urlset
    _end_sitemap_urlset = _end_urlset

    def _start_sitemapindex(self, attrs_d):
        self.insitemap = 1
        self.infeed = 1
        self.version = "sitemap"
        self.push("sitemapindex", 0)

    def _end_sitemapindex(self):
        self.pop("sitemapindex")
        self.insitemap = 0
        self.infeed = 0

    _start_sitemap_sitemapindex = _start_sitemapindex
    _end_sitemap_sitemapindex = _end_sitemapindex

    def _start_sitemap_entry(self, attrs_d):
        # Called for <url> (via the branch in _base's _start_url, because
        # plain <url> already means something else in RSS) and directly
        # for <sitemap> children of a sitemap index.
        self.entries.append(FeedParserDict())
        self.push("url", 0)
        self.inentry = 1
        self.guidislink = 0
        self.title_depth = -1

    def _end_sitemap_entry(self):
        self.pop("url")
        self.inentry = 0
        self.hasContent = 0

    _start_sitemap = _start_sitemap_entry
    _end_sitemap = _end_sitemap_entry
    _start_sitemap_url = _start_sitemap_entry
    _end_sitemap_url = _end_sitemap_entry
    _start_sitemap_sitemap = _start_sitemap_entry
    _end_sitemap_sitemap = _end_sitemap_entry

    # -- per-URL elements ------------------------------------------------

    def _start_loc(self, attrs_d):
        context = self._get_context()
        context.setdefault("links", []).append(FeedParserDict())
        self.push("link", 1)

    def _end_loc(self):
        self.pop("link")

    _start_sitemap_loc = _start_loc
    _end_sitemap_loc = _end_loc

    def _start_lastmod(self, attrs_d):
        self.push("updated", 1)

    def _end_lastmod(self):
        value = self.pop("updated")
        self._save("updated_parsed", _parse_date(value), overwrite=True)

    _start_sitemap_lastmod = _start_lastmod
    _end_sitemap_lastmod = _end_lastmod

    def _start_changefreq(self, attrs_d):
        self.push("changefreq", 1)

    def _end_changefreq(self):
        self.pop("changefreq")

    _start_sitemap_changefreq = _start_changefreq
    _end_sitemap_changefreq = _end_changefreq

    def _start_priority(self, attrs_d):
        self.push("priority", 1)

    def _end_priority(self):
        self.pop("priority")

    _start_sitemap_priority = _start_priority
    _end_sitemap_priority = _end_priority

    # -- Google News extension -------------------------------------------

    def _news_context(self):
        context = self._get_context()
        return context.setdefault("news", FeedParserDict())

    def _start_news_news(self, attrs_d):
        self.innews = 1
        self._news_context()
        self.push("news_news", 0)

    def _end_news_news(self):
        self.pop("news_news")
        self.innews = 0

    def _start_news_publication(self, attrs_d):
        self.inpublication = 1
        self._news_context()["publication"] = FeedParserDict()
        self.push("news_publication", 0)

    def _end_news_publication(self):
        self.pop("news_publication")
        self.inpublication = 0

    def _start_news_name(self, attrs_d):
        self.push("news_name", 0)

    def _end_news_name(self):
        value = self.pop("news_name")
        if self.inpublication:
            publication = self._news_context().setdefault(
                "publication", FeedParserDict()
            )
            publication["name"] = value

    def _start_news_language(self, attrs_d):
        self.push("news_language", 0)

    def _end_news_language(self):
        value = self.pop("news_language")
        if self.inpublication:
            publication = self._news_context().setdefault(
                "publication", FeedParserDict()
            )
            publication["language"] = value

    def _start_news_publication_date(self, attrs_d):
        self.push("news_publication_date", 0)

    def _end_news_publication_date(self):
        value = self.pop("news_publication_date")
        news = self._news_context()
        news["publication_date"] = value
        news["publication_date_parsed"] = _parse_date(value)
        if self.inentry:
            context = self._get_context()
            if "published" not in context:
                context["published"] = value
                context["published_parsed"] = news["publication_date_parsed"]

    def _start_news_title(self, attrs_d):
        self.push("news_title", 0)

    def _end_news_title(self):
        value = self.pop("news_title")
        self._news_context()["title"] = value
        if self.inentry:
            context = self._get_context()
            if "title" not in context:
                context["title"] = value

    def _start_news_keywords(self, attrs_d):
        self.push("news_keywords", 0)

    def _end_news_keywords(self):
        value = self.pop("news_keywords")
        self._news_context()["keywords"] = value
        if self.inentry and value:
            for term in value.split(","):
                term = term.strip()
                if term:
                    self._add_tag(term, None, None)

    def _start_news_genres(self, attrs_d):
        self.push("news_genres", 0)

    def _end_news_genres(self):
        self._news_context()["genres"] = self.pop("news_genres")

    def _start_news_stock_tickers(self, attrs_d):
        self.push("news_stock_tickers", 0)

    def _end_news_stock_tickers(self):
        self._news_context()["stock_tickers"] = self.pop("news_stock_tickers")
