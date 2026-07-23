import json
import time
from pathlib import Path

_LOG_PATH = Path(__file__).resolve().parents[1] / "debug-d1c607.log"
_SESSION_ID = "d1c607"


def debug_log(location: str, message: str, data: dict | None = None, hypothesis_id: str = "", run_id: str = "pre-fix"):
    # region agent log
    try:
        payload = {
            "sessionId": _SESSION_ID,
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
        }
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        pass
    # endregion
