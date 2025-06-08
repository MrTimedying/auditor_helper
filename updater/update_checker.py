"""
Update Checker for Auditor Helper

Main logic for checking and managing application updates.
"""

import platform
from typing import Optional, Dict, Any
from .github_client import GitHubClient, GitHubRelease
from .version_manager import VersionManager


class UpdateInfo:
    """Contains information about an available update."""
    
    def __init__(self, release: GitHubRelease, current_version: str):
        self.release = release
        self.current_version = current_version
        self.new_version = release.tag_name
        self.release_notes = release.body
        self.download_url = release.get_download_url(self._get_platform())
        self.asset_size = release.get_asset_size(self._get_platform())
        self.is_prerelease = release.prerelease
        self.release_url = release.html_url
    
    def _get_platform(self) -> str:
        """Get the current platform identifier."""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        elif system == "darwin":
            return "macos"
        else:
            return "unknown"
    
    def format_size(self) -> str:
        """Format the asset size in human-readable format."""
        if not self.asset_size:
            return "Unknown size"
        
        size = self.asset_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class UpdateChecker:
    """Handles checking for application updates."""
    
    def __init__(self, repo_owner: str = "MrTimedying", repo_name: str = "auditor_helper"):
        """
        Initialize update checker.
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
        """
        self.github_client = GitHubClient(repo_owner, repo_name)
        self.version_manager = VersionManager()
        self.last_check_result: Optional[UpdateInfo] = None
    
    def check_for_updates(self, include_prereleases: bool = True) -> Optional[UpdateInfo]:
        """
        Check for available updates.
        
        Args:
            include_prereleases: Whether to include beta/pre-release versions
            
        Returns:
            UpdateInfo object if update is available, None otherwise
        """
        try:
            # Get the latest release
            latest_release = self.github_client.get_latest_release(include_prereleases)
            
            if not latest_release:
                print("No releases found on GitHub")
                return None
            
            # Extract version from tag
            remote_version = self.version_manager.extract_version_from_tag(latest_release.tag_name)
            if not remote_version:
                print(f"Could not parse version from tag: {latest_release.tag_name}")
                return None
            
            # Compare versions
            current_version = self.version_manager.get_current_version()
            if self.version_manager.is_newer_version(remote_version, current_version):
                update_info = UpdateInfo(latest_release, current_version)
                self.last_check_result = update_info
                return update_info
            else:
                print(f"Current version {current_version} is up to date (latest: {remote_version})")
                return None
                
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return None
    
    def get_update_summary(self, update_info: UpdateInfo) -> Dict[str, Any]:
        """
        Get a summary of the available update.
        
        Args:
            update_info: UpdateInfo object
            
        Returns:
            Dictionary with update summary information
        """
        return {
            'current_version': update_info.current_version,
            'new_version': update_info.new_version,
            'is_prerelease': update_info.is_prerelease,
            'download_size': update_info.format_size(),
            'has_download': update_info.download_url is not None,
            'release_notes': update_info.release_notes[:500] + "..." if len(update_info.release_notes) > 500 else update_info.release_notes,
            'release_url': update_info.release_url
        }
    
    def is_update_available(self, include_prereleases: bool = True) -> bool:
        """
        Quick check if an update is available.
        
        Args:
            include_prereleases: Whether to include beta/pre-release versions
            
        Returns:
            True if update is available, False otherwise
        """
        return self.check_for_updates(include_prereleases) is not None
    
    def get_current_version_info(self) -> Dict[str, str]:
        """
        Get information about the current version.
        
        Returns:
            Dictionary with current version information
        """
        current_version = self.version_manager.get_current_version()
        return {
            'version': current_version,
            'is_beta': self.version_manager.is_beta_version(current_version),
            'platform': platform.system(),
            'architecture': platform.machine()
        } 