# Scrapy settings for homepass_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "homepass_scraper"

SPIDER_MODULES = ["homepass_scraper.spiders"]
NEWSPIDER_MODULE = "homepass_scraper.spiders"

ADDONS = {}



# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "homepass_scraper (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Concurrency and throttling settings
# 동시성/지연 설정 (속도 개선)
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 0.25

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "homepass_scraper.middlewares.HomepassScraperSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "homepass_scraper.middlewares.HomepassScraperDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "homepass_scraper.pipelines.HomepassScraperPipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = False
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

# 1. 파일 파이프라인 활성화
# ITEM_PIPELINES = {
#    'scrapy.pipelines.files.FilesPipeline': 1,
# }

# 2. 파일 다운로드 폴더 지정 (예: 'downloads')
FILES_STORE = 'downloads'



# (중요) Scrapy가 본인을 봇(bot)으로 밝히면 차단하는 사이트가 많습니다.
# 일반 브라우저처럼 보이도록 User-Agent를 설정하는 것이 좋습니다.
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'

# homepass_scraper/homepass_scraper/settings.py

ITEM_PIPELINES = {
   # 'scrapy.pipelines.files.FilesPipeline': 1, # (주석 처리)
   'homepass_scraper.pipelines.HomepassScraperPipeline': 1, # (새 파이프라인으로 변경)
   'homepass_scraper.pipelines.MySQLAnnouncementsPipeline': 500, # MySQL 적재 파이프라인
}

FEEDS = {
    'results.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'indent': 4,
        'overwrite': False  # (중요) True로 하면 매번 새 파일로 덮어쓰고,
                           # False로 하면 기존 파일에 내용이 추가(append)됩니다.
    }
}