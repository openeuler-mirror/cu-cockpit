"""Offline inspection core regressions with isolated collectors and child processes."""

import subprocess
import sys
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from osmanager.system_management import alerts, inspection, inspection_collectors, monitoring


class InspectionCenterTest(unittest.TestCase):
    """Exercise the synchronous core without Django setup or host commands."""


if __name__ == '__main__':
    unittest.main()
