import os
import tempfile
from pathlib import Path

# Point the app's default engine at a throwaway SQLite file so importing the app
# and running its startup never reaches for a real Postgres. Tests that touch the
# database use their own isolated in-memory engine via dependency override.
_TEST_DB = Path(tempfile.gettempdir()) / "houseflavor_test.db"
_TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
