"""Tests for Bing search result parsing and research source handling."""

import pytest

from scripts import research_web


def test_bing_parser_reads_titles_urls_and_snippets():
    parser = research_web._BingResultsParser()
    parser.feed(
        '<ol><li class="b_algo"><h2><a href="https://example.org/study">'
        "Estudo científico</a></h2><p>Resumo com evidências.</p></li></ol>"
    )

    assert parser.results == [
        {
            "title": "Estudo científico",
            "url": "https://example.org/study",
            "snippet": "Resumo com evidências.",
        }
    ]


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "https://localhost/private",
        "https://wikipedia.org/science",
        "https://bing.com/redirect",
        "https://user:password@example.org/private",
    ],
)
def test_canonical_url_rejects_unsafe_or_excluded_urls(url):
    assert research_web._canonical_url(url) is None


def test_canonical_url_removes_fragment():
    assert research_web._canonical_url("https://example.org/article#section") == (
        "https://example.org/article"
    )


def test_format_research_context_marks_results_untrusted_and_requires_citations():
    context = research_web.format_research_context(
        {
            "sources": [
                {
                    "id": "S1",
                    "title": "Study",
                    "url": "https://example.org/study",
                    "publisher": "example.org",
                    "snippet": "Evidence",
                }
            ]
        }
    )

    assert "conteúdo externo não confiável" in context
    assert "source_ids" in context
    assert '"id": "S1"' in context


def test_format_research_context_rejects_empty_sources():
    with pytest.raises(ValueError, match="ao menos uma fonte"):
        research_web.format_research_context({"sources": []})


def test_search_sources_filters_results_without_topic_relevance(monkeypatch):
    request_params = []

    class Response:
        text = """
        <li class="b_algo"><h2><a href="https://suno.com/">Suno AI music</a></h2>
        <p>Create songs instantly.</p></li>
        <li class="b_algo"><h2><a href="https://example.org/sleep">
        Sono e memória</a></h2><p>O sono fortalece a memória e o aprendizado.</p></li>
        """

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        research_web.requests,
        "get",
        lambda *args, **kwargs: request_params.append(kwargs["params"]) or Response(),
    )

    result = research_web.search_sources("sono e memória afetam aprendizado")

    assert [source["url"] for source in result["sources"]] == [
        "https://example.org/sleep"
    ]
    assert result["status"] == "completed"
    assert request_params[0]["q"] == "sono memória afetam aprendizado"
