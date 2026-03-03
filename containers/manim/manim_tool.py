import json
import os
import subprocess
import tempfile
import shutil
from datetime import datetime, timezone
from worker import app
from scenes import get_scene_generator


def _save_result(job_id, tool, data, project="_default", label=None):
    results_dir = os.getenv("RESULTS_DIR", "/data/results")
    project_dir = os.path.join(results_dir, project)
    os.makedirs(project_dir, exist_ok=True)
    run_dir = os.path.join(project_dir, job_id)
    os.makedirs(run_dir, exist_ok=True)

    metadata = {
        "job_id": job_id, "tool": tool, "project": project,
        "label": label, "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(run_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    with open(os.path.join(run_dir, "result.json"), "w") as f:
        json.dump(data, f)

    index_path = os.path.join(project_dir, "_index.json")
    index = []
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
    index.append(metadata)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    return run_dir


# 3D scene types that should be forced to low quality for performance
_3D_SCENE_TYPES = {"bloch_sphere", "orbital_animation", "geodesic_visualization"}

QUALITY_MAP = {
    "low_quality": "-ql",
    "medium_quality": "-qm",
    "high_quality": "-qh",
}


@app.task(name="tools.manim_tool.run_manim", bind=True, soft_time_limit=300)
def run_manim(self, params, project="_default", label=None):
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Manim rendering"})

    sim_type = params.get("simulation_type", "equation_animation")
    quality = params.get("quality", "medium_quality")
    output_format = params.get("format", "mp4")

    try:
        # Generate scene code via registry
        generator = get_scene_generator(sim_type)
        if generator:
            scene_code = generator(params)
            if sim_type in _3D_SCENE_TYPES and quality in ("medium_quality", "high_quality"):
                quality = "low_quality"  # 3D scenes are slower
        elif sim_type == "custom_scene":
            scene_code = params.get("scene_code", "")
            if not scene_code:
                raise ValueError("custom_scene requires scene_code parameter")
        else:
            raise ValueError(f"Unknown simulation_type: {sim_type}")

        self.update_state(state="PROGRESS", meta={"progress": 0.2, "message": "Rendering animation"})

        # Write scene to temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            scene_path = os.path.join(tmpdir, "scene.py")
            with open(scene_path, "w") as f:
                f.write(scene_code)

            # Run Manim
            quality_flag = QUALITY_MAP.get(quality, "-qm")
            format_flag = f"--format={output_format}"

            cmd = [
                "manim", "render",
                quality_flag,
                format_flag,
                scene_path,
                "GeneratedScene",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=280,
                cwd=tmpdir,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Manim render failed: {result.stderr[:500]}")

            self.update_state(state="PROGRESS", meta={"progress": 0.7, "message": "Copying output"})

            # Find the output file
            media_dir = os.path.join(tmpdir, "media")
            output_file = None
            for root, dirs, files in os.walk(media_dir):
                for f in files:
                    if f.endswith(f".{output_format}"):
                        output_file = os.path.join(root, f)
                        break
                if output_file:
                    break

            if not output_file:
                raise RuntimeError("Manim render produced no output file")

            # Copy to results directory
            job_id = self.request.id
            results_dir = os.getenv("RESULTS_DIR", "/data/results")
            run_dir = os.path.join(results_dir, project, job_id)
            os.makedirs(run_dir, exist_ok=True)

            video_filename = f"animation.{output_format}"
            dest_path = os.path.join(run_dir, video_filename)
            shutil.copy2(output_file, dest_path)

            # Get file info
            file_size = os.path.getsize(dest_path)
            video_url = f"/results-files/{project}/{job_id}/{video_filename}"

            result_data = {
                "tool": "manim",
                "simulation_type": sim_type,
                "video_filename": video_filename,
                "video_url": video_url,
                "format": output_format,
                "quality": quality,
                "file_size_bytes": file_size,
            }

    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "manim", result_data, project, label)

    return result_data
