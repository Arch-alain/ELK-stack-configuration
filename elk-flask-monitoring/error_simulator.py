#!/usr/bin/env python3
"""
Error Simulation Script for Flask App
This script simulates different types of database errors to test alerting
"""

import requests
import json
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor
import sys

FLASK_URL = "http://localhost:5000"

class ErrorSimulator:
    def __init__(self, base_url=FLASK_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_connection(self):
        """Test if Flask app is running"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def simulate_pool_exhaustion(self):
        """Enable connection pool exhaustion simulation"""
        try:
            response = self.session.post(f"{self.base_url}/simulate-pool-exhaustion")
            print(f"✓ Pool exhaustion simulation enabled: {response.status_code}")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to enable pool exhaustion: {e}")
            return False
    
    def reset_pool(self):
        """Reset connection pool simulation"""
        try:
            response = self.session.post(f"{self.base_url}/reset-pool")
            print(f"✓ Pool simulation reset: {response.status_code}")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to reset pool: {e}")
            return False
    
    def stress_test_database(self):
        """Run stress test to trigger connection errors"""
        try:
            response = self.session.post(f"{self.base_url}/stress-test")
            print(f"✓ Stress test completed: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Error count: {data.get('error_count', 0)}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"✗ Stress test failed: {e}")
            return False
    
    def add_book(self, title, author):
        """Add a book (may fail with database errors)"""
        try:
            data = {"title": title, "author": author}
            response = self.session.post(f"{self.base_url}/books", json=data)
            return response.status_code in [201, 503, 500]
        except requests.exceptions.RequestException:
            return False
    
    def get_book(self, book_id):
        """Get a book (may fail with database errors)"""
        try:
            response = self.session.get(f"{self.base_url}/books/{book_id}")
            return response.status_code in [200, 404, 503, 500]
        except requests.exceptions.RequestException:
            return False
    
    def list_books(self):
        """List books (may fail with database errors)"""
        try:
            response = self.session.get(f"{self.base_url}/books")
            return response.status_code in [200, 503, 500]
        except requests.exceptions.RequestException:
            return False
    
    def health_check(self):
        """Check service health"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

def scenario_1_connection_pool_exhaustion(simulator):
    """
    Scenario 1: Database Connection Pool Exhaustion
    This simulates what happens when too many concurrent requests exhaust the connection pool
    """
    print("\n" + "="*60)
    print("SCENARIO 1: Database Connection Pool Exhaustion")
    print("="*60)
    
    # Enable pool exhaustion simulation
    if not simulator.simulate_pool_exhaustion():
        print("Failed to enable simulation")
        return
    
    # Generate multiple concurrent requests to trigger connection errors
    def make_concurrent_requests():
        operations = [
            lambda: simulator.add_book(f"Book_{random.randint(1000, 9999)}", f"Author_{random.randint(100, 999)}"),
            lambda: simulator.get_book(random.randint(1, 10)),
            lambda: simulator.list_books(),
        ]
        
        for _ in range(5):  # 5 operations per thread
            operation = random.choice(operations)
            operation()
            time.sleep(random.uniform(0.1, 0.3))
    
    print("Generating concurrent database requests...")
    
    # Use ThreadPoolExecutor to create concurrent requests
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(make_concurrent_requests) for _ in range(8)]
        
        # Wait for all threads to complete
        for future in futures:
            future.result()
    
    print("✓ Connection pool exhaustion scenario completed")
    print("Expected: Multiple DATABASE_CONNECTION_ERROR entries in logs")
    print("This should trigger the 'High Database Connection Errors' alert")
    
    # Reset after scenario
    time.sleep(2)
    simulator.reset_pool()

def scenario_2_sustained_database_errors(simulator):
    """
    Scenario 2: Sustained Database Operation Errors
    This simulates ongoing database issues affecting multiple operations
    """
    print("\n" + "="*60)
    print("SCENARIO 2: Sustained Database Operation Errors")
    print("="*60)
    
    # Enable pool exhaustion
    simulator.simulate_pool_exhaustion()
    
    print("Generating sustained database errors over 5 minutes...")
    
    start_time = time.time()
    error_count = 0
    
    while time.time() - start_time < 300:  # Run for 5 minutes
        # Mix of different operations
        operations = [
            ("add_book", lambda: simulator.add_book(f"TestBook_{random.randint(1000, 9999)}", "Test Author")),
            ("get_book", lambda: simulator.get_book(random.randint(1, 100))),
            ("list_books", lambda: simulator.list_books()),
            ("health_check", lambda: simulator.health_check()),
        ]
        
        op_name, operation = random.choice(operations)
        try:
            operation()
            error_count += 1
        except:
            pass
        
        time.sleep(random.uniform(2, 8))  # Random interval between requests
        
        # Print progress every minute
        elapsed = time.time() - start_time
        if int(elapsed) % 60 == 0 and int(elapsed) > 0:
            print(f"  Progress: {int(elapsed/60)} minutes elapsed, ~{error_count} operations attempted")
    
    print("✓ Sustained error scenario completed")
    print("Expected: Multiple DATABASE_ERROR entries spread over time")
    print("This should trigger the 'Multiple Database Operation Errors' alert")
    
    # Reset after scenario
    simulator.reset_pool()

