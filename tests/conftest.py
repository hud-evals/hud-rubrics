"""Shared fixtures for hud-rubrics test suite."""

from dotenv import load_dotenv

load_dotenv()

import pytest
from fastapi.testclient import TestClient

from environment.server import app, state


@pytest.fixture
def client():
    """FastAPI TestClient with fresh state."""

    state.reset()
    yield TestClient(app)
    state.reset()
