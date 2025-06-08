# Auditor Helper Updater System - Development Roadmap

## 📋 Project Overview

The Auditor Helper updater system provides automatic update checking and installation capabilities by integrating with GitHub releases. This document tracks the implementation progress and outlines the roadmap for completing the feature.

**Repository:** MrTimedying/auditor_helper  
**Current Version:** 0.16.8-beta  
**Target Platforms:** Windows, Linux, macOS  

---

## ✅ Phase 1: Core Infrastructure (COMPLETED)

### 1.1 Basic Architecture ✅
- [x] Created modular updater package structure
- [x] Implemented `VersionManager` for version parsing and comparison
- [x] Built `GitHubClient` for API communication
- [x] Developed `UpdateChecker` as main coordination logic
- [x] Created basic UI components (`UpdateDialog`, `UpdateCheckWidget`)
- [x] Integrated Updates tab into Options dialog

### 1.2 GitHub Integration ✅
- [x] GitHub API client with proper error handling
- [x] Release fetching with prerelease support
- [x] Platform-specific asset detection
- [x] Rate limiting and timeout handling
- [x] Repository configured: `MrTimedying/auditor_helper`

### 1.3 Version Management ✅
- [x] Semantic version parsing with `packaging` library
- [x] Version comparison logic
- [x] Beta/prerelease detection
- [x] Git tag parsing for various formats
- [x] Current version tracking (0.16.8-beta)

### 1.4 Basic UI ✅
- [x] Update check widget in Options dialog
- [x] Update available dialog with release notes
- [x] Manual update checking functionality
- [x] Current version display with platform info
- [x] Basic settings (auto-check, include beta)

---

## 🚧 Phase 2: Enhanced Functionality (IN PROGRESS)

### 2.1 Dependencies and Requirements
- [ ] **Add `packaging` library to requirements**
  - Create/update `requirements.txt` with `packaging>=21.0`
  - Test version parsing functionality
  - Handle import errors gracefully

### 2.2 Settings Persistence
- [ ] **Create `UpdateSettings` class**
  - Extend existing settings system or create new one
  - Store: auto-check enabled, check frequency, include prereleases
  - Store: last check timestamp, update channel preference
  - Integration with `QtCore.QSettings`

- [ ] **Integrate settings with UI**
  - Load saved settings on dialog open
  - Save settings when changed
  - Persist checkbox states between sessions

### 2.3 Auto-Check Scheduling
- [ ] **Implement background checking**
  - Create `UpdateScheduler` class
  - Use `QTimer` for periodic checks
  - Configurable intervals (daily, weekly, monthly)
  - Startup check option

- [ ] **Background check logic**
  - Non-blocking update checks
  - Silent checks with notification only if update found
  - Respect user preferences for frequency
  - Handle network failures gracefully

### 2.4 Enhanced Download Management
- [ ] **Create `DownloadManager` class**
  - Progress tracking with `QProgressDialog`
  - Resume capability for interrupted downloads
  - Checksum verification (if provided by GitHub)
  - Temporary file handling

- [ ] **Download UI improvements**
  - Progress bar during download
  - Cancel download option
  - Download location selection
  - Error handling and retry logic

---

## 🎯 Phase 3: Installation System (PLANNED)

### 3.1 Update Installation
- [ ] **Create `UpdateInstaller` class**
  - Platform-specific installation logic
  - Backup current version before update
  - Safe file replacement strategies
  - Rollback capability on failure

- [ ] **Windows Installation**
  - Handle `.exe` file replacement
  - Manage file locks (running application)
  - UAC elevation if required
  - Registry updates if needed

- [ ] **Linux Installation**
  - Handle `.AppImage` or package files
  - File permissions management
  - Desktop integration updates
  - Symlink handling

- [ ] **macOS Installation**
  - Handle `.dmg` or `.app` bundles
  - Code signing verification
  - Application bundle replacement
  - Gatekeeper compatibility

