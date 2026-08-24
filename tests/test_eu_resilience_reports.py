from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from zipfile import ZipFile

import pytest


AGENT_DIR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "agents"
    / "eu-resilience-agent"
)
sys.path.insert(0, str(AGENT_DIR))

import functions  # noqa: E402


@pytest.fixture(autouse=True)
def clear_generated_documents():
    with functions._GENERATED_DOCUMENTS_LOCK:
        functions._GENERATED_DOCUMENTS.clear()
    yield
    with functions._GENERATED_DOCUMENTS_LOCK:
        functions._GENERATED_DOCUMENTS.clear()


@pytest.mark.parametrize(
    ("arguments", "expected_scope", "expected_title"),
    [
        (
            {"report_type": "country", "country": "Spain", "limit": None},
            "country",
            "Spain resilience decision briefing",
        ),
        (
            {"report_type": "eu_priorities", "country": None, "limit": 5},
            "eu_priorities",
            "EU27 resilience leadership priorities",
        ),
    ],
)
def test_generates_styled_docx_with_two_charts(
    monkeypatch,
    tmp_path,
    arguments,
    expected_scope,
    expected_title,
):
    monkeypatch.setattr(functions, "_REPORT_OUTPUT_DIR", tmp_path)

    result = functions.generate_resilience_report(**arguments)
    metadata = result["document"]
    generated = functions.get_generated_document(metadata["id"])

    assert result["status"] == "generated"
    assert metadata["scope"] == expected_scope
    assert metadata["title"] == expected_title
    assert metadata["chart_count"] == 2
    assert metadata["download_url"] == f"/api/documents/{metadata['id']}"
    assert "path" not in metadata
    assert generated is not None
    assert generated.path.is_file()

    with ZipFile(generated.path) as archive:
        media = [
            name
            for name in archive.namelist()
            if name.startswith("word/media/")
        ]
        document_xml = archive.read("word/document.xml").decode("utf-8")

    assert len(media) == 2
    assert expected_title in document_xml
    assert "Evidence boundaries" in document_xml


def test_dispatches_report_generation(monkeypatch, tmp_path):
    monkeypatch.setattr(functions, "_REPORT_OUTPUT_DIR", tmp_path)

    output = json.loads(
        functions.call_local_function(
            "generate_resilience_report",
            {
                "report_type": "country",
                "country": "Spain",
                "limit": None,
            },
        )
    )

    assert output["status"] == "generated"
    assert output["document"]["scope"] == "country"
    assert functions.get_generated_document(output["document"]["id"]) is not None


def test_generates_reports_concurrently(monkeypatch, tmp_path):
    monkeypatch.setattr(functions, "_REPORT_OUTPUT_DIR", tmp_path)
    countries = ("Spain", "Italy", "Portugal", "Greece")

    with ThreadPoolExecutor(max_workers=len(countries)) as executor:
        results = list(
            executor.map(
                lambda country: functions.generate_resilience_report(
                    report_type="country",
                    country=country,
                    limit=None,
                ),
                countries,
            )
        )

    document_ids = {result["document"]["id"] for result in results}
    assert len(document_ids) == len(countries)
    for document_id in document_ids:
        generated = functions.get_generated_document(document_id)
        assert generated is not None
        with ZipFile(generated.path) as archive:
            media = [
                name
                for name in archive.namelist()
                if name.startswith("word/media/")
            ]
        assert len(media) == 2
