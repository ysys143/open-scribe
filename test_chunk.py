#!/usr/bin/env python
"""Test chunk transcription to debug the issue"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get the first chunk if it exists
chunk_file = "/Users/jaesolshin/Documents/GitHub/yt-trans/temp_audio/chunk_000.mp3"

if not os.path.exists(chunk_file):
    print(f"Chunk file not found: {chunk_file}")
    exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print(f"Testing with chunk file: {chunk_file}")
print(f"File size: {os.path.getsize(chunk_file) / 1024 / 1024:.2f} MB")

# Test transcription with text format (what GPT-4o uses)
try:
    with open(chunk_file, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file,
            response_format="text"
        )
    
    print(f"\nResponse type: {type(response)}")
    print(f"Is string: {isinstance(response, str)}")
    
    if isinstance(response, str):
        print(f"Response length: {len(response)} chars")
        print(f"First 200 chars: {response[:200]}")
    else:
        print(f"Response attrs: {dir(response)}")
        if hasattr(response, 'text'):
            print(f"response.text: {response.text[:200]}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()