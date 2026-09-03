"""Evaluation API endpoint — runs the evaluation suite."""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.post("/run")
async def run_evaluation():
    """Run the evaluation suite and return results."""
    try:
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "../../evaluation/evaluate.py", "--json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr, "success": False}
    except Exception as e:
        logger.error(f"Evaluation run failed: {e}")
        return {"error": str(e), "success": False}


@router.get("/datasets")
def list_datasets():
    """List available evaluation datasets."""
    import os
    from pathlib import Path
    datasets_dir = Path("../../evaluation/datasets")
    if not datasets_dir.exists():
        return {"datasets": []}
    files = [f.name for f in datasets_dir.glob("*.json")]
    return {"datasets": files}
