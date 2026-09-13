import asyncio
import main

async def run():
    result = await main.invoke({
        "prompt": "Use the browser to visit https://example.com and tell me the page title and the main heading.",
        "customer_id": "CUST-123",
        "session_id": "t11",
    })
    print(result)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    loop.run_until_complete(run())
finally:
    loop.close()
