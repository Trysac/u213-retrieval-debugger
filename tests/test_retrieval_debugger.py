"""Tests for retrieval_debugger."""

from __future__ import annotations

import pytest

from retrieval_debugger import DebugError, explain, render


def test_acceptance_below_cutoff() -> None:
    e = explain(
        "Running shoes",
        "I bought running shoes yesterday.",
        doc_id="d1",
        ranking=[("d0", 3.2), ("d1", 2.5)],
        k=1,
    )
    assert e.rank == 2
    assert e.in_top_k is False
    assert e.gap_to_cutoff == 0.7
    assert len(e.terms) == 2
    assert all(tm.status == "exact" for tm in e.terms)
    assert e.reasons == ("below_cutoff",)


def test_acceptance_stem_mismatch() -> None:
    e = explain("install packages", "How to installing a package", doc_id="d2")
    assert len(e.terms) == 2
    assert {tm.term for tm in e.terms} == {"install", "packages"}
    assert all(tm.status == "stem" for tm in e.terms)
    assert e.reasons == ("stem_mismatch",)
    assert e.rank is None
    assert e.in_top_k is None
    assert e.gap_to_cutoff is None


def test_acceptance_accent_mismatch() -> None:
    e = explain("café", "Cafe menu", doc_id="d3")
    assert len(e.terms) == 1
    tm = e.terms[0]
    assert tm.term == "café"
    assert tm.status == "accent"
    assert e.reasons == ("accent_mismatch",)


def test_acceptance_accent_escape_literal() -> None:
    e = explain("caf\u00e9", "Cafe menu", doc_id="d3")
    assert len(e.terms) == 1
    tm = e.terms[0]
    assert tm.term == "caf\u00e9"
    assert tm.status == "accent"
    assert e.reasons == ("accent_mismatch",)


def test_acceptance_not_in_ranking_and_missing() -> None:
    e = explain(
        "refund policy",
        "Shipping times",
        doc_id="d9",
        ranking=[("d0", 1.0)],
        k=1,
    )
    assert e.rank is None
    assert e.in_top_k is None
    assert e.gap_to_cutoff is None
    assert len(e.terms) == 2
    assert all(tm.status == "missing" for tm in e.terms)
    assert e.reasons == ("not_in_ranking", "missing_terms")


def test_acceptance_beyond_chunk() -> None:
    e = explain(
        "refund",
        "Intro text here and more words. refund policy applies",
        doc_id="d4",
        chunk_chars=20,
    )
    assert len(e.terms) == 1
    tm = e.terms[0]
    assert tm.term == "refund"
    assert tm.status == "exact"
    assert tm.positions == (32,)
    assert tm.beyond_chunk is True
    assert e.reasons == ("term_beyond_chunk",)


def test_acceptance_render() -> None:
    e = explain(
        "Running shoes",
        "I bought running shoes yesterday.",
        doc_id="d1",
        ranking=[("d0", 3.2), ("d1", 2.5)],
        k=1,
    )
    expected = (
        "doc d1: rank 2, cutoff k=1, below cutoff by 0.7\n"
        "running: exact\nshoes: exact\nreasons: below_cutoff"
    )
    assert render(e) == expected


def test_acceptance_limits() -> None:
    # document too large
    with pytest.raises(DebugError) as exc_info:
        explain("query", "x" * 1_000_001, doc_id="d")
    assert exc_info.value.code == "input_too_large"

    # document exactly at limit should not raise here (but query may be empty)
    explain("", "x" * 1_000_000, doc_id="d")

    # query too large
    with pytest.raises(DebugError) as exc_info:
        explain("x" * 1_001, "doc", doc_id="d")
    assert exc_info.value.code == "input_too_large"

    # invalid k
    with pytest.raises(DebugError) as exc_info:
        explain("q", "doc", doc_id="d", k=0)
    assert exc_info.value.code == "invalid_k"
    with pytest.raises(DebugError) as exc_info:
        explain("q", "doc", doc_id="d", k=10_001)
    assert exc_info.value.code == "invalid_k"

    # duplicate id in ranking
    with pytest.raises(DebugError) as exc_info:
        explain("q", "doc", doc_id="d", ranking=[("a", 1.0), ("a", 2.0)])
    assert exc_info.value.code == "invalid_ranking"


def test_rank_exactly_at_cutoff() -> None:
    e = explain(
        "query",
        "document",
        doc_id="d1",
        ranking=[("d0", 3.0), ("d1", 2.0)],
        k=2,
    )
    assert e.rank == 2
    assert e.in_top_k is True
    assert e.gap_to_cutoff is None
    assert "below_cutoff" not in e.reasons


def test_term_exact_wins_over_stem() -> None:
    # 'running' appears exactly and as stem? doc has 'run' which stems to 'run', query 'running' exact? query 'running' exact? Actually doc 'running' matches exact.
    # We need a case where exact and stem both possible for the same term.
    # Use query 'runs', doc 'run runs' -> 'run' stems to 'run' (stem relation), 'runs' exact (term 'runs' exact match 'runs').
    # Accept: query 'runs', doc 'run runs'. Exact should win.
    e = explain("runs", "run runs", doc_id="d")
    assert len(e.terms) == 1
    assert e.terms[0].status == "exact"
    assert "stem_mismatch" not in e.reasons


