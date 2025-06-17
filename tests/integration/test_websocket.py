#!/usr/bin/env python3
"""Test WebSocket connection to the dashboard endpoint"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket():
    uri = "ws://localhost:12001/ws/dashboard"
    
    try:
        print(f"🔌 Connecting to WebSocket: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Receive and print messages for 10 seconds
            start_time = datetime.now()
            message_count = 0
            
            while (datetime.now() - start_time).seconds < 10:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    print(f"\n📊 Message #{message_count} received:")
                    print(f"   Engines: {len(data.get('engines', []))}")
                    print(f"   System Metrics: {data.get('systemMetrics', {}).get('totalTasks', 'N/A')} total tasks")
                    print(f"   Alerts: {len(data.get('alerts', []))}")
                    
                    # Show engine status
                    for engine in data.get('engines', []):
                        print(f"   🔧 {engine['type']}: {engine['status']} ({engine['performance']:.1f}%)")
                    
                except asyncio.TimeoutError:
                    print("⏰ No message received in 3 seconds")
                    continue
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    continue
            
            print(f"\n🎉 Test completed! Received {message_count} messages in 10 seconds")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing reVoAgent WebSocket Dashboard Connection")
    print("=" * 60)
    
    success = asyncio.run(test_websocket())
    
    if success:
        print("\n✅ WebSocket test PASSED!")
        print("🚀 Real-time dashboard is working correctly")
    else:
        print("\n❌ WebSocket test FAILED!")
        print("🔧 Check backend server and WebSocket endpoint")