def scenario_3_error_rate_spike(simulator):
    """
    Scenario 3: Sudden Error Rate Spike
    This simulates a sudden burst of errors that would indicate a system failure
    """
    print("\n" + "="*60)
    print("SCENARIO 3: Sudden Error Rate Spike")
    print("="*60)
    
    # Enable pool exhaustion for maximum error generation
    simulator.simulate_pool_exhaustion()
    
    print("Generating rapid burst of errors...")
    
    def rapid_fire_requests():
        """Generate rapid requests to create error spike"""
        operations = [
            lambda: simulator.add_book(f"RapidBook_{random.randint(10000, 99999)}", "Rapid Author"),
            lambda: simulator.get_book(random.randint(1, 1000)),
            lambda: simulator.list_books(),
            lambda: simulator.stress_test_database(),
        ]
        
        for _ in range(10):  # 10 rapid operations
            operation = random.choice(operations)
            operation()
            time.sleep(0.1)  # Very short delay
    
    # Create multiple threads for rapid-fire requests
    threads = []
    for i in range(6):  # 6 concurrent threads
        thread = threading.Thread(target=rapid_fire_requests)
        threads.append(thread)
        thread.start()
        time.sleep(0.2)  # Stagger thread starts slightly
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("✓ Error rate spike scenario completed")
    print("Expected: High concentration of errors in short time period")
    print("This should trigger the 'Error Rate Spike Detection' alert")
    
    # Reset after scenario
    time.sleep(2)
    simulator.reset_pool()

def scenario_4_service_degradation(simulator):
    """
    Scenario 4: Service Health Degradation
    This simulates gradual service degradation leading to health check failures
    """
    print("\n" + "="*60)
    print("SCENARIO 4: Service Health Degradation")
    print("="*60)
    
    print("Simulating gradual service degradation...")
    
    # First, cause some database stress
    simulator.simulate_pool_exhaustion()
    
    # Perform multiple health checks that will fail
    for i in range(10):
        print(f"  Health check attempt {i+1}/10")
        simulator.health_check()
        time.sleep(random.uniform(5, 15))  # Space out health checks
    
    print("✓ Service degradation scenario completed")
    print("Expected: Multiple 'Health check failed' log entries")
    print("This should trigger the 'Service Health Check Failures' alert")
    
    # Reset after scenario
    simulator.reset_pool()

def interactive_menu(simulator):
    """Interactive menu for manual testing"""
    while True:
        print("\n" + "="*50)
        print("FLASK APP ERROR SIMULATION MENU")
        print("="*50)
        print("1. Test Connection")
        print("2. Run Scenario 1: Connection Pool Exhaustion")
        print("3. Run Scenario 2: Sustained Database Errors (5 min)")
        print("4. Run Scenario 3: Error Rate Spike")
        print("5. Run Scenario 4: Service Health Degradation")
        print("6. Manual Operations")
        print("7. View Current Status")
        print("8. Reset Pool Simulation")
        print("0. Exit")
        print("-"*50)
        
        choice = input("Select option (0-8): ").strip()
        
        if choice == "0":
            print("Exiting...")
            break
        elif choice == "1":
            if simulator.test_connection():
                print("✓ Flask app is running and accessible")
            else:
                print("✗ Flask app is not accessible")
        elif choice == "2":
            scenario_1_connection_pool_exhaustion(simulator)
        elif choice == "3":
            print("⚠️  This will run for 5 minutes. Continue? (y/N)")
            if input().lower().startswith('y'):
                scenario_2_sustained_database_errors(simulator)
        elif choice == "4":
            scenario_3_error_rate_spike(simulator)
        elif choice == "5":
            scenario_4_service_degradation(simulator)
        elif choice == "6":
            manual_operations_menu(simulator)
        elif choice == "7":
            view_status(simulator)
        elif choice == "8":
            simulator.reset_pool()
        else:
            print("Invalid option. Please try again.")

