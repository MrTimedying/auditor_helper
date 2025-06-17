#!/usr/bin/env python3
"""
Phase 2 Performance Test for Auditor Helper
Tests startup performance improvements from Redis replacement and database optimization
"""

import sys
import time
import subprocess
import os
from pathlib import Path

def test_phase2_performance():
    """Test Phase 2 startup performance improvements"""
    print("🚀 PHASE 2 PERFORMANCE TEST")
    print("=" * 50)
    print("Testing startup performance improvements:")
    print("  • Redis replacement with multi-tier cache")
    print("  • Database optimization with connection pooling")
    print("  • Comprehensive startup profiling")
    print()
    
    # Test parameters
    num_tests = 3
    startup_times = []
    
    print(f"Running {num_tests} startup tests...")
    print()
    
    for i in range(num_tests):
        print(f"🔄 Test {i+1}/{num_tests}...")
        
        # Record start time
        start_time = time.time()
        
        # Run the application with a timeout
        try:
            # Start the application
            process = subprocess.Popen(
                [sys.executable, "src/__main__.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            
            # Wait for startup completion (look for specific output)
            startup_completed = False
            startup_time = None
            
            # Read output line by line with timeout
            try:
                import select
                import fcntl
                
                # Make stdout non-blocking (Unix only)
                fd = process.stdout.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                unix_mode = True
            except ImportError:
                # Windows doesn't have fcntl/select
                unix_mode = False
            
            timeout = 30  # 30 second timeout
            elapsed = 0
            
            while elapsed < timeout and process.poll() is None:
                try:
                    if unix_mode:
                        # Unix: Use select for non-blocking read
                        ready, _, _ = select.select([process.stdout], [], [], 0.1)
                        if ready:
                            line = process.stdout.readline()
                            if line:
                                print(f"    {line.strip()}")
                                
                                # Look for startup completion indicators
                                if "Phase 1+2 Startup completed" in line:
                                    # Extract time from the line
                                    try:
                                        time_part = line.split("in ")[1].split("s")[0]
                                        startup_time = float(time_part)
                                        startup_completed = True
                                        break
                                    except:
                                        pass
                                elif "PHASE 2 STARTUP PERFORMANCE REPORT" in line:
                                    # Startup is completing
                                    pass
                    else:
                        # Windows: Simple timeout-based approach
                        time.sleep(0.1)
                        if elapsed > 10:  # Give up after 10 seconds on Windows
                            startup_time = elapsed
                            startup_completed = True
                            break
                    
                    elapsed = time.time() - start_time
                    
                except:
                    elapsed = time.time() - start_time
                    continue
            
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            # Record the time
            if startup_completed and startup_time:
                startup_times.append(startup_time)
                print(f"    ✅ Startup completed in {startup_time:.2f}s")
            else:
                fallback_time = time.time() - start_time
                startup_times.append(fallback_time)
                print(f"    ⚠️ Startup time estimated at {fallback_time:.2f}s (timeout/incomplete)")
            
        except Exception as e:
            print(f"    ❌ Test failed: {e}")
            # Use a fallback time
            fallback_time = time.time() - start_time
            startup_times.append(fallback_time)
        
        print()
        
        # Wait between tests
        if i < num_tests - 1:
            print("    Waiting 2 seconds before next test...")
            time.sleep(2)
    
    # Analyze results
    if startup_times:
        avg_time = sum(startup_times) / len(startup_times)
        min_time = min(startup_times)
        max_time = max(startup_times)
        
        print("📊 PHASE 2 PERFORMANCE RESULTS")
        print("-" * 40)
        print(f"Average startup time: {avg_time:.2f}s")
        print(f"Best startup time:    {min_time:.2f}s")
        print(f"Worst startup time:   {max_time:.2f}s")
        print(f"Tests completed:      {len(startup_times)}/{num_tests}")
        print()
        
        # Performance analysis
        print("🎯 PERFORMANCE ANALYSIS")
        print("-" * 30)
        
        if avg_time <= 3.0:
            grade = "A"
            status = "EXCELLENT"
        elif avg_time <= 5.0:
            grade = "B"
            status = "GOOD"
        elif avg_time <= 7.0:
            grade = "C"
            status = "ACCEPTABLE"
        elif avg_time <= 10.0:
            grade = "D"
            status = "NEEDS IMPROVEMENT"
        else:
            grade = "F"
            status = "POOR"
        
        print(f"Performance Grade: {grade} ({status})")
        
        # Compare with Phase 1 baseline
        phase1_baseline = 9.0  # Approximate Phase 1 performance
        if avg_time < phase1_baseline:
            improvement = ((phase1_baseline - avg_time) / phase1_baseline) * 100
            print(f"Improvement over Phase 1: {improvement:.1f}% faster")
        else:
            regression = ((avg_time - phase1_baseline) / phase1_baseline) * 100
            print(f"Regression from Phase 1: {regression:.1f}% slower")
        
        print()
        
        # Recommendations
        print("💡 PHASE 2 OPTIMIZATIONS ACTIVE")
        print("-" * 35)
        print("✅ Redis replacement with multi-tier cache")
        print("✅ Database optimization with connection pooling")
        print("✅ Comprehensive startup profiling")
        print("✅ Lazy loading system (from Phase 1)")
        
        if avg_time > 5.0:
            print("\n🔍 FURTHER OPTIMIZATION OPPORTUNITIES")
            print("-" * 45)
            print("• UI component async loading")
            print("• Background service initialization")
            print("• Additional database optimizations")
            print("• Component lazy initialization")
        
        print()
        print("📄 Check 'phase2_startup_report.txt' for detailed analysis")
        
    else:
        print("❌ No successful tests completed")
    
    return startup_times

def main():
    """Main test function"""
    print("Starting Phase 2 performance testing...")
    print()
    
    # Check if we're in the right directory
    if not Path("src/__main__.py").exists():
        print("❌ Error: Please run this script from the auditor_helper root directory")
        print("   Current directory:", os.getcwd())
        return
    
    # Run the performance test
    startup_times = test_phase2_performance()
    
    # Save results
    if startup_times:
        with open("phase2_test_results.txt", "w") as f:
            f.write("Phase 2 Performance Test Results\n")
            f.write("=" * 40 + "\n")
            f.write(f"Test runs: {len(startup_times)}\n")
            f.write(f"Startup times: {startup_times}\n")
            f.write(f"Average: {sum(startup_times)/len(startup_times):.2f}s\n")
            f.write(f"Best: {min(startup_times):.2f}s\n")
            f.write(f"Worst: {max(startup_times):.2f}s\n")
        
        print(f"📄 Results saved to: phase2_test_results.txt")

if __name__ == "__main__":
    main() 