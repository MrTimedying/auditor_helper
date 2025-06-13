"""
Auditor Helper Updater Module

This module handles automatic updates for the Auditor Helper application
by checking GitHub releases and managing the update process.
"""

from .version_manager import VersionManager
from .github_client import GitHubClient
from .update_checker import UpdateChecker

__version__ = "1.0.0"
__all__ = ["VersionManager", "GitHubClient", "UpdateChecker"] 