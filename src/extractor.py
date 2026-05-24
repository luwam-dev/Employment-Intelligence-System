import re

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}

TIMEOUT = 20

REMOVE_TAGS = {"script", "style", "noscript", "svg", "iframe"}

REMOVE_SELECTORS = (
    "[role='navigation']",
    "[role='banner']",
    "[role='contentinfo']",
    ".navbar",
    ".nav",
    ".menu",
    ".footer",
    ".header",
    ".sidebar",
    ".cookie",
    ".cookies",
    ".consent",
    ".popup",
    ".modal",
)

BAD_URL_PARTS = (
    "/login",
    "return_to=",
    "accounts.google.com",
    "servicelogin",
    "signin/identifier",
)

BAD_TEXT_PARTS = (
    "sign in",
    "log in",
    "login",
    "page not found",
    "access denied",
    "enable javascript",
)


def normalise_spaces(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def is_bad_url(url):
    url = str(url or "").lower()
    return any(part in url for part in BAD_URL_PARTS)


def has_blocked_text(text):
    text = str(text or "").lower()
    return any(part in text for part in BAD_TEXT_PARTS)


def remove_unwanted_html(soup):
    for tag in soup(REMOVE_TAGS):
        tag.decompose()

    for selector in REMOVE_SELECTORS:
        for node in soup.select(selector):
            node.decompose()


def get_main_text_node(soup):
    candidates = [
        soup.find("main"),
        soup.find("article"),
        soup.find(attrs={"role": "main"}),
        soup.find(id="content"),
        soup.find(id="main"),
    ]

    for node in candidates:
        if node is not None:
            return node

    return soup.body or soup


def remove_boilerplate(text):
    boilerplate = {
        "google sites",
        "report abuse",
        "page details",
        "terms of service",
        "privacy policy",
        "skip to main content",
    }

    chunks = re.split(r"(?<=[.!?])\s+", text)
    useful_chunks = []

    for chunk in chunks:
        if not any(item in chunk.lower() for item in boilerplate):
            useful_chunks.append(chunk)

    return normalise_spaces(" ".join(useful_chunks))


def clean_html_text(raw_html, min_length=80):
    if not raw_html or not raw_html.strip():
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title:
        print(f"   Page title: {title}")

    remove_unwanted_html(soup)

    main_node = get_main_text_node(soup)
    text = normalise_spaces(main_node.get_text(separator=" ", strip=True))

    if not text:
        return ""

    if has_blocked_text(text):
        return ""

    text = remove_boilerplate(text)

    if len(text) < min_length:
        return ""

    return text


def extract_with_requests(url, min_length=80):
    try:
        with requests.Session() as session:
            session.headers.update(HEADERS)
            response = session.get(
                url,
                timeout=TIMEOUT,
                allow_redirects=True,
            )
            response.raise_for_status()

    except requests.RequestException as error:
        print(f"   Request failed: {error}")
        return ""

    final_url = response.url
    content_type = response.headers.get("Content-Type", "").lower()

    print(f"   Final URL: {final_url}")
    print(f"   Status code: {response.status_code}")
    print(f"   Content type: {content_type}")

    if is_bad_url(final_url):
        print("   Blocked by redirect or login page")
        return ""

    if "text/html" not in content_type:
        return ""

    return clean_html_text(response.text, min_length=min_length)


def extract_with_playwright(url, min_length=80):
    browser = None

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(2000)

            final_url = page.url
            print(f"   Final URL: {final_url}")

            if is_bad_url(final_url):
                print("   Blocked by redirect or login page")
                return ""

            html = page.content()

    except Exception as error:
        print(f"   Playwright failed: {error}")
        return ""

    finally:
        if browser:
            browser.close()

    return clean_html_text(html, min_length=min_length)


def extract_text_from_url(url, min_length=80):
    url = str(url or "").strip()

    if not url:
        return ""

    if "sites.google.com" in url.lower():
        return extract_with_playwright(url, min_length=min_length)

    return extract_with_requests(url, min_length=min_length)