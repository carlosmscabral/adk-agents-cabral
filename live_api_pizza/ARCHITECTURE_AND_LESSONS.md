# Gemini Live API Architecture & Integration Guide

This document details the precise technical requirements and implementation patterns required to build a stable, real-time bidirectional (Bidi) audio streaming application using the Google Agent Development Kit (ADK) backend and a React (Next.js) frontend.

## 1. Backend Architecture (ADK + FastAPI)

The standard `adk api_server` CLI is optimized for text-based JSON endpoints and is not suitable for raw binary audio WebSocket connections out of the box. To support real-time voice, you **must** implement a custom FastAPI wrapper around the ADK `Runner`.

### 1.1. Model Selection & Location
- **Model:** Use models that natively support bidirectional audio streaming. 
  - Preview/Native: `gemini-live-2.5-flash-native-audio` (Ensure your Google Cloud Project is allowlisted for this specific model).
- **Location:** Preview models are often restricted to specific regions (e.g., `us-central1`).
  - **CRITICAL:** Do NOT rely on Python's `os.environ` to set `GOOGLE_CLOUD_LOCATION` at runtime, as the `google-genai` SDK caches this upon import. Hardcode the environment variable in your `Dockerfile` or pass it explicitly to Cloud Run via `--set-env-vars`.

### 1.2. WebSocket Handling (Custom FastAPI)
Instead of relying on the ADK CLI, expose a raw WebSocket endpoint in your FastAPI app. This allows you to handle raw binary frames (`bytes`) directly, avoiding JSON parsing errors on large audio chunks.

```python
# Extract from api_server.py
@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await websocket.accept()
    
    # 1. Initialize ADK Session manually to avoid 404s
    session = await session_service.get_session(app_name="agent", user_id=user_id, session_id=session_id)
    if not session:
        await session_service.create_session(app_name="agent", user_id=user_id, session_id=session_id)

    live_request_queue = LiveRequestQueue()

    # 2. Upstream Task: Receive from Browser
    async def upstream_task():
        while True:
            message = await websocket.receive()
            if "bytes" in message:
                # Wrap raw binary PCM data into the ADK Blob format
                audio_blob = types.Blob(mime_type="audio/pcm;rate=16000", data=message["bytes"])
                live_request_queue.send_realtime(audio_blob)
            elif "text" in message:
                # Handle text inputs
                ...
                
    # 3. Downstream Task: Send to Browser
    async def downstream_task():
        async for event in runner.run_live(..., live_request_queue=live_request_queue):
            # Serialize ADK Event to JSON string and send
            await websocket.send_text(event.model_dump_json(exclude_none=True, by_alias=True))
            
    await asyncio.gather(upstream_task(), downstream_task())
```

---

## 2. Frontend Architecture (React Web Audio API)

The frontend must conform to strict audio encoding formats. The Gemini Live API expects **16-bit PCM Audio at 16kHz (Little-Endian)**. Standard browser `MediaRecorder` implementations output compressed formats (like `webm` or `ogg`) which will cause the Gemini model to silently ignore the input or crash the connection.

### 2.1. Microphone Capture (Upstream)
You must capture the raw `MediaStream` and manually convert the `Float32Array` buffers to 16-bit PCM using a `ScriptProcessorNode` (or `AudioWorkletNode`).

```javascript
// Request explicitly 16kHz audio
const stream = await navigator.mediaDevices.getUserMedia({ 
    audio: { sampleRate: 16000, channelCount: 1 }
});

const audioContext = new AudioContext({ sampleRate: 16000 });
const source = audioContext.createMediaStreamSource(stream);
const processor = audioContext.createScriptProcessor(4096, 1, 1);

processor.onaudioprocess = (e) => {
    if (socket.readyState === WebSocket.OPEN) {
        const float32Data = e.inputBuffer.getChannelData(0);
        // Convert Float32 (-1.0 to 1.0) to Int16 (-32768 to 32767)
        const pcm16Data = new Int16Array(float32Data.length);
        for (let i = 0; i < float32Data.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Data[i]));
            pcm16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        // Send raw ArrayBuffer over WebSocket (browser sends as Binary Frame)
        socket.send(pcm16Data.buffer); 
    }
};
source.connect(processor);
processor.connect(audioContext.destination);
```

### 2.2. Audio Playback (Downstream)
The ADK `Event` model returns audio responses as base64-encoded strings inside `data.content.parts[x].inlineData.data`. The MIME type is `audio/pcm;rate=24000`. 

**CRITICAL RULES for Playback:**
1.  **Autoplay Restrictions:** Browsers block audio playback unless the `AudioContext` is created or resumed immediately following a user gesture (e.g., clicking a "Start Talking" button).
2.  **Gapless Scheduling:** You must decode the base64 chunks back to `Float32Array` and schedule them precisely using `AudioContext.currentTime`. Naively calling `play()` on each chunk will cause them to overlap or cancel out, resulting in silence.

```javascript
// Shared references across the component lifecycle
const playbackContextRef = useRef(null);
const nextPlayTimeRef = useRef(0);

// Inside the user interaction handler (e.g. onClick)
if (!playbackContextRef.current) {
    playbackContextRef.current = new AudioContext({ sampleRate: 24000 }); // Match output sample rate
} else if (playbackContextRef.current.state === 'suspended') {
    playbackContextRef.current.resume();
}

// Inside the WebSocket onmessage handler
const audioPart = adkEvent.content.parts.find(p => p.inlineData && p.inlineData.mimeType.includes('audio'));
if (audioPart && playbackContextRef.current) {
    const audioCtx = playbackContextRef.current;
    
    // 1. Decode Base64 to Uint8Array
    const binaryString = window.atob(audioPart.inlineData.data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    
    // 2. Convert Int16 PCM to Float32 Array
    const pcm16Data = new Int16Array(bytes.buffer);
    const float32Data = new Float32Array(pcm16Data.length);
    for (let i = 0; i < pcm16Data.length; i++) {
        float32Data[i] = pcm16Data[i] / 32768.0;
    }
    
    // 3. Create AudioBuffer
    const audioBuffer = audioCtx.createBuffer(1, float32Data.length, 24000);
    audioBuffer.getChannelData(0).set(float32Data);
    
    // 4. Schedule Gapless Playback
    const source = audioCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioCtx.destination);
    
    // If the queue ran dry, start slightly in the future to avoid clipping
    if (nextPlayTimeRef.current < audioCtx.currentTime) {
        nextPlayTimeRef.current = audioCtx.currentTime + 0.1; 
    }
    source.start(nextPlayTimeRef.current);
    nextPlayTimeRef.current += audioBuffer.duration;
}
```

### 2.3. Transcriptions vs. Content
The ADK WebSocket response stream will send multiple partial events before sending the final audio chunk.
- **Transcriptions:** `data.outputTranscription.text` streams the real-time text of what the agent is saying (or `inputTranscription` for what the user is saying). Use these to update the chat UI interactively.
- **Audio Delivery:** The actual audio `inlineData` may be delivered asynchronously alongside or after the text transcriptions. Ensure your UI logic does not accidentally drop the entire event just because it lacks a `text` part in the `content` block.