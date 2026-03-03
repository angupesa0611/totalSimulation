"""Tests for the sweep engine — sampling methods, axis application, orchestration."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models.sweep import SweepAxis, SweepRequest
from sweep import (
    _expand_axis_values,
    _apply_axis_value,
    generate_sweep_points,
)


class TestExpandAxisValues:
    def test_explicit_values(self):
        axis = SweepAxis(param="dt", values=[0.1, 0.5, 1.0])
        result = _expand_axis_values(axis)
        assert result == [0.1, 0.5, 1.0]

    def test_linear_range(self):
        axis = SweepAxis(param="dt", range={"min": 0.0, "max": 1.0, "steps": 5})
        result = _expand_axis_values(axis)
        assert len(result) == 5
        assert result[0] == pytest.approx(0.0)
        assert result[-1] == pytest.approx(1.0)

    def test_log_range(self):
        axis = SweepAxis(param="dt", range={"min": 0.01, "max": 100.0, "steps": 5}, log_scale=True)
        result = _expand_axis_values(axis)
        assert len(result) == 5
        assert result[0] == pytest.approx(0.01)
        assert result[-1] == pytest.approx(100.0)
        # Log spacing: each step should multiply by the same factor
        ratio = result[1] / result[0]
        assert result[2] / result[1] == pytest.approx(ratio, rel=1e-5)

    def test_empty_axis(self):
        axis = SweepAxis(param="dt")
        result = _expand_axis_values(axis)
        assert result == []


class TestApplyAxisValue:
    def test_simple_path(self):
        params = {"dt": 0.1, "steps": 100}
        result = _apply_axis_value(params, "dt", 0.5)
        assert result["dt"] == 0.5
        # Original should not be modified
        assert params["dt"] == 0.1

    def test_nested_path(self):
        params = {"integrator": {"dt": 0.1, "type": "leapfrog"}}
        result = _apply_axis_value(params, "integrator.dt", 0.5)
        assert result["integrator"]["dt"] == 0.5
        assert result["integrator"]["type"] == "leapfrog"

    def test_creates_nested_path(self):
        params = {"steps": 100}
        result = _apply_axis_value(params, "integrator.dt", 0.5)
        assert result["integrator"]["dt"] == 0.5


class TestGenerateSweepPoints:
    def test_grid_single_axis(self):
        axes = [SweepAxis(param="dt", values=[0.1, 0.5, 1.0])]
        points = generate_sweep_points(axes, "grid", None, {"steps": 100})
        assert len(points) == 3
        assert points[0]["dt"] == 0.1
        assert points[1]["dt"] == 0.5
        assert points[2]["dt"] == 1.0
        # Base params preserved
        assert all(p["steps"] == 100 for p in points)

    def test_grid_two_axes(self):
        axes = [
            SweepAxis(param="dt", values=[0.1, 0.5]),
            SweepAxis(param="steps", values=[100, 200]),
        ]
        points = generate_sweep_points(axes, "grid", None, {})
        assert len(points) == 4  # 2 x 2

    def test_grid_three_axes(self):
        axes = [
            SweepAxis(param="a", values=[1, 2]),
            SweepAxis(param="b", values=[3, 4]),
            SweepAxis(param="c", values=[5, 6]),
        ]
        points = generate_sweep_points(axes, "grid", None, {})
        assert len(points) == 8  # 2 x 2 x 2

    def test_random_method(self):
        axes = [SweepAxis(param="dt", values=[0.1, 0.5, 1.0])]
        points = generate_sweep_points(axes, "random", 7, {})
        assert len(points) == 7
        assert all("dt" in p for p in points)

    def test_lhs_method(self):
        axes = [SweepAxis(param="dt", values=[0.1, 0.5, 1.0, 2.0, 5.0])]
        points = generate_sweep_points(axes, "lhs", 5, {})
        assert len(points) == 5
        assert all("dt" in p for p in points)

    def test_unknown_method_raises(self):
        axes = [SweepAxis(param="dt", values=[0.1])]
        with pytest.raises(ValueError, match="Unknown sweep method"):
            generate_sweep_points(axes, "invalid", None, {})
