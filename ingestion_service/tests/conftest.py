from __future__ import annotations

import sys
from pathlib import Path

# Ensure `import ingestion_service...` works even when pytest is run from
# inside subdirectories (e.g., `cd ingestion_service/tests`).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


