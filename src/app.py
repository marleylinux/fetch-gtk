#!/usr/bin/env python3
"""Application entry point for fetch-gtk"""
import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import init_gi  # noqa: F401, E402
from main import FetchGtkApp  # noqa: E402

if __name__ == "__main__":
    app = FetchGtkApp()
    sys.exit(app.run(sys.argv))