def test_accent_then_stem_precedence() -> None:
    # 'Cafés' vs 'cafe': accent folding does not make them equal ('cafes' vs
    # 'cafe'), so the stem step applies and reports a stem match.
    e = explain("Cafés", "cafe", doc_id="d")
    assert e.terms[0].status == "stem"
    assert "stem_mismatch" in e.reasons

    # When accent folding alone makes them equal, accent wins over stem.
    e = explain("café", "cafe", doc_id="d")
    assert e.terms[0].status == "accent"
    assert "stem_mismatch" not in e.reasons


def test_empty_query_no_terms_ranking_reasons() -> None:
    # empty query, ranking with doc absent -> reasons only 'not_in_ranking'
    e = explain("", "doc", doc_id="d", ranking=[("other", 1.0)], k=1)
    assert e.terms == ()
    assert e.reasons == ("not_in_ranking",)

    # empty query, ranking with doc present but above cutoff -> reasons empty
    e = explain("", "doc", doc_id="d", ranking=[("d", 1.0)], k=1)
    assert e.terms == ()
    assert e.reasons == ()
    assert e.in_top_k is True


def test_query_term_limit_64() -> None:
    query_terms = [f"t{i}" for i in range(100)]
    query = " ".join(query_terms)
    doc = " "
    e = explain(query, doc, doc_id="d")
    assert len(e.terms) == 64
    # ensure first 64 terms are present
    assert [tm.term for tm in e.terms] == query_terms[:64]


def test_positions_truncated_to_10() -> None:
    doc = " ".join(["word"] * 20)
    e = explain("word", doc, doc_id="d")
    assert len(e.terms) == 1
    assert e.terms[0].status == "exact"
    assert len(e.terms[0].positions) == 10
    # positions should be first 10 occurrences, ascending
    # compute expected: positions of first 10 tokens, all start at multiples of 5 (word len 4 + space)
    expected = tuple(i * 5 for i in range(10))
    assert e.terms[0].positions == expected


def test_chunk_chars_all_positions_ge() -> None:
    doc = "aa bb cc dd"
    e = explain("cc", doc, doc_id="d", chunk_chars=6)
    assert e.terms[0].status == "exact"
    assert e.terms[0].positions == (6,)
    assert e.terms[0].beyond_chunk is True


def test_chunk_chars_some_below() -> None:
    # term appears at positions 0 and 4; chunk_chars=3 -> one below, one above => beyond_chunk False
    doc = "aa aa"
    e = explain("aa", doc, doc_id="d", chunk_chars=3)
    assert e.terms[0].beyond_chunk is False


def test_render_no_ranking() -> None:
    e = explain("query", "document", doc_id="d")
    assert render(e) == "doc d: no ranking\nquery: missing\nreasons: missing_terms"


def test_render_not_in_ranking() -> None:
    e = explain("query", "document", doc_id="d", ranking=[("other", 1.0)], k=3)
    expected = (
        "doc d: not in ranking, cutoff k=3\nquery: missing\nreasons: not_in_ranking, missing_terms"
    )
    assert render(e) == expected


def test_render_empty_reasons() -> None:
    e = explain("query", "document query", doc_id="d")
    assert render(e) == "doc d: no ranking\nquery: exact\nreasons: none"


def test_render_beyond_chunk_in_term_line() -> None:
    e = explain("word", "some text word", doc_id="d", chunk_chars=10)
    expected = "doc d: no ranking\nword: exact (beyond chunk)\nreasons: term_beyond_chunk"
    assert render(e) == expected


def test_dataclasses_frozen() -> None:
    e = explain("q", "doc", doc_id="d")
    with pytest.raises(AttributeError):
        e.rank = 1  # type: ignore[attr-defined]
    tm = e.terms[0]
    with pytest.raises(AttributeError):
        tm.status = "missing"  # type: ignore[attr-defined]


def test_debug_error_code_attribute() -> None:
    err = DebugError("input_too_large")
    assert err.code == "input_too_large"
    assert "input_too_large" in str(err)


def test_ranking_length_over_limit() -> None:
    ranking = [(f"d{i}", float(i)) for i in range(10_001)]
    with pytest.raises(DebugError) as exc_info:
        explain("q", "doc", doc_id="d", ranking=ranking)
    assert exc_info.value.code == "invalid_ranking"


def test_ranking_non_finite_score() -> None:
    with pytest.raises(DebugError) as exc_info:
        explain("q", "doc", doc_id="d", ranking=[("d", float("nan"))])
    assert exc_info.value.code == "invalid_ranking"


def test_ranking_wrong_type_entry() -> None:
    with pytest.raises(DebugError) as exc_info:
        explain("q", "doc", doc_id="d", ranking=[("d", "not a float")])  # type: ignore[list-item]
    assert exc_info.value.code == "invalid_ranking"


def test_ranking_with_int_score_allowed() -> None:
    e = explain("q", "doc", doc_id="d", ranking=[("d", 1)], k=1)
    assert e.rank == 1
    assert e.in_top_k is True


def test_unsorted_ranking_uses_given_order() -> None:
    # even if not sorted, rank is index in provided order
    e = explain(
        "q",
        "doc",
        doc_id="d2",
        ranking=[("d1", 3.0), ("d2", 1.0), ("d3", 2.0)],
        k=2,
    )
    assert e.rank == 2
    assert e.in_top_k is True
    assert e.gap_to_cutoff is None


def test_doc_id_not_found_with_ranking_length_less_than_k() -> None:
    e = explain(
        "q",
        "doc",
        doc_id="d_missing",
        ranking=[("d1", 1.0)],
        k=5,
    )
    assert e.rank is None
    assert e.in_top_k is None
    assert e.gap_to_cutoff is None
    assert e.reasons == ("not_in_ranking", "missing_terms")
