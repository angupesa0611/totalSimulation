import json
import os
import shutil
from datetime import datetime, timezone
from config import settings


def get_results_dir(project: str = "_default") -> str:
    path = os.path.join(settings.results_dir, project)
    os.makedirs(path, exist_ok=True)
    return path


def save_result(job_id: str, tool: str, data: dict, project: str = "_default",
                label: str | None = None, duration: float | None = None,
                params: dict | None = None, status: str = "SUCCESS",
                error: str | None = None) -> str:
    """Save simulation result to disk. Returns the result directory path."""
    results_dir = get_results_dir(project)
    run_dir = os.path.join(results_dir, f"{job_id}")
    os.makedirs(run_dir, exist_ok=True)

    data_str = json.dumps(data)
    params_summary = json.dumps(params)[:200] if params else None

    metadata = {
        "job_id": job_id,
        "tool": tool,
        "project": project,
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "duration_s": duration,
        "params_summary": params_summary,
        "result_size_bytes": len(data_str),
        "error": error,
    }
    with open(os.path.join(run_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    with open(os.path.join(run_dir, "result.json"), "w") as f:
        f.write(data_str)

    _update_index(project, metadata)
    return run_dir


def _update_index(project: str, entry: dict) -> None:
    """Append or update entry in project's _index.json."""
    results_dir = get_results_dir(project)
    index_path = os.path.join(results_dir, "_index.json")

    index = []
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)

    # Replace existing entry for same job_id, or append
    existing = next((i for i, e in enumerate(index) if e.get("job_id") == entry["job_id"]), None)
    if existing is not None:
        index[existing] = entry
    else:
        index.append(entry)

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)


def delete_result(job_id: str, project: str = "_default") -> bool:
    """Delete a result directory and remove from _index.json. Returns True if found."""
    results_dir = get_results_dir(project)
    run_dir = os.path.join(results_dir, job_id)

    if not os.path.exists(run_dir):
        return False

    shutil.rmtree(run_dir)

    # Remove from index
    index_path = os.path.join(results_dir, "_index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
        index = [e for e in index if e.get("job_id") != job_id]
        with open(index_path, "w") as f:
            json.dump(index, f, indent=2)

    return True


def update_result_status(job_id: str, project: str = "_default",
                         status: str = "SUCCESS", error: str | None = None) -> bool:
    """Update the status of an existing result. Returns True if found."""
    results_dir = get_results_dir(project)
    meta_path = os.path.join(results_dir, job_id, "metadata.json")

    if not os.path.exists(meta_path):
        return False

    with open(meta_path) as f:
        metadata = json.load(f)

    metadata["status"] = status
    if error is not None:
        metadata["error"] = error

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    _update_index(project, metadata)
    return True


def search_results(project: str = "_default", query: str | None = None,
                   tool_filter: str | None = None, status_filter: str | None = None,
                   sort: str = "newest", offset: int = 0,
                   limit: int = 20) -> dict:
    """Search and filter results with pagination. Returns {results, total}."""
    all_results = list_results(project)

    # Apply filters
    filtered = all_results
    if tool_filter:
        filtered = [r for r in filtered if r.get("tool") == tool_filter]
    if status_filter:
        filtered = [r for r in filtered if r.get("status", "SUCCESS") == status_filter]
    if query:
        q = query.lower()
        filtered = [r for r in filtered if (
            q in (r.get("label") or "").lower() or
            q in (r.get("tool") or "").lower() or
            q in (r.get("job_id") or "").lower() or
            q in (r.get("params_summary") or "").lower()
        )]

    # Sort
    if sort == "newest":
        filtered.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    elif sort == "oldest":
        filtered.sort(key=lambda r: r.get("timestamp", ""))
    elif sort == "tool":
        filtered.sort(key=lambda r: r.get("tool", ""))

    total = len(filtered)
    page = filtered[offset:offset + limit]

    return {"results": page, "total": total, "offset": offset, "limit": limit}


def get_result_files(job_id: str, project: str = "_default") -> list[dict] | None:
    """List files in a result directory. Returns None if not found."""
    results_dir = get_results_dir(project)
    run_dir = os.path.join(results_dir, job_id)

    if not os.path.exists(run_dir):
        return None

    files = []
    for name in sorted(os.listdir(run_dir)):
        filepath = os.path.join(run_dir, name)
        if os.path.isfile(filepath):
            files.append({
                "name": name,
                "size_bytes": os.path.getsize(filepath),
            })
    return files


def get_result_file_path(job_id: str, filename: str,
                         project: str = "_default") -> str | None:
    """Get absolute path of a file in a result directory. Returns None if not found."""
    results_dir = get_results_dir(project)
    filepath = os.path.join(results_dir, job_id, filename)

    # Prevent path traversal
    real_path = os.path.realpath(filepath)
    real_base = os.path.realpath(os.path.join(results_dir, job_id))
    if not real_path.startswith(real_base):
        return None

    if not os.path.isfile(filepath):
        return None
    return filepath


def list_projects() -> list[str]:
    """List all project directories."""
    base = settings.results_dir
    if not os.path.exists(base):
        return ["_default"]
    projects = []
    for name in sorted(os.listdir(base)):
        if os.path.isdir(os.path.join(base, name)) and not name.startswith("."):
            projects.append(name)
    if not projects:
        projects = ["_default"]
    return projects


def create_project(name: str) -> bool:
    """Create a new project directory. Returns True if created, False if exists."""
    results_dir = get_results_dir(name)
    index_path = os.path.join(results_dir, "_index.json")
    if os.path.exists(index_path):
        return False
    with open(index_path, "w") as f:
        json.dump([], f)
    return True


def delete_project(name: str) -> bool:
    """Delete a project and all its results. Returns True if deleted."""
    if name == "_default":
        return False
    project_dir = os.path.join(settings.results_dir, name)
    if not os.path.exists(project_dir):
        return False
    shutil.rmtree(project_dir)
    return True


def get_result_metadata(job_id: str, project: str = "_default") -> dict | None:
    """Get metadata for a specific result."""
    results_dir = get_results_dir(project)
    meta_path = os.path.join(results_dir, job_id, "metadata.json")
    if not os.path.exists(meta_path):
        return None
    with open(meta_path) as f:
        return json.load(f)


def list_results(project: str = "_default") -> list[dict]:
    """List all results for a project."""
    results_dir = get_results_dir(project)
    index_path = os.path.join(results_dir, "_index.json")
    if not os.path.exists(index_path):
        return []
    with open(index_path) as f:
        return json.load(f)


def get_result(job_id: str, project: str = "_default") -> dict | None:
    """Get a specific result by job_id."""
    results_dir = get_results_dir(project)
    result_path = os.path.join(results_dir, job_id, "result.json")
    if not os.path.exists(result_path):
        return None
    with open(result_path) as f:
        return json.load(f)


def get_result_data(job_id: str, project: str = "_default") -> dict | None:
    """Get result data for pipeline chaining. Tries saved file first, then Celery backend."""
    result = get_result(job_id, project)
    if result is not None:
        return result

    from celery.result import AsyncResult
    from celery_app import app as celery_app
    ar = AsyncResult(job_id, app=celery_app)
    if ar.status == "SUCCESS":
        return ar.result
    return None