def manual_operations_menu(simulator):
    """Manual operations submenu"""
    while True:
        print("\n" + "-"*40)
        print("MANUAL OPERATIONS")
        print("-"*40)
        print("1. Add Book")
        print("2. Get Book")
        print("3. List Books")
        print("4. Health Check")
        print("5. Stress Test")
        print("6. Enable Pool Exhaustion")
        print("7. Disable Pool Exhaustion")
        print("0. Back to Main Menu")
        
        choice = input("Select operation (0-7): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            title = input("Book title: ") or f"TestBook_{random.randint(1000, 9999)}"
            author = input("Author name: ") or f"TestAuthor_{random.randint(100, 999)}"
            if simulator.add_book(title, author):
                print("✓ Add book operation completed")
            else:
                print("✗ Add book operation failed")
        elif choice == "2":
            book_id = input("Book ID (or press enter for random): ").strip()
            if not book_id:
                book_id = random.randint(1, 100)
            if simulator.get_book(book_id):
                print("✓ Get book operation completed")
            else:
                print("✗ Get book operation failed")
        elif choice == "3":
            if simulator.list_books():
                print("✓ List books operation completed")
            else:
                print("✗ List books operation failed")
        elif choice == "4":
            if simulator.health_check():
                print("✓ Health check passed")
            else:
                print("✗ Health check failed")
        elif choice == "5":
            if simulator.stress_test_database():
                print("✓ Stress test completed")
            else:
                print("✗ Stress test failed")
        elif choice == "6":
            if simulator.simulate_pool_exhaustion():
                print("✓ Pool exhaustion enabled")
            else:
                print("✗ Failed to enable pool exhaustion")
        elif choice == "7":
            if simulator.reset_pool():
                print("✓ Pool exhaustion disabled")
            else:
                print("✗ Failed to disable pool exhaustion")
        else:
            print("Invalid option. Please try again.")

def view_status(simulator):
    """View current application status"""
    print("\n" + "-"*40)
    print("CURRENT STATUS")
    print("-"*40)
    
    try:
        response = simulator.session.get(f"{simulator.base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"Service Status: ✓ Running")
            print(f"Pool Exhausted: {'Yes' if data.get('pool_exhausted') else 'No'}")
            print(f"Error Count: {data.get('error_count', 0)}")
        else:
            print(f"Service Status: ✗ Error (HTTP {response.status_code})")
    except Exception as e:
        print(f"Service Status: ✗ Not accessible ({e})")
    
    # Health check
    if simulator.health_check():
        print("Health Check: ✓ Healthy")
    else:
        print("Health Check: ✗ Unhealthy")

def run_all_scenarios(simulator):
    """Run all scenarios in sequence for comprehensive testing"""
    print("\n" + "="*60)
    print("RUNNING ALL ERROR SIMULATION SCENARIOS")
    print("="*60)
    print("This will take approximately 10-15 minutes to complete")
    print("Press Ctrl+C to cancel")
    
    try:
        input("Press Enter to continue or Ctrl+C to cancel...")
        
        # Run scenarios in sequence with delays between them
        scenario_1_connection_pool_exhaustion(simulator)
        time.sleep(30)  # 30 second break
        
        scenario_3_error_rate_spike(simulator)
        time.sleep(30)  # 30 second break
        
        scenario_4_service_degradation(simulator)
        time.sleep(30)  # 30 second break
        
        print("\n⚠️  Starting 5-minute sustained error scenario...")
        scenario_2_sustained_database_errors(simulator)
        
        print("\n" + "="*60)
        print("ALL SCENARIOS COMPLETED!")
        print("="*60)
        print("Check Kibana for alerts and dashboard updates")
        
    except KeyboardInterrupt:
        print("\n\nScenarios cancelled by user")
        simulator.reset_pool()

def main():
    """Main function"""
    print("Flask App Error Simulation Tool")
    print("This tool generates various database errors to test Kibana alerting")
    
    simulator = ErrorSimulator()
    
    # Test connection first
    if not simulator.test_connection():
        print("✗ Cannot connect to Flask app at http://localhost:5000")
        print("Make sure the Flask app is running with docker-compose up")
        sys.exit(1)
    
    print("✓ Connected to Flask app successfully")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            run_all_scenarios(simulator)
        elif sys.argv[1] == "--scenario1":
            scenario_1_connection_pool_exhaustion(simulator)
        elif sys.argv[1] == "--scenario2":
            scenario_2_sustained_database_errors(simulator)
        elif sys.argv[1] == "--scenario3":
            scenario_3_error_rate_spike(simulator)
        elif sys.argv[1] == "--scenario4":
            scenario_4_service_degradation(simulator)
        else:
            print("Usage: python error_simulation.py [--all|--scenario1|--scenario2|--scenario3|--scenario4]")
    else:
        interactive_menu(simulator)

if __name__ == "__main__":
    main()