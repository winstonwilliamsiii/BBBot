#!/usr/bin/env python
"""Quick test of Rhea charting API outputs."""
import requests
import time
import json

base = "http://127.0.0.1:7860"
print("Testing Rhea charting API...")

# POST to analyze_ticker
r = requests.post(
    base + "/gradio_api/call/_gradio_analyze",
    json={"data": ["GD", "", "false"]},
    timeout=45,
)
print(f"POST status: {r.status_code}")

if r.status_code == 200:
    evt_id = r.json()["event_id"]
    print(f"Event ID: {evt_id}")
    
    # Wait for processing
    time.sleep(12)
    
    # Poll results
    g = requests.get(
        base + f"/gradio_api/call/_gradio_analyze/{evt_id}",
        timeout=30,
    )
    print(f"GET status: {g.status_code}")
    
    # Parse SSE stream
    lines = g.text.split("\n")
    for i, line in enumerate(lines):
        if "event: complete" in line and i + 1 < len(lines):
            json_str = lines[i + 1].replace("data: ", "")
            try:
                data = json.loads(json_str)
                print(f"\n✅ Outputs received: {len(data)}")
                print(f"   Output[0] chart type: {data[0].get('type')}")
                print(f"   Output[1] summary: {data[1][:120]}")
                json_data = json.loads(data[2])
                print(f"   Output[2] ticker: {json_data.get('ticker')}")
                print(f"   Output[2] action: {json_data.get('action')}")
                print(f"   Output[2] composite_score: {json_data.get('composite_score')}")
            except Exception as e:
                print(f"Error parsing: {e}")
            break
else:
    print(f"Error: {r.text[:300]}")
