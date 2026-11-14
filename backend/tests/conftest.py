import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Base de datos temporal: las pruebas nunca tocan backend/basal.db
os.environ["BASAL_DB"] = os.path.join(tempfile.mkdtemp(prefix="basal_test_"), "test.db")


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from basal.main import app
    return TestClient(app)


@pytest.fixture()
def fresh(client):
    """Misión de demostración recién inicializada."""
    client.post("/api/sim/reset", json={"seed": 7})
    return client
