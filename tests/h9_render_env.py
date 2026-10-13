"""
Shared helper for tests that exercise the pipeline's stages and hand-offs but not video pixels.

The default render backend is the REAL one (headless Chromium + the measured media gate). A test that
only needs "a pipeline run finished" must say so explicitly by selecting the labelled dry-run backend.
Real rendering is covered by tests/test_render_backend.py and tests/test_media_gate.py.

Usage in a unittest module:

    from tests.h9_render_env import setUpModule, tearDownModule  # noqa: F401
"""

import os
from unittest import mock

_patcher = None


def setUpModule():  # noqa: N802 - unittest/pytest module fixture name
    global _patcher
    _patcher = mock.patch.dict(os.environ, {"HARNESS9_RENDER_BACKEND": "stub"})
    _patcher.start()


def tearDownModule():  # noqa: N802
    global _patcher
    if _patcher is not None:
        _patcher.stop()
        _patcher = None
