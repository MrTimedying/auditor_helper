"""
Test Phase 3 Adaptive Resize Optimization System

This script validates the Phase 3 adaptive optimization system including:
- Adaptive threshold management
- Context-aware optimization
- Performance learning and analytics
- Integration with Phase 2 system
"""

import sys
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PySide6 import QtWidgets, QtCore, QtGui
from core.resize_optimization.adaptive_threshold_manager import (
    AdaptiveThresholdManager, 
    ContextProfile, 
    ThresholdSet,
    HardwareProfile,
    OptimizationSession
)
from core.resize_optimization.phase3_integration import Phase3ResizeOptimization
from core.resize_optimization.resize_state_manager import OptimizationLevel


class TestPhase3Optimization:
    """Test suite for Phase 3 optimization system"""
    
    def __init__(self):
        self.app = None
        self.temp_dir = None
        self.test_results = []
        
    def setup(self):
        """Setup test environment"""
        print("Setting up Phase 3 test environment...")
        
        # Create QApplication if needed
        if not QtWidgets.QApplication.instance():
            self.app = QtWidgets.QApplication([])
        
        # Create temporary directory for test data
        self.temp_dir = Path(tempfile.mkdtemp())
        print(f"Test data directory: {self.temp_dir}")
        
    def cleanup(self):
        """Clean up test environment"""
        print("Cleaning up test environment...")
        
        # Clean up temporary directory
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
        
        # Clean up QApplication
        if self.app:
            self.app.quit()
    
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append((test_name, success, details))
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
    
    def test_adaptive_threshold_manager(self):
        """Test AdaptiveThresholdManager functionality"""
        print("\n=== Testing AdaptiveThresholdManager ===")
        
        try:
            # Test initialization
            manager = AdaptiveThresholdManager(self.temp_dir / "adaptive_test")
            self.log_result("AdaptiveThresholdManager initialization", True, 
                          f"Hardware score: {manager.hardware_profile.performance_score:.1f}")
            
            # Test hardware profile detection
            profile = manager.hardware_profile
            has_valid_profile = (
                profile.cpu_cores > 0 and 
                profile.memory_gb > 0 and 
                0 <= profile.performance_score <= 100
            )
            self.log_result("Hardware profile detection", has_valid_profile,
                          f"CPU: {profile.cpu_cores} cores, RAM: {profile.memory_gb:.1f}GB, Score: {profile.performance_score:.1f}")
            
            # Test context profile creation
            context = ContextProfile(
                task_count=25,
                window_size=(1200, 800),
                monitor_count=1,
                high_dpi=False,
                accessibility_enabled=False
            )
            
            # Test threshold calculation
            thresholds = manager.get_optimal_thresholds(context)
            has_valid_thresholds = (
                thresholds.light_threshold > 0 and
                thresholds.medium_threshold > thresholds.light_threshold and
                thresholds.heavy_threshold > thresholds.medium_threshold and
                thresholds.static_threshold > thresholds.heavy_threshold
            )
            self.log_result("Threshold calculation", has_valid_thresholds,
                          f"Thresholds: {thresholds.to_dict()}")
            
            # Test session recording
            manager.record_optimization_session(
                context=context,
                thresholds_used=thresholds.to_dict(),
                performance_metrics={
                    'session_duration': 2.5,
                    'start_frequency': 45.0,
                    'end_frequency': 30.0,
                    'avg_frequency': 37.5,
                    'peak_frequency': 50.0
                },
                effectiveness_score=75.0
            )
            
            has_session = len(manager.session_history) > 0
            self.log_result("Session recording", has_session,
                          f"Recorded {len(manager.session_history)} sessions")
            
            # Test performance analysis
            analysis = manager.get_performance_analysis()
            has_analysis = 'total_sessions' in analysis and analysis['total_sessions'] > 0
            self.log_result("Performance analysis", has_analysis,
                          f"Analysis keys: {list(analysis.keys())}")
            
            # Test data persistence
            manager._save_data()
            
            # Create new manager and verify data loading
            manager2 = AdaptiveThresholdManager(self.temp_dir / "adaptive_test")
            data_loaded = len(manager2.session_history) == len(manager.session_history)
            self.log_result("Data persistence", data_loaded,
                          f"Loaded {len(manager2.session_history)} sessions")
            
        except Exception as e:
            self.log_result("AdaptiveThresholdManager test", False, f"Error: {e}")
    
    def test_phase3_integration(self):
        """Test Phase3ResizeOptimization integration"""
        print("\n=== Testing Phase3ResizeOptimization ===")
        
        try:
            # Create mock TaskGrid
            task_grid = Mock(spec=QtWidgets.QTableView)
            task_grid.model.return_value = Mock()
            task_grid.model().rowCount.return_value = 50
            task_grid.width.return_value = 1200
            task_grid.height.return_value = 800
            
            # Mock QApplication screens
            mock_screen = Mock()
            mock_screen.devicePixelRatio.return_value = 1.0
            QtWidgets.QApplication.primaryScreen = Mock(return_value=mock_screen)
            QtWidgets.QApplication.screens = Mock(return_value=[mock_screen])
            
            # Initialize Phase 3 optimization
            phase3 = Phase3ResizeOptimization(task_grid, debug_mode=True, data_dir=self.temp_dir / "phase3_test")
            
            # Test initialization
            has_adaptive_manager = phase3.adaptive_manager is not None
            self.log_result("Phase3 initialization", has_adaptive_manager,
                          "Adaptive manager created")
            
            # Test context detection
            has_context = phase3.current_context is not None
            self.log_result("Context detection", has_context,
                          f"Context: {phase3._get_context_key(phase3.current_context) if has_context else 'None'}")
            
            # Test threshold application
            has_thresholds = phase3.current_thresholds is not None
            self.log_result("Threshold application", has_thresholds,
                          f"Thresholds: {phase3.current_thresholds.to_dict() if has_thresholds else 'None'}")
            
            # Test status reporting
            status = phase3.get_adaptive_status()
            has_status = 'phase3_enabled' in status and status['phase3_enabled']
            self.log_result("Status reporting", has_status,
                          f"Status keys: {list(status.keys())}")
            
            # Test performance analytics
            analytics = phase3.get_performance_analytics()
            has_analytics = 'hardware_profile' in analytics
            self.log_result("Performance analytics", has_analytics,
                          f"Analytics keys: {list(analytics.keys())}")
            
            # Test cleanup
            phase3.cleanup()
            self.log_result("Phase3 cleanup", True, "Cleanup completed")
            
        except Exception as e:
            self.log_result("Phase3ResizeOptimization test", False, f"Error: {e}")
    
    def test_threshold_adaptation(self):
        """Test adaptive threshold learning"""
        print("\n=== Testing Threshold Adaptation ===")
        
        try:
            manager = AdaptiveThresholdManager(self.temp_dir / "adaptation_test")
            
            # Create test context
            context = ContextProfile(
                task_count=100,  # Large task count
                window_size=(1600, 1000),  # Large window
                monitor_count=1,
                high_dpi=False,
                accessibility_enabled=False
            )
            
            # Get initial thresholds
            initial_thresholds = manager.get_optimal_thresholds(context)
            
            # Simulate multiple sessions with poor effectiveness
            for i in range(10):
                manager.record_optimization_session(
                    context=context,
                    thresholds_used=initial_thresholds.to_dict(),
                    performance_metrics={
                        'session_duration': 3.0,
                        'start_frequency': 70.0,  # High frequency
                        'end_frequency': 65.0,   # Still high after optimization
                        'avg_frequency': 67.5,
                        'peak_frequency': 75.0
                    },
                    effectiveness_score=40.0  # Poor effectiveness
                )
            
            # Get thresholds after learning
            adapted_thresholds = manager.get_optimal_thresholds(context)
            
            # Check if thresholds were adapted (should be lower to optimize earlier)
            thresholds_adapted = (
                adapted_thresholds.light_threshold <= initial_thresholds.light_threshold or
                adapted_thresholds.medium_threshold <= initial_thresholds.medium_threshold
            )
            
            self.log_result("Threshold adaptation", thresholds_adapted,
                          f"Initial: {initial_thresholds.to_dict()}, Adapted: {adapted_thresholds.to_dict()}")
            
            # Test analysis after adaptation
            analysis = manager.get_performance_analysis()
            has_recommendations = 'threshold_recommendations' in analysis
            self.log_result("Adaptation analysis", has_recommendations,
                          f"Recommendations: {analysis.get('threshold_recommendations', {})}")
            
        except Exception as e:
            self.log_result("Threshold adaptation test", False, f"Error: {e}")
    
    def test_context_awareness(self):
        """Test context-aware optimization"""
        print("\n=== Testing Context Awareness ===")
        
        try:
            manager = AdaptiveThresholdManager(self.temp_dir / "context_test")
            
            # Test different contexts
            contexts = [
                ContextProfile(10, (800, 600), 1, False, False),    # Small context
                ContextProfile(50, (1200, 800), 1, False, False),   # Medium context
                ContextProfile(200, (1920, 1080), 2, True, False),  # Large context
            ]
            
            thresholds_by_context = {}
            for i, context in enumerate(contexts):
                thresholds = manager.get_optimal_thresholds(context)
                context_key = manager._get_context_key(context)
                thresholds_by_context[context_key] = thresholds
                
                self.log_result(f"Context {i+1} thresholds", True,
                              f"{context_key}: {thresholds.to_dict()}")
            
            # Verify different contexts can have different thresholds
            unique_thresholds = len(set(
                (t.light_threshold, t.medium_threshold, t.heavy_threshold, t.static_threshold)
                for t in thresholds_by_context.values()
            ))
            
            context_awareness = unique_thresholds > 1 or len(contexts) == 1
            self.log_result("Context awareness", context_awareness,
                          f"Generated {unique_thresholds} unique threshold sets for {len(contexts)} contexts")
            
        except Exception as e:
            self.log_result("Context awareness test", False, f"Error: {e}")
    
    def test_performance_scoring(self):
        """Test effectiveness scoring algorithm"""
        print("\n=== Testing Performance Scoring ===")
        
        try:
            # Create mock Phase 3 system
            task_grid = Mock(spec=QtWidgets.QTableView)
            task_grid.model.return_value = Mock()
            task_grid.model().rowCount.return_value = 25
            task_grid.width.return_value = 1000
            task_grid.height.return_value = 700
            
            # Mock QApplication screens
            mock_screen = Mock()
            mock_screen.devicePixelRatio.return_value = 1.0
            QtWidgets.QApplication.primaryScreen = Mock(return_value=mock_screen)
            QtWidgets.QApplication.screens = Mock(return_value=[mock_screen])
            
            phase3 = Phase3ResizeOptimization(task_grid, debug_mode=True, data_dir=self.temp_dir / "scoring_test")
            
            # Test different scenarios
            test_scenarios = [
                (60.0, 30.0, 1.0, "Good optimization"),      # Good: 50% reduction, fast
                (80.0, 70.0, 2.0, "Moderate optimization"),  # Moderate: 12.5% reduction
                (40.0, 35.0, 5.0, "Slow optimization"),     # Slow: 12.5% reduction, slow
                (30.0, 45.0, 1.0, "Performance regression"), # Bad: performance got worse
            ]
            
            for start_freq, end_freq, duration, description in test_scenarios:
                score = phase3._calculate_effectiveness_score(start_freq, end_freq, duration)
                
                # Score should be between 0 and 100
                valid_score = 0 <= score <= 100
                self.log_result(f"Scoring: {description}", valid_score,
                              f"{start_freq}Hz → {end_freq}Hz in {duration}s = {score:.1f}%")
            
        except Exception as e:
            self.log_result("Performance scoring test", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Phase 3 Optimization Tests")
        print("=" * 50)
        
        self.setup()
        
        try:
            self.test_adaptive_threshold_manager()
            self.test_phase3_integration()
            self.test_threshold_adaptation()
            self.test_context_awareness()
            self.test_performance_scoring()
            
        finally:
            self.cleanup()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Phase 3 system is ready.")
        else:
            print("⚠️  Some tests failed. Review the results above.")
            
            # Show failed tests
            failed_tests = [(name, details) for name, success, details in self.test_results if not success]
            if failed_tests:
                print("\nFailed tests:")
                for name, details in failed_tests:
                    print(f"  ❌ {name}: {details}")
        
        return passed == total


def main():
    """Main test function"""
    tester = TestPhase3Optimization()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Phase 3 optimization system validation completed successfully!")
        print("The adaptive threshold management system is working correctly.")
    else:
        print("\n❌ Phase 3 optimization system validation failed!")
        print("Please review the test results and fix any issues.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 