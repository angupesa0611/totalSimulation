"""Tests for the export engine — CSV/JSON/LaTeX generation, result flattening."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from export_engine import (
    _flatten_dict,
    _to_csv,
    _to_json,
    _to_latex,
    _filter_columns,
    _latex_escape,
)


class TestFlattenDict:
    def test_simple_dict(self):
        d = {"a": 1, "b": "hello"}
        result = _flatten_dict(d)
        assert result == {"a": 1, "b": "hello"}

    def test_nested_dict(self):
        d = {"energy": {"kinetic": 1.5, "potential": -3.0}}
        result = _flatten_dict(d)
        assert result["energy.kinetic"] == 1.5
        assert result["energy.potential"] == -3.0

    def test_deeply_nested(self):
        d = {"a": {"b": {"c": 42}}}
        result = _flatten_dict(d)
        assert result["a.b.c"] == 42

    def test_list_values_short(self):
        d = {"coords": [1.0, 2.0, 3.0]}
        result = _flatten_dict(d)
        assert result["coords"] == str([1.0, 2.0, 3.0])

    def test_list_values_long(self):
        d = {"data": list(range(100))}
        result = _flatten_dict(d)
        assert "100 items" in result["data"]


class TestFilterColumns:
    def test_auto_columns(self):
        results = [{"a": 1, "b": 2}, {"a": 3, "c": 4}]
        cols, _ = _filter_columns(results, None)
        assert "a" in cols
        assert "b" in cols
        assert "c" in cols

    def test_specified_columns(self):
        results = [{"a": 1, "b": 2, "c": 3}]
        cols, _ = _filter_columns(results, ["a", "c"])
        assert cols == ["_job_id", "a", "c"]


class TestToCSV:
    def test_basic_csv(self, sample_flat_results):
        columns = ["_job_id", "tool", "data.energy.kinetic"]
        csv_str = _to_csv(sample_flat_results, columns)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 3  # header + 2 data rows
        assert "_job_id" in lines[0]
        assert "job-001" in lines[1]


class TestToJSON:
    def test_basic_json(self, sample_flat_results):
        import json
        columns = ["_job_id", "tool"]
        json_str = _to_json(sample_flat_results, columns)
        parsed = json.loads(json_str)
        assert len(parsed) == 2
        assert parsed[0]["_job_id"] == "job-001"


class TestToLatex:
    def test_basic_latex(self, sample_flat_results):
        columns = ["_job_id", "tool"]
        latex = _to_latex(sample_flat_results, columns, "Test Results")
        assert "\\begin{tabular}" in latex
        assert "\\toprule" in latex
        assert "\\bottomrule" in latex
        assert "Test Results" in latex

    def test_latex_without_title(self, sample_flat_results):
        columns = ["_job_id", "tool"]
        latex = _to_latex(sample_flat_results, columns, None)
        assert "\\begin{tabular}" in latex
        assert "\\caption" not in latex


class TestLatexEscape:
    def test_special_chars(self):
        assert _latex_escape("a & b") == "a \\& b"
        assert _latex_escape("100%") == "100\\%"
        assert _latex_escape("$x$") == "\\$x\\$"
        assert _latex_escape("a_b") == "a\\_b"
