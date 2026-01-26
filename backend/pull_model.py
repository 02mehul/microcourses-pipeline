import httpx
import asyncio
import json

async def pull_model():
    url = "http://localhost:11434/api/pull"
    print(f"Triggering model pull for 'llama3' at {url}...")
    
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json={"name": "llama3"}) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            status = data.get("status")
                            completed = data.get("completed")
                            total = data.get("total")
                            if completed and total:
                                percent = (completed / total) * 100
                                print(f"{status}: {percent:.1f}%")
                            else:
                                print(f"{status}")
                                
                            if status == "success":
                                print("Model pulled successfully!")
                        except:
                            print(line)
    except Exception as e:
        print(f"Error pulling model: {e}")

if __name__ == "__main__":
    asyncio.run(pull_model())
