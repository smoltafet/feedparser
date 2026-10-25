import time

import feedparser

PLAIN_SITEMAP = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>http://www.example.org/</loc>
        <lastmod>2005-01-01</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>http://www.example.org/catalog?item=12&amp;desc=vacation_hawaii</loc>
        <changefreq>weekly</changefreq>
    </url>
</urlset>
"""

NEWS_SITEMAP = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
    <url>
        <loc>http://www.example.org/business/article55.html</loc>
        <lastmod>2008-12-23T18:00:15+00:00</lastmod>
        <news:news>
            <news:publication>
                <news:name>The Example Times</news:name>
                <news:language>en</news:language>
            </news:publication>
            <news:publication_date>2008-12-23T18:00:15+00:00</news:publication_date>
            <news:title>Companies A, B in Merger Talks</news:title>
            <news:keywords>business, merger, acquisition</news:keywords>
        </news:news>
    </url>
    <url>
        <loc>http://www.example.org/business/article66.html</loc>
        <news:news>
            <news:publication>
                <news:name>The Example Times</news:name>
                <news:language>en</news:language>
            </news:publication>
            <news:genres>PressRelease, Blog</news:genres>
            <news:publication_date>2008-12-23</news:publication_date>
            <news:title>Article 66 Title</news:title>
            <news:keywords>stocks</news:keywords>
            <news:stock_tickers>NYSE:IBM, NASDAQ:MSFT</news:stock_tickers>
        </news:news>
    </url>
</urlset>
"""

SITEMAP_INDEX = """\
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <sitemap>
        <loc>http://www.example.org/sitemap1.xml.gz</loc>
        <lastmod>2004-10-01T18:23:17+00:00</lastmod>
    </sitemap>
    <sitemap>
        <loc>http://www.example.org/sitemap2.xml.gz</loc>
        <lastmod>2005-01-01</lastmod>
    </sitemap>
</sitemapindex>
"""


def test_plain_sitemap_is_recognized():
    result = feedparser.parse(PLAIN_SITEMAP)
    assert result.bozo is False
    assert result.version == "sitemap"
    assert len(result.entries) == 2


def test_plain_sitemap_url_fields():
    result = feedparser.parse(PLAIN_SITEMAP)
    first, second = result.entries
    assert first.link == "http://www.example.org/"
    assert first.links[0].href == "http://www.example.org/"
    assert first.updated == "2005-01-01"
    assert first.updated_parsed == time.gmtime(1104537600)
    assert first.changefreq == "monthly"
    assert first.priority == "0.8"
    # Query strings survive parsing.
    assert second.link == (
        "http://www.example.org/catalog?item=12&desc=vacation_hawaii"
    )
    assert second.changefreq == "weekly"
    assert "updated" not in second


def test_news_sitemap_publication():
    result = feedparser.parse(NEWS_SITEMAP)
    assert result.bozo is False
    assert result.version == "sitemap"
    entry = result.entries[0]
    assert entry.news.publication.name == "The Example Times"
    assert entry.news.publication.language == "en"


def test_news_sitemap_maps_onto_entry_fields():
    result = feedparser.parse(NEWS_SITEMAP)
    entry = result.entries[0]
    assert entry.title == "Companies A, B in Merger Talks"
    assert entry.news.title == "Companies A, B in Merger Talks"
    assert entry.published == "2008-12-23T18:00:15+00:00"
    assert entry.published_parsed == entry.news.publication_date_parsed
    assert [tag.term for tag in entry.tags] == [
        "business",
        "merger",
        "acquisition",
    ]
    # <lastmod> still maps to the entry's updated date.
    assert entry.updated == "2008-12-23T18:00:15+00:00"
    assert entry.updated_parsed == entry.published_parsed


def test_news_sitemap_optional_elements():
    result = feedparser.parse(NEWS_SITEMAP)
    entry = result.entries[1]
    assert entry.news.genres == "PressRelease, Blog"
    assert entry.news.stock_tickers == "NYSE:IBM, NASDAQ:MSFT"
    assert entry.news.publication_date == "2008-12-23"
    assert entry.published_parsed.tm_year == 2008
    assert entry.title == "Article 66 Title"


def test_news_sitemap_entries_do_not_leak_into_each_other():
    result = feedparser.parse(NEWS_SITEMAP)
    first, second = result.entries
    assert "genres" not in first.news
    assert "stock_tickers" not in first.news
    assert second.news.publication.name == "The Example Times"


def test_sitemap_index():
    result = feedparser.parse(SITEMAP_INDEX)
    assert result.bozo is False
    assert result.version == "sitemap"
    assert len(result.entries) == 2
    assert result.entries[0].link == "http://www.example.org/sitemap1.xml.gz"
    assert result.entries[0].updated == "2004-10-01T18:23:17+00:00"
    assert result.entries[0].updated_parsed.tm_year == 2004
    assert result.entries[1].link == "http://www.example.org/sitemap2.xml.gz"


def test_rss_url_element_is_not_a_sitemap_entry():
    # The <url> element inside an RSS <image> must keep its existing
    # meaning; the sitemap handling only applies inside a sitemap.
    rss = """\
<rss version="2.0"><channel>
<title>Example</title><link>http://example.org/</link>
<image><url>http://example.org/logo.png</url><title>Logo</title>
<link>http://example.org/</link></image>
<item><title>Item</title><link>http://example.org/1</link></item>
</channel></rss>
"""
    result = feedparser.parse(rss)
    assert result.bozo is False
    assert result.version == "rss20"
    assert len(result.entries) == 1
    assert result.feed.image.href == "http://example.org/logo.png"
