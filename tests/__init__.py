"""
Test package initialization.
This file ensures that OpenTelemetry is disabled before any tests are run.
"""

import os

# Disable OpenTelemetry exporter by setting environment variables
# before any modules are imported
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["OTEL_PYTHON_DISABLED"] = "true"
