import contextlib
import re
import tempfile
from urllib.parse import urlparse
from urllib.parse import urlunparse

import httpx
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.html_bs import BSHTMLLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.messages import AIMessage

DEFAULT_HEADERS = {
    "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8,en-US;q=0.7,en;q=0.6",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",  # noqa
    "Cookie": "over18=1",  # ptt
}


def download(url: str) -> str:
    resp = httpx.get(url=url, headers=DEFAULT_HEADERS, follow_redirects=True)
    resp.raise_for_status()

    suffix = ".pdf" if resp.headers.get("content-type") == "application/pdf" else None
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as fp:
        fp.write(resp.content)
        return fp.name


def parse_url(s: str) -> str:
    url_pattern = r"https?://[^\s]+"

    match = re.search(url_pattern, s)
    if match:
        return match.group(0)

    return ""


def docs_to_str(docs: list[Document]) -> str:
    return "\n".join([doc.page_content.strip() for doc in docs])


def load_document(url: str) -> str:
    # https://python.langchain.com/docs/integrations/document_loaders/

    with contextlib.suppress(ValueError):
        return docs_to_str(
            YoutubeLoader.from_youtube_url(
                url, add_video_info=True, language=["zh-TW", "zh-Hant", "zh-Hans", "ja", "en"]
            ).load()
        )

    # fix twitter url
    url = fix_twitter(url)

    f = download(url)

    if f.endswith(".pdf"):
        return docs_to_str(PyPDFLoader(f).load())

    return docs_to_str(BSHTMLLoader(f).load())


def ai_message_repr(ai_message: AIMessage) -> str:
    content: str | list[str | dict] = ai_message.content
    if isinstance(content, str):
        return content

    contents = []
    for item in content:
        if isinstance(item, str):
            contents.append(f"• {item}")

        if isinstance(item, dict):
            for k, v in item.items():
                contents.append(f"• {k}: {v}")

    return "\n".join(contents)


def fix_twitter(url: str) -> str:
    replacements = {
        # "twitter.com": "vxtwitter.com",
        # "x.com": "fixvx.com",
        # "twitter.com": "twittpr.com",
        # "x.com": "fixupx.com",
        "twitter.com": "api.fxtwitter.com",
        "x.com": "api.fxtwitter.com",
    }

    parsed_url = urlparse(url)
    if parsed_url.netloc in replacements:
        new_netloc = replacements[parsed_url.netloc]
        fixed_url = parsed_url._replace(netloc=new_netloc)
        return urlunparse(fixed_url)

    return url
