"""
Version Manager for Auditor Helper

Handles version detection, parsing, and comparison logic.
"""

import re
from typing import Optional, Tuple
from packaging import version
from pathlib import Path


class VersionManager:
    """Manages version detection and comparison for the application."""
    
    def __init__(self):
        self.current_version = self._get_current_app_version()
    
    def _get_current_app_version(self) -> str:
        """Extract the current application version from CHANGELOG.md."""
        changelog_file = Path(__file__).resolve().parents[2] / "docs" / "CHANGELOG.md"
        if not changelog_file.exists():
            print("⚠️ CHANGELOG.md not found. Defaulting app version to 1.0.0")
            return "1.0.0"

        try:
            with open(changelog_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Iterate forward to find the first (latest) version
                for line in lines:
                    if line.startswith("## v"):
                        # Extract version using regex: ## vX.Y.Z-beta (Title)
                        match = re.match(r"## (v\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)*)", line)
                        if match:
                            return match.group(1)
            print("⚠️ No version found in CHANGELOG.md. Defaulting app version to 1.0.0")
        except Exception as e:
            print(f"⚠️ Could not read app version from CHANGELOG.md: {e}")
        return "1.0.0"

    def get_current_version(self) -> str:
        """Get the current application version."""
        return self.current_version
    
    def parse_version(self, version_string: str) -> Optional[version.Version]:
        """
        Parse a version string into a Version object.
        
        Args:
            version_string: Version string (e.g., "v0.16.8-beta", "0.16.8-beta")
            
        Returns:
            Parsed Version object or None if parsing fails
        """
        try:
            # Remove 'v' prefix if present
            clean_version = version_string.lstrip('v')
            return version.parse(clean_version)
        except Exception:
            return None
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
            None if comparison fails
        """
        try:
            v1 = self.parse_version(version1)
            v2 = self.parse_version(version2)
            
            if v1 is None or v2 is None:
                return None
                
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0
        except Exception:
            return None
    
    def is_newer_version(self, remote_version: str, current_version: Optional[str] = None) -> bool:
        """
        Check if a remote version is newer than the current version.
        
        Args:
            remote_version: Version string from remote source
            current_version: Current version (uses self.current_version if None)
            
        Returns:
            True if remote version is newer, False otherwise
        """
        if current_version is None:
            current_version = self.current_version
            
        comparison = self.compare_versions(current_version, remote_version)
        return comparison == -1  # current < remote
    
    def extract_version_from_tag(self, tag_name: str) -> Optional[str]:
        """
        Extract version from a git tag name.
        
        Args:
            tag_name: Git tag name (e.g., "v0.16.8-beta", "release-0.16.8")
            
        Returns:
            Extracted version string or None if extraction fails
        """
        # Common patterns for version tags
        patterns = [
            r'^v?(\d+\.\d+\.\d+(?:-\w+)?)$',  # v0.16.8-beta or 0.16.8-beta
            r'^release-v?(\d+\.\d+\.\d+(?:-\w+)?)$',  # release-v0.16.8-beta
            r'^(\d+\.\d+\.\d+(?:-\w+)?)$',  # 0.16.8-beta
        ]
        
        for pattern in patterns:
            match = re.match(pattern, tag_name)
            if match:
                return match.group(1)
        
        return None
    
    def is_beta_version(self, version_string: str) -> bool:
        """
        Check if a version is a beta/pre-release version.
        
        Args:
            version_string: Version string to check
            
        Returns:
            True if version contains beta/alpha/rc indicators
        """
        version_string = version_string.lower()
        beta_indicators = ['beta', 'alpha', 'rc', 'pre', 'dev']
        return any(indicator in version_string for indicator in beta_indicators) 