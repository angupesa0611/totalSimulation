"""Tests for the DAG pipeline engine — cycle detection, topological sort, conditions, param resolution."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pipeline_dag import (
    _build_execution_graph,
    _resolve_dag_params,
    _evaluate_condition,
)


class TestBuildExecutionGraph:
    def test_linear_chain(self):
        steps = [
            {"id": "a", "tool": "rebound", "depends_on": []},
            {"id": "b", "tool": "qutip", "depends_on": ["a"]},
            {"id": "c", "tool": "pyscf", "depends_on": ["b"]},
        ]
        adj, order = _build_execution_graph(steps)
        assert order == ["a", "b", "c"]

    def test_parallel_steps(self):
        steps = [
            {"id": "a", "tool": "rebound", "depends_on": []},
            {"id": "b", "tool": "qutip", "depends_on": []},
            {"id": "c", "tool": "pyscf", "depends_on": ["a", "b"]},
        ]
        adj, order = _build_execution_graph(steps)
        assert order[-1] == "c"  # c must be last
        assert set(order[:2]) == {"a", "b"}  # a, b can be in any order

    def test_cycle_detection(self):
        steps = [
            {"id": "a", "tool": "rebound", "depends_on": ["c"]},
            {"id": "b", "tool": "qutip", "depends_on": ["a"]},
            {"id": "c", "tool": "pyscf", "depends_on": ["b"]},
        ]
        with pytest.raises(ValueError, match="cycle"):
            _build_execution_graph(steps)

    def test_unknown_dependency(self):
        steps = [
            {"id": "a", "tool": "rebound", "depends_on": ["nonexistent"]},
        ]
        with pytest.raises(ValueError, match="unknown step"):
            _build_execution_graph(steps)

    def test_single_step(self):
        steps = [{"id": "a", "tool": "rebound", "depends_on": []}]
        adj, order = _build_execution_graph(steps)
        assert order == ["a"]

    def test_diamond_dependency(self):
        steps = [
            {"id": "a", "tool": "rebound", "depends_on": []},
            {"id": "b", "tool": "qutip", "depends_on": ["a"]},
            {"id": "c", "tool": "pyscf", "depends_on": ["a"]},
            {"id": "d", "tool": "openmm", "depends_on": ["b", "c"]},
        ]
        adj, order = _build_execution_graph(steps)
        assert order[0] == "a"
        assert order[-1] == "d"


class TestResolveDagParams:
    def test_step_reference(self):
        step = {
            "params": {"extra": "value"},
            "param_map": {"source_job_id": "$step_a.job_id"},
        }
        completed = {"step_a": {"job_id": "abc-123", "data": {"x": 1}}}
        result = _resolve_dag_params(step, completed, {})
        assert result["source_job_id"] == "abc-123"
        assert result["extra"] == "value"

    def test_nested_step_reference(self):
        step = {
            "params": {},
            "param_map": {"energy": "$sim.data.energy.kinetic"},
        }
        completed = {"sim": {"data": {"energy": {"kinetic": 1.5}}}}
        result = _resolve_dag_params(step, completed, {})
        assert result["energy"] == 1.5

    def test_variable_reference(self):
        step = {
            "params": {},
            "param_map": {"temperature": "$var.temp"},
        }
        variables = {"temp": 300.0}
        result = _resolve_dag_params(step, {}, variables)
        assert result["temperature"] == 300.0

    def test_literal_value(self):
        step = {
            "params": {},
            "param_map": {"basis": "6-31g"},
        }
        result = _resolve_dag_params(step, {}, {})
        assert result["basis"] == "6-31g"

    def test_no_param_map(self):
        step = {"params": {"a": 1, "b": 2}}
        result = _resolve_dag_params(step, {}, {})
        assert result == {"a": 1, "b": 2}


class TestEvaluateCondition:
    def test_equality_true(self):
        completed = {"step_a": {"status": "SUCCESS"}}
        assert _evaluate_condition("$step_a.status == 'SUCCESS'", completed) is True

    def test_equality_false(self):
        completed = {"step_a": {"status": "FAILURE"}}
        assert _evaluate_condition("$step_a.status == 'SUCCESS'", completed) is False

    def test_numeric_comparison(self):
        completed = {"sim": {"data": {"value": 15}}}
        assert _evaluate_condition("$sim.data.value > 10", completed) is True
        assert _evaluate_condition("$sim.data.value > 20", completed) is False

    def test_empty_condition(self):
        assert _evaluate_condition("", {}) is True
        assert _evaluate_condition(None, {}) is True

    def test_missing_step(self):
        assert _evaluate_condition("$nonexistent.status == 'SUCCESS'", {}) is False

    def test_invalid_syntax(self):
        assert _evaluate_condition("not valid python {{", {}) is False

    def test_rejects_function_calls(self):
        completed = {"a": {"status": "SUCCESS"}}
        assert _evaluate_condition("print('hello')", completed) is False
