"""Tests for the existing sequential pipeline engine."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pipeline import resolve_param_map


class TestResolveParamMap:
    def test_prev_job_id(self):
        param_map = {"source_job_id": "$prev.job_id"}
        prev_result = {"job_id": "abc-123", "tool": "rebound"}
        result = resolve_param_map(param_map, prev_result)
        assert result["source_job_id"] == "abc-123"

    def test_nested_prev_reference(self):
        param_map = {"energy": "$prev.data.energy.kinetic"}
        prev_result = {"data": {"energy": {"kinetic": 1.5}}}
        result = resolve_param_map(param_map, prev_result)
        assert result["energy"] == 1.5

    def test_array_indexing(self):
        param_map = {"first_pos": "$prev.positions.0"}
        prev_result = {"positions": [[1.0, 2.0], [3.0, 4.0]]}
        result = resolve_param_map(param_map, prev_result)
        assert result["first_pos"] == [1.0, 2.0]

    def test_literal_value(self):
        param_map = {"basis": "6-31g"}
        prev_result = {"job_id": "abc"}
        result = resolve_param_map(param_map, prev_result)
        assert result["basis"] == "6-31g"

    def test_missing_path(self):
        param_map = {"val": "$prev.nonexistent.deep.path"}
        prev_result = {"data": {}}
        result = resolve_param_map(param_map, prev_result)
        assert result["val"] is None

    def test_empty_param_map(self):
        result = resolve_param_map({}, {"data": 1})
        assert result == {}
