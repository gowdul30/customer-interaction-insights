import os
import json
import asyncio
import argparse
from datetime import datetime
from google import genai
from google.genai import types
import edge_tts
from dotenv import load_dotenv

load_dotenv()

# Replace with your actual Gemini API Key or load from env
API_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_PROMPT = """You are an expert at generating highly realistic customer service transcripts.
Generate a simulated customer service call transcript.
The output MUST be valid JSON containing a list of messages.

Example format:
{
    "topic": "Billing Issue",
    "client": "Verizon",
    "messages": [
        {"speaker": "Agent", "text": "Thank you for calling Verizon, my name is Alex. How can I help you today?"},
        {"speaker": "Customer", "text": "Hi Alex, I'm looking at my bill and there's an unexpected charge of $40."}
    ]
}

Include realistic hesitation, frustration if applicable, and a complete resolution or escalation.
Make the call about 8-12 turns long.
"""

async def generate_transcript(scenario_prompt):
    print(f"\n[INFO] Generating synthetic transcript for: {scenario_prompt}")
    if not API_KEY:
        print("[ERROR] GEMINI_API_KEY environment variable is not set.")
        return None
        
    client = genai.Client(api_key=API_KEY)
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=scenario_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
    )
    
    try:
        data = json.loads(response.text)
        return data
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return None

async def generate_audio_for_message(text, voice, output_filename):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_filename)
    return output_filename

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio")

async def generate_call_audio(transcript, output_dir=DEFAULT_AUDIO_DIR):
    os.makedirs(output_dir, exist_ok=True)
    
    import uuid
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    base_name = f"call_{timestamp}_{unique_id}"
    
    # Save transcript
    transcript_path = os.path.join(output_dir, f"{base_name}.json")
    with open(transcript_path, "w") as f:
        json.dump(transcript, f, indent=2)
    print(f"[INFO] Saved transcript to {transcript_path}")
    
    # Voice selection
    # Agent: Female, Customer: Male
    voices = {
        "Agent": "en-US-AvaNeural",
        "Customer": "en-US-GuyNeural"
    }
    
    audio_files = []
    
    print("[INFO] Generating audio clips with Edge TTS...")
    for i, msg in enumerate(transcript.get("messages", [])):
        speaker = msg.get("speaker", "Agent")
        text = msg.get("text", "")
        voice = voices.get(speaker, "en-US-AvaNeural")
        
        temp_file = os.path.join(output_dir, f"temp_{i}.mp3")
        await generate_audio_for_message(text, voice, temp_file)
        audio_files.append(temp_file)
        print(f"  - Generated clip for {speaker}")
        
    print("[INFO] Combining audio clips...")
    try:
        final_audio_path = os.path.join(output_dir, f"{base_name}.mp3")
        with open(final_audio_path, "wb") as outfile:
            for file in audio_files:
                with open(file, "rb") as infile:
                    outfile.write(infile.read())
                    
        print(f"[SUCCESS] Final audio saved to {final_audio_path}")
        
        # Cleanup temp files
        for file in audio_files:
            try:
                os.remove(file)
            except:
                pass
            
    except Exception as e:
        print(f"[ERROR] Failed to combine audio: {e}")

async def main():
    scenarios = [
        "Generate a realistic customer service call about a billing error where the customer was double charged for Verizon. The customer is highly frustrated and demands a refund and escalation.",
        "Generate a customer service call for Wells Fargo where a customer wants to dispute a fraudulent credit card transaction. Customer is anxious but polite.",
        "Generate a tech support call for Comcast where the internet keeps dropping. The agent successfully troubleshoots it by resetting the modem.",
        "Generate a call for AT&T where the customer wants to cancel their service because it's too expensive. The agent tries to retain them with a discount but fails.",
        "Generate a T-Mobile call where a customer is just inquiring about international roaming rates for an upcoming trip to Europe. It's a quick, pleasant interaction."
    ]
    
    for i, prompt in enumerate(scenarios):
        print(f"\n=== Generating Call {i+1}/{len(scenarios)} ===")
        transcript = await generate_transcript(prompt)
        if transcript:
            await generate_call_audio(transcript)

if __name__ == "__main__":
    asyncio.run(main())
