"""
Version Manager for Auditor Helper

Handles version detection, parsing, and comparison logic.
"""

import re
from typing import Optional, Tuple
from packaging import version


class VersionManager:
    """Manages version detection and comparison for the application."""
    
    # Current app version - this should be updated with each release
    CURRENT_VERSION = "0.16.8-beta"
    
    def __init__(self):
        self.current_version = self.CURRENT_VERSION
    
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