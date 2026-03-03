"""Tests for result persistence — save/get/list/delete/search operations."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import tempfile
import pytest
from unittest.mock import patch


class TestResultOperations:
    @pytest.fixture(autouse=True)
    def setup_temp_dir(self, tmp_path):
        """Use temp directory for results during tests."""
        self.results_dir = str(tmp_path)
        patcher1 = patch("config.settings")
        patcher2 = patch("results.settings")
        mock1 = patcher1.start()
        mock2 = patcher2.start()
        mock1.results_dir = self.results_dir
        mock2.results_dir = self.results_dir
        yield
        patcher1.stop()
        patcher2.stop()

    def test_save_and_get_result(self):
        from results import save_result, get_result

        data = {"tool": "rebound", "data": {"energy": 1.5}}
        save_result("job-001", "rebound", data, "_default", "Test run")

        result = get_result("job-001", "_default")
        assert result is not None
        assert result["data"]["energy"] == 1.5

    def test_list_results(self):
        from results import save_result, list_results

        save_result("job-001", "rebound", {"data": 1}, "_default")
        save_result("job-002", "qutip", {"data": 2}, "_default")

        results = list_results("_default")
        assert len(results) == 2
        assert results[0]["job_id"] == "job-001"
        assert results[1]["job_id"] == "job-002"

    def test_get_nonexistent_result(self):
        from results import get_result

        result = get_result("nonexistent", "_default")
        assert result is None

    def test_separate_projects(self):
        from results import save_result, list_results

        save_result("job-001", "rebound", {"data": 1}, "project_a")
        save_result("job-002", "qutip", {"data": 2}, "project_b")

        assert len(list_results("project_a")) == 1
        assert len(list_results("project_b")) == 1
        assert len(list_results("project_c")) == 0

    def test_save_result_creates_metadata(self):
        from results import save_result

        save_result("job-meta", "rebound", {"data": 1}, "_default", "Meta test")

        meta_path = os.path.join(self.results_dir, "_default", "job-meta", "metadata.json")
        assert os.path.exists(meta_path)

        with open(meta_path) as f:
            meta = json.load(f)
        assert meta["job_id"] == "job-meta"
        assert meta["tool"] == "rebound"
        assert meta["label"] == "Meta test"

    # --- Phase 15: Enriched metadata tests ---

    def test_save_result_enriched_metadata(self):
        from results import save_result

        data = {"result": "ok"}
        params = {"integrator": "whfast", "tmax": 62.83}
        save_result(
            "job-enriched", "rebound", data, "_default", "Enriched",
            duration=3.21, params=params, status="SUCCESS",
        )

        meta_path = os.path.join(self.results_dir, "_default", "job-enriched", "metadata.json")
        with open(meta_path) as f:
            meta = json.load(f)

        assert meta["status"] == "SUCCESS"
        assert meta["duration_s"] == 3.21
        assert meta["params_summary"] is not None
        assert "whfast" in meta["params_summary"]
        assert meta["result_size_bytes"] > 0
        assert meta["error"] is None

    def test_save_result_failure_status(self):
        from results import save_result

        save_result(
            "job-fail", "qutip", {}, "_default",
            status="FAILURE", error="Dimension mismatch",
        )

        meta_path = os.path.join(self.results_dir, "_default", "job-fail", "metadata.json")
        with open(meta_path) as f:
            meta = json.load(f)

        assert meta["status"] == "FAILURE"
        assert meta["error"] == "Dimension mismatch"

    # --- Phase 15: Delete tests ---

    def test_delete_result(self):
        from results import save_result, delete_result, list_results, get_result

        save_result("job-del", "rebound", {"x": 1}, "_default")
        assert get_result("job-del", "_default") is not None

        deleted = delete_result("job-del", "_default")
        assert deleted is True
        assert get_result("job-del", "_default") is None

        results = list_results("_default")
        assert all(r["job_id"] != "job-del" for r in results)

    def test_delete_nonexistent_result(self):
        from results import delete_result

        assert delete_result("nonexistent", "_default") is False

    # --- Phase 15: Status update tests ---

    def test_update_result_status(self):
        from results import save_result, update_result_status, list_results

        save_result("job-upd", "rebound", {"x": 1}, "_default", status="RUNNING")
        updated = update_result_status("job-upd", "_default", "INTERRUPTED", "Server restarted")
        assert updated is True

        results = list_results("_default")
        entry = next(r for r in results if r["job_id"] == "job-upd")
        assert entry["status"] == "INTERRUPTED"

    def test_update_nonexistent_status(self):
        from results import update_result_status

        assert update_result_status("ghost", "_default", "CANCELLED") is False

    # --- Phase 15: Search tests ---

    def test_search_results_basic(self):
        from results import save_result, search_results

        save_result("s-001", "rebound", {"x": 1}, "_default", "alpha")
        save_result("s-002", "qutip", {"x": 2}, "_default", "beta")
        save_result("s-003", "rebound", {"x": 3}, "_default", "gamma", status="FAILURE")

        result = search_results("_default")
        assert result["total"] == 3
        assert len(result["results"]) == 3

    def test_search_results_tool_filter(self):
        from results import save_result, search_results

        save_result("f-001", "rebound", {"x": 1}, "_default")
        save_result("f-002", "qutip", {"x": 2}, "_default")

        result = search_results("_default", tool_filter="rebound")
        assert result["total"] == 1
        assert result["results"][0]["tool"] == "rebound"

    def test_search_results_status_filter(self):
        from results import save_result, search_results

        save_result("sf-001", "rebound", {"x": 1}, "_default", status="SUCCESS")
        save_result("sf-002", "rebound", {"x": 2}, "_default", status="FAILURE")

        result = search_results("_default", status_filter="FAILURE")
        assert result["total"] == 1
        assert result["results"][0]["status"] == "FAILURE"

    def test_search_results_query(self):
        from results import save_result, search_results

        save_result("q-001", "rebound", {"x": 1}, "_default", "solar system")
        save_result("q-002", "qutip", {"x": 2}, "_default", "rabi oscillation")

        result = search_results("_default", query="solar")
        assert result["total"] == 1
        assert result["results"][0]["label"] == "solar system"

    def test_search_results_pagination(self):
        from results import save_result, search_results

        for i in range(5):
            save_result(f"p-{i:03d}", "rebound", {"x": i}, "_default")

        page1 = search_results("_default", offset=0, limit=2)
        assert len(page1["results"]) == 2
        assert page1["total"] == 5

        page2 = search_results("_default", offset=2, limit=2)
        assert len(page2["results"]) == 2

        page3 = search_results("_default", offset=4, limit=2)
        assert len(page3["results"]) == 1

    # --- Phase 15: File listing tests ---

    def test_get_result_files(self):
        from results import save_result, get_result_files

        save_result("fl-001", "rebound", {"x": 1}, "_default")

        files = get_result_files("fl-001", "_default")
        assert files is not None
        names = [f["name"] for f in files]
        assert "metadata.json" in names
        assert "result.json" in names

    def test_get_result_files_nonexistent(self):
        from results import get_result_files

        assert get_result_files("ghost", "_default") is None

    # --- Phase 15: File path security ---

    def test_get_result_file_path_blocks_traversal(self):
        from results import save_result, get_result_file_path

        save_result("sec-001", "rebound", {"x": 1}, "_default")

        path = get_result_file_path("sec-001", "../../etc/passwd", "_default")
        assert path is None

    def test_get_result_file_path_valid(self):
        from results import save_result, get_result_file_path

        save_result("sec-002", "rebound", {"x": 1}, "_default")

        path = get_result_file_path("sec-002", "metadata.json", "_default")
        assert path is not None
        assert path.endswith("metadata.json")

    # --- Phase 15: Project management tests ---

    def test_list_projects(self):
        from results import save_result, list_projects

        save_result("lp-001", "rebound", {"x": 1}, "_default")
        save_result("lp-002", "rebound", {"x": 2}, "my_project")

        projects = list_projects()
        assert "_default" in projects
        assert "my_project" in projects

    def test_create_project(self):
        from results import create_project, list_projects

        created = create_project("new_proj")
        assert created is True

        assert "new_proj" in list_projects()

        # Duplicate should return False
        assert create_project("new_proj") is False

    def test_delete_project(self):
        from results import create_project, delete_project, list_projects

        create_project("temp_proj")
        assert "temp_proj" in list_projects()

        deleted = delete_project("temp_proj")
        assert deleted is True
        assert "temp_proj" not in list_projects()

    def test_cannot_delete_default_project(self):
        from results import delete_project

        assert delete_project("_default") is False

    # --- Phase 15: Startup recovery ---

    def test_startup_recovery(self):
        from results import save_result, list_results

        save_result("stale-001", "rebound", {"x": 1}, "_default", status="RUNNING")
        save_result("stale-002", "qutip", {"x": 2}, "_default", status="PENDING")
        save_result("ok-001", "openmm", {"x": 3}, "_default", status="SUCCESS")

        # Simulate recovery logic (same as main._recover_stale_jobs)
        from results import update_result_status
        for entry in list_results("_default"):
            if entry.get("status") in ("RUNNING", "PENDING"):
                update_result_status(
                    entry["job_id"], "_default", "INTERRUPTED",
                    error="Server restarted while job was in progress",
                )

        results = list_results("_default")
        statuses = {r["job_id"]: r["status"] for r in results}
        assert statuses["stale-001"] == "INTERRUPTED"
        assert statuses["stale-002"] == "INTERRUPTED"
        assert statuses["ok-001"] == "SUCCESS"
