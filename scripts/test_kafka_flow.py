#!/usr/bin/env python3
"""
Test script to verify Kafka flow is working
"""
import requests
import time
import subprocess

BASE_URL = "http://localhost:8000/api/v1"

def fetch_prices(symbol="AAPL", count=5):
    """Fetch multiple prices to trigger moving average calculation"""
    print(f"\n📈 Fetching {count} prices for {symbol}...")
    
    for i in range(count):
        response = requests.get(f"{BASE_URL}/prices/latest", 
                              params={"symbol": symbol, "provider": "alpha_vantage"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Price {i+1}: ${data['price']}")
        else:
            print(f"  ✗ Error: {response.text}")
        
        # Small delay to avoid rate limits
        time.sleep(2)

def check_moving_averages():
    """Check if moving averages were calculated"""
    print("\n📊 Checking moving averages in database...")
    
    cmd = '''docker exec market_data_postgres psql -U postgres -d market_data -c "SELECT symbol, average_price, period, calculated_at FROM moving_averages ORDER BY calculated_at DESC LIMIT 5;"'''
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)

def check_kafka_messages():
    """Check messages in Kafka topic"""
    print("\n📬 Checking Kafka messages...")
    print("Visit http://localhost:8080 to see Kafka UI")
    print("Look for topic: 'price-events'")

if __name__ == "__main__":
    print("🚀 Testing Kafka Flow")
    print("="*50)
    
    print("\n⚠️  Make sure:")
    print("1. Docker containers are running (docker-compose ps)")
    print("2. FastAPI app is running")
    print("3. Consumer is running (python scripts/run_consumer.py)")
    
    input("\nPress Enter to continue...")
    
    # Test flow
    fetch_prices("AAPL", 5)
    
    # Wait for processing
    print("\n⏳ Waiting 5 seconds for processing...")
    time.sleep(5)
    
    # Check results
    check_moving_averages()
    check_kafka_messages()
    
    print("\n✅ Test complete!")