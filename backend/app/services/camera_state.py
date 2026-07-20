"""Thread-safe shared state for cross-module camera session coordination.

The realtime camera WebSocket runs in the async API layer while background
video tracking tasks run on sync worker threads. This tiny module exposes a
threading.Event so that video tasks can detect an active camera session and
voluntarily throttle GPU/CPU usage.
"""

import threading

_camera_active = threading.Event()


def set_camera_active() -> None:
    """Mark a camera realtime session as active."""
    _camera_active.set()


def set_camera_inactive() -> None:
    """Mark a camera realtime session as inactive."""
    _camera_active.clear()


def is_camera_active() -> bool:
    """Return True if a camera realtime session is currently active."""
    return _camera_active.is_set()
