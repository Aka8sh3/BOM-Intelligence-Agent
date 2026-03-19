import asyncio
import aiohttp
import json
import websockets

async def test_upload_and_progress():
    url = "http://localhost:8000/api/upload-bom"
    file_path = "sample_bom.csv"
    
    print("1. Uploading BOM via REST...")
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('file', open(file_path, 'rb'), filename='sample_bom.csv')
        
        async with session.post(url, data=data) as resp:
            result = await resp.json()
            print("Upload Response:", json.dumps(result, indent=2))
            
            if not result.get("success"):
                print("Upload failed.")
                return
                
            analysis_id = result.get("analysis_id")
            
    print("\n2. Connecting to WebSocket for progress...")
    uri = "ws://localhost:8000/ws/progress"
    async with websockets.connect(uri) as websocket:
        while True:
            msg_str = await websocket.recv()
            msg = json.loads(msg_str)
            
            # We only care about our analysis_id
            if msg.get("analysis_id") != analysis_id:
                continue
                
            if msg["type"] == "progress":
                print(f"[{msg['current']}/{msg['total']}] Analysis: {msg['part_number']}")
            elif msg["type"] == "complete":
                print("\n3. Analysis Complete!")
                break
            elif msg["type"] == "error":
                print("\nError occurred during analysis:", msg["error"])
                break
                
    print("\n4. Fetching final analysis results...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://localhost:8000/api/analysis/{analysis_id}") as resp:
            final_result = await resp.json()
            print(f"Status: {final_result.get('status')}")
            summary = final_result.get("result", {}).get("summary", {})
            print("Final Summary:", json.dumps(summary, indent=2))

if __name__ == "__main__":
    asyncio.run(test_upload_and_progress())