### 3.2 Restart and Finalization
- [ ] **Application restart logic**
  - Graceful application shutdown
  - Restart with same parameters
  - State preservation across restart
  - Update completion verification

- [ ] **Post-update tasks**
  - Cleanup temporary files
  - Update version tracking
  - Show "what's new" dialog
  - Log update success/failure

---

## 🔧 Phase 4: Polish and Security (PLANNED)

### 4.1 Security Enhancements
- [ ] **Download verification**
  - SHA256 checksum validation
  - Digital signature verification (if available)
  - HTTPS enforcement
  - Malware scanning integration (optional)

- [ ] **Update authenticity**
  - Verify releases are from official repository
  - Check release author/publisher
  - Validate asset integrity
  - Prevent downgrade attacks

### 4.2 Error Handling and Logging
- [ ] **Comprehensive error handling**
  - Network connectivity issues
  - GitHub API rate limiting
  - Download failures and corruption
  - Installation permission errors

- [ ] **Logging system**
  - Update check logs
  - Download progress logs
  - Installation success/failure logs
  - Error reporting for debugging

### 4.3 User Experience Improvements
- [ ] **Notification system**
  - System tray notifications
  - Toast notifications for updates
  - Update reminder scheduling
  - Quiet mode for minimal interruption

- [ ] **Advanced settings**
  - Proxy configuration support
  - Custom GitHub token for private repos
  - Update channel management
  - Bandwidth limiting for downloads

---

## 🧪 Phase 5: Testing and Deployment (PLANNED)

### 5.1 Testing Framework
- [ ] **Unit tests**
  - Version comparison logic
  - GitHub API client functionality
  - Download manager reliability
  - Installation process validation

- [ ] **Integration tests**
  - End-to-end update process
  - Cross-platform compatibility
  - Network failure scenarios
  - UI interaction testing

### 5.2 Documentation
- [ ] **User documentation**
  - Update process explanation
  - Troubleshooting guide
  - Settings configuration help
  - FAQ for common issues

- [ ] **Developer documentation**
  - API documentation
  - Architecture overview
  - Extension points for customization
  - Deployment considerations

---

## 📊 Current Status Summary

| Component | Status | Priority | Estimated Effort |
|-----------|--------|----------|------------------|
| Core Infrastructure | ✅ Complete | - | - |
| Dependencies Setup | 🔄 Pending | High | 1 day |
| Settings Persistence | 🔄 Pending | High | 2 days |
| Auto-Check Scheduling | 🔄 Pending | Medium | 3 days |
| Download Manager | 🔄 Pending | Medium | 4 days |
| Installation System | 📋 Planned | High | 1 week |
| Security Features | 📋 Planned | Medium | 3 days |
| Testing & Polish | 📋 Planned | Low | 1 week |

---

## 🎯 Immediate Next Steps (Priority Order)

1. **Add packaging dependency** - Required for version parsing
2. **Implement settings persistence** - Store user preferences
3. **Create auto-check scheduling** - Background update checking
4. **Enhance download management** - Progress tracking and reliability
5. **Build installation system** - Actual update installation
6. **Add security features** - Verification and validation
7. **Comprehensive testing** - Ensure reliability across platforms

---

## 📝 Notes and Considerations

### Technical Decisions
- Using `packaging` library for robust version parsing
- `QtCore.QSettings` for cross-platform settings storage
- `QTimer` for non-blocking background operations
- Platform detection via `platform.system()`

### Potential Challenges
- File locking during application updates
- Platform-specific installation procedures
- Network connectivity and proxy handling
- User permission management for file operations

### Future Enhancements
- Delta updates for smaller downloads
- Multiple update channels (stable, beta, nightly)
- Plugin system for custom update sources
- Integration with CI/CD for automated releases

---

**Last Updated:** 2024-12-19  
**Next Review:** After Phase 2 completion 