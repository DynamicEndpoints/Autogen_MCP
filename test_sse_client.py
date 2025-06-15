#!/usr/bin/env python3
"""
Test client for SSE (Server-Sent Events) functionality.
Tests the MCP server over HTTP with SSE transport.
"""

import asyncio
import aiohttp
import json
import uuid
from typing import Dict, Any

class SSETestClient:
    """Test client for SSE MCP server."""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.session_id = None
    
    async def test_health_endpoint(self):
        """Test the health check endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Health Check Passed")
                        print(f"   Server: {data.get('name', 'Unknown')}")
                        print(f"   Version: {data.get('version', 'Unknown')}")
                        print(f"   Status: {data.get('status', 'Unknown')}")
                        print(f"   Features: {data.get('features', [])}")
                        print(f"   Connections: {data.get('connections', 0)}")
                        print(f"   Uptime: {data.get('uptime', 0):.2f}s")
                        return True
                    else:
                        print(f"❌ Health Check Failed: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Health Check Error: {e}")
            return False
    
    async def test_sse_connection(self):
        """Test SSE connection establishment."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test SSE endpoint
                async with session.get(f"{self.base_url}/sse") as response:
                    if response.status == 200:
                        print("✅ SSE Connection Established")
                        
                        # Read some SSE data
                        async for line in response.content:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data = line_str[6:]  # Remove 'data: ' prefix
                                try:
                                    message = json.loads(data)
                                    print(f"   Received: {message.get('method', 'unknown')}")
                                    if message.get('method') == 'server/capabilities':
                                        print("✅ Server Capabilities Received")
                                        break
                                except json.JSONDecodeError:
                                    continue
                        return True
                    else:
                        print(f"❌ SSE Connection Failed: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ SSE Connection Error: {e}")
            return False
    
    async def test_mcp_message(self):
        """Test sending MCP messages via HTTP POST."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test list tools request
                message = {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "tools/list",
                    "params": {}
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "x-session-id": "test-session"
                }
                
                async with session.post(
                    f"{self.base_url}/message",
                    json=message,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ MCP Message Test Passed")
                        if 'result' in data and 'tools' in data['result']:
                            tools = data['result']['tools']
                            print(f"   Found {len(tools)} tools:")
                            for tool in tools[:3]:  # Show first 3 tools
                                print(f"     - {tool.get('name', 'unnamed')}: {tool.get('description', 'no description')}")
                        return True
                    else:
                        print(f"❌ MCP Message Test Failed: HTTP {response.status}")
                        text = await response.text()
                        print(f"   Response: {text}")
                        return False
        except Exception as e:
            print(f"❌ MCP Message Test Error: {e}")
            return False
    
    async def test_resource_endpoints(self):
        """Test resource listing via MCP."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test list resources
                message = {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "resources/list",
                    "params": {}
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "x-session-id": "test-session"
                }
                
                async with session.post(
                    f"{self.base_url}/message",
                    json=message,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Resource Listing Test Passed")
                        if 'result' in data and 'resources' in data['result']:
                            resources = data['result']['resources']
                            print(f"   Found {len(resources)} resources:")
                            for resource in resources:
                                print(f"     - {resource.get('uri', 'no-uri')}: {resource.get('name', 'unnamed')}")
                        return True
                    else:
                        print(f"❌ Resource Listing Test Failed: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Resource Listing Test Error: {e}")
            return False
    
    async def test_prompt_endpoints(self):
        """Test prompt listing via MCP."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test list prompts
                message = {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "prompts/list",
                    "params": {}
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "x-session-id": "test-session"
                }
                
                async with session.post(
                    f"{self.base_url}/message",
                    json=message,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Prompt Listing Test Passed")
                        if 'result' in data and 'prompts' in data['result']:
                            prompts = data['result']['prompts']
                            print(f"   Found {len(prompts)} prompts:")
                            for prompt in prompts:
                                print(f"     - {prompt.get('name', 'unnamed')}: {prompt.get('description', 'no description')}")
                        return True
                    else:
                        print(f"❌ Prompt Listing Test Failed: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Prompt Listing Test Error: {e}")
            return False

    async def run_all_tests(self):
        """Run all SSE tests."""
        print("🚀 Starting SSE Test Suite")
        print("=" * 60)
        
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("SSE Connection", self.test_sse_connection),
            ("MCP Messages", self.test_mcp_message),
            ("Resource Endpoints", self.test_resource_endpoints),
            ("Prompt Endpoints", self.test_prompt_endpoints),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Testing {test_name}...")
            if await test_func():
                passed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All SSE tests passed! Server is fully functional!")
        else:
            print("❌ Some tests failed. Check server configuration.")
        
        return passed == total

async def main():
    """Main test function."""
    client = SSETestClient()
    await client.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
