#!/usr/bin/env python3
"""
Test script for polling functionality
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

def create_polling_job():
    """Create a new polling job"""
    print("\n🚀 Creating polling job...")
    
    payload = {
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "interval": 30,  # Poll every 30 seconds
        "provider": "alpha_vantage"
    }
    
    response = requests.post(f"{BASE_URL}/prices/poll", json=payload)
    
    if response.status_code == 202:
        data = response.json()
        print(f"✅ Polling job created successfully!")
        print(f"   Job ID: {data['job_id']}")
        print(f"   Status: {data['status']}")
        print(f"   Config: {json.dumps(data['config'], indent=2)}")
        return data['job_id']
    else:
        print(f"❌ Error: {response.text}")
        return None

def check_job_status(job_id):
    """Check the status of a polling job"""
    print(f"\n🔍 Checking status of job {job_id}...")
    
    response = requests.get(f"{BASE_URL}/prices/poll/{job_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: {data['status']}")
        return data
    else:
        print(f"❌ Error: {response.text}")
        return None

def monitor_database():
    """Monitor database for new prices"""
    import subprocess
    
    print("\n📊 Monitoring database for new prices...")
    print("   (Press Ctrl+C to stop)\n")
    
    query = """
    SELECT 
        symbol, 
        COUNT(*) as price_count,
        MAX(created_at) as last_update
    FROM price_points 
    WHERE created_at > NOW() - INTERVAL '5 minutes'
    GROUP BY symbol 
    ORDER BY symbol;
    """
    
    try:
        while True:
            result = subprocess.run(
                f'docker exec market_data_postgres psql -U postgres -d market_data -c "{query}"',
                shell=True,
                capture_output=True,
                text=True
            )
            
            print("\033[H\033[J")  # Clear screen
            print("📊 Recent Price Updates (Last 5 minutes):")
            print("="*50)
            print(result.stdout)
            print("\nPolling job is running... (Ctrl+C to stop)")
            
            time.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\n✋ Monitoring stopped")

def stop_polling_job(job_id):
    """Stop a polling job"""
    print(f"\n🛑 Stopping polling job {job_id}...")
    
    response = requests.delete(f"{BASE_URL}/prices/poll/{job_id}")
    
    if response.status_code == 200:
        print(f"✅ {response.json()['message']}")
    else:
        print(f"❌ Error: {response.text}")

def main():
    print("🧪 Testing Polling Functionality")
    print("="*50)
    
    # Create a polling job
    job_id = create_polling_job()
    
    if not job_id:
        print("Failed to create polling job!")
        return
    
    # Check job status
    time.sleep(2)
    check_job_status(job_id)
    
    # Monitor database
    print("\n⏰ The polling job will fetch prices every 30 seconds")
    print("   Let's monitor the database to see new prices coming in...")
    
    input("\nPress Enter to start monitoring...")
    
    try:
        monitor_database()
    except KeyboardInterrupt:
        pass
    
    # Ask if user wants to stop the job
    stop = input("\n\nDo you want to stop the polling job? (y/n): ")
    if stop.lower() == 'y':
        stop_polling_job(job_id)
    else:
        print(f"\n💡 Job {job_id} is still running in the background!")
        print("   It will continue fetching prices until you restart the server.")

if __name__ == "__main__":
    main()