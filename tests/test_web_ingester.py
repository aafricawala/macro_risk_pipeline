"""
Unit Tests for src/data/web_ingester.py.
"""
from unittest.mock import patch, MagicMock
import pytest
from src.data.source_registry import SourceEndpoint, SourceCategory
from src.data.web_ingester import (
    fetch_and_extract_webpage,
    fetch_and_extract_rss,
    ingest_source_endpoint,
)

@patch("requests.get")
@patch("trafilatura.extract")
def test_fetch_and_extract_webpage_mocked_success(mock_extract, mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "<html><body><h1>Headline</h1><p>Federal Reserve minutes summary text.</p></body></html>"
    mock_get.return_value = mock_resp
    mock_extract.return_value = "Headline\nFederal Reserve minutes summary text."
    extracted = fetch_and_extract_webpage("https://example.com/news")
    assert extracted is not None
    assert "Federal Reserve" in extracted

@patch("requests.get")
@patch("feedparser.parse")
def test_fetch_and_extract_rss_mocked_success(mock_feed_parse, mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"<rss><channel></channel></rss>"
    mock_get.return_value = mock_resp

    entry_mock = MagicMock()
    entry_mock.title = "FDIC Closes Bank XYZ"
    entry_mock.link = "https://fdic.gov/news/press/123"
    entry_mock.published = "2026-08-18"
    entry_mock.summary = "<p>FDIC enters receivership for Bank XYZ.</p>"
    feed_obj = MagicMock()
    feed_obj.entries = [entry_mock]
    mock_feed_parse.return_value = feed_obj

    rss_items = fetch_and_extract_rss("https://fdic.gov/rss")
    assert len(rss_items) == 1
    assert rss_items[0]["title"] == "FDIC Closes Bank XYZ"

@patch("src.data.web_ingester.fetch_and_extract_webpage", return_value="Sample clean text content.")
@patch("src.data.web_ingester.fetch_and_extract_rss", return_value=[{"title": "News 1", "summary": "Alert", "link": "", "published": ""}])
def test_ingest_source_endpoint_dispatch(mock_rss, mock_web):
    html_source = SourceEndpoint(name="Test_HTML", url="https://example.com/html", category=SourceCategory.MACRO_CALENDAR, is_rss=False)
    rss_source = SourceEndpoint(name="Test_RSS", url="https://example.com/rss", category=SourceCategory.GEOPOLITICS_AND_NEWS, is_rss=True)

    res_html = ingest_source_endpoint(html_source)
    assert res_html["is_rss"] is False
    assert "Sample clean text" in res_html["text_content"]

    res_rss = ingest_source_endpoint(rss_source)
    assert res_rss["is_rss"] is True
    assert "News 1" in res_rss["text_content"]
