"""
GitHub API Client for Auditor Helper

Handles communication with GitHub API to fetch release information.
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Any
from datetime import datetime


class GitHubRelease:
    """Represents a GitHub release."""
    
    def __init__(self, release_data: Dict[str, Any]):
        self.data = release_data
        self.tag_name = release_data.get('tag_name', '')
        self.name = release_data.get('name', '')
        self.body = release_data.get('body', '')
        self.prerelease = release_data.get('prerelease', False)
        self.draft = release_data.get('draft', False)
        self.published_at = release_data.get('published_at', '')
        self.html_url = release_data.get('html_url', '')
        self.assets = release_data.get('assets', [])
    
    def get_download_url(self, platform: str = None) -> Optional[str]:
        """
        Get download URL for the appropriate platform asset.
        
        Args:
            platform: Target platform ('windows', 'linux', 'macos')
            
        Returns:
            Download URL or None if no suitable asset found
        """
        if not self.assets:
            return None
        
        # If no platform specified, return first asset
        if platform is None and self.assets:
            return self.assets[0].get('browser_download_url')
        
        # Platform-specific asset selection
        platform_patterns = {
            'windows': ['.exe', 'win', 'windows'],
            'linux': ['.AppImage', 'linux', '.tar.gz'],
            'macos': ['.dmg', 'mac', 'darwin']
        }
        
        if platform in platform_patterns:
            patterns = platform_patterns[platform]
            for asset in self.assets:
                asset_name = asset.get('name', '').lower()
                if any(pattern.lower() in asset_name for pattern in patterns):
                    return asset.get('browser_download_url')
        
        return None
    
    def get_asset_size(self, platform: str = None) -> Optional[int]:
        """Get the size of the asset for the specified platform."""
        if not self.assets:
            return None
            
        download_url = self.get_download_url(platform)
        if not download_url:
            return None
            
        for asset in self.assets:
            if asset.get('browser_download_url') == download_url:
                return asset.get('size', 0)
        
        return None


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, repo_owner: str, repo_name: str):
        """
        Initialize GitHub client.
        
        Args:
            repo_owner: GitHub repository owner/organization
            repo_name: Repository name
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    
    def _make_request(self, url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to GitHub API.
        
        Args:
            url: API endpoint URL
            timeout: Request timeout in seconds
            
        Returns:
            JSON response data or None if request fails
        """
        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'AuditorHelper-Updater/1.0'
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
                else:
                    print(f"GitHub API request failed with status: {response.status}")
                    return None
                    
        except urllib.error.HTTPError as e:
            print(f"HTTP error fetching GitHub data: {e.code} - {e.reason}")
            return None
        except urllib.error.URLError as e:
            print(f"URL error fetching GitHub data: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching GitHub data: {e}")
            return None
    
    def get_latest_release(self, include_prereleases: bool = True) -> Optional[GitHubRelease]:
        """
        Get the latest release from the repository.
        
        Args:
            include_prereleases: Whether to include pre-release versions
            
        Returns:
            GitHubRelease object or None if no release found
        """
        if include_prereleases:
            # Get all releases and find the latest (including prereleases)
            releases = self.get_releases(per_page=1)
            return releases[0] if releases else None
        else:
            # Get latest stable release only
            url = f"{self.base_url}/releases/latest"
            data = self._make_request(url)
            return GitHubRelease(data) if data else None
    
    def get_releases(self, per_page: int = 10, page: int = 1) -> List[GitHubRelease]:
        """
        Get list of releases from the repository.
        
        Args:
            per_page: Number of releases per page (max 100)
            page: Page number to fetch
            
        Returns:
            List of GitHubRelease objects
        """
        url = f"{self.base_url}/releases?per_page={per_page}&page={page}"
        data = self._make_request(url)
        
        if data and isinstance(data, list):
            releases = []
            for release_data in data:
                # Skip draft releases
                if not release_data.get('draft', False):
                    releases.append(GitHubRelease(release_data))
            return releases
        
        return []
    
    def get_release_by_tag(self, tag: str) -> Optional[GitHubRelease]:
        """
        Get a specific release by tag name.
        
        Args:
            tag: Release tag name
            
        Returns:
            GitHubRelease object or None if not found
        """
        url = f"{self.base_url}/releases/tags/{tag}"
        data = self._make_request(url)
        return GitHubRelease(data) if data else None 