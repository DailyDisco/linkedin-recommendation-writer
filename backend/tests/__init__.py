"""Test package for LinkedIn Recommendation Writer backend.

``app.core.config`` builds its settings object at import time and SECRET_KEY has
no default, so it has to exist before any test module imports the app. This
package is imported before ``conftest.py``, which makes it the earliest place.
"""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-not-secure")
