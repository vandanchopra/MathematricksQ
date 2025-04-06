from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime
import uuid

app = FastAPI()

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def event_generator():
    while True:
        # Create message with current timestamp and strategy info
        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "strategy_id": f"strat_{uuid.uuid4().hex[:8]}", # Generate random strategy ID
            "funds_allocated": round(1000000 + (242344 * asyncio.get_event_loop().time() % 500000)), # Dynamic fund allocation
            "kill_switch": False
        }
        
        # SSE format: "data: message\n\n"
        yield f"data: {json.dumps(data)}\n\n"
        
        # Wait for 2 seconds before next message
        await asyncio.sleep(2)

@app.get("/events")
async def events():
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)