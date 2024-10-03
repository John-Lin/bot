from urllib.parse import urlparse
from urllib.parse import urlunparse

import httpx
from loguru import logger

from .pdf import load_pdf
from .ptt import load_ptt
from .singlefile_html import load_singlefile_html
from .video_transcript import load_video_transcript
from .youtube_transcript import load_youtube_transcript


def is_pdf(url: str) -> bool:
    headers = {
        "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8,en-US;q=0.7,en;q=0.6",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",  # noqa
    }

    resp = httpx.head(url=url, headers=headers, follow_redirects=True)
    resp.raise_for_status()
    return resp.headers.get("content-type") == "application/pdf"


def is_youtube_url(url: str) -> bool:
    return (
        url.startswith("https://www.youtube.com")
        or url.startswith("https://youtu.be")
        or url.startswith("https://m.youtube.com")
    )


def replace_domain(url: str) -> str:
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


def load_url(url: str) -> str:
    # https://python.langchain.com/docs/integrations/document_loaders/

    # replace domain
    url = replace_domain(url)

    if is_youtube_url(url):
        transcript = load_youtube_transcript(url)
        if transcript:
            return transcript
        logger.info("No transcript found for YouTube video: {}", url)

        # if the video has no transcripts
        # download the video and transcribe it by whisper
        transcript = load_video_transcript(url)
        if transcript:
            return transcript
        logger.info("Unable to load video transcript for YouTube video: {}", url)

    # check and load PDF
    if is_pdf(url):
        return load_pdf(url)

    # check and load PTT
    if url.startswith("https://www.ptt.cc/bbs"):
        return load_ptt(url)

    # download the page by singlefile and convert it to text
    return load_singlefile_html(url)
