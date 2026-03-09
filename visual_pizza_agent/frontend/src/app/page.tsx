'use client';

import { useState, useRef, useEffect } from 'react';

// Helper to convert float32 to int16
function floatTo16BitPCM(input: Float32Array) {
  const output = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]));
    output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return output;
}

// Helper to encode ArrayBuffer to Base64
function arrayBufferToBase64(buffer: ArrayBuffer) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

// Helper to create WAV blob from PCM bytes
function pcmToWav(pcmBytes: Uint8Array, sampleRate: number) {
  const numChannels = 1;
  const byteRate = sampleRate * numChannels * 2;
  const blockAlign = numChannels * 2;
  const buffer = new ArrayBuffer(44 + pcmBytes.length);
  const view = new DataView(buffer);

  const writeString = (v: DataView, offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      v.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + pcmBytes.length, true);
  writeString(view, 8, 'WAVE');

  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true); 
  view.setUint16(20, 1, true); 
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, 16, true); 

  writeString(view, 36, 'data');
  view.setUint32(40, pcmBytes.length, true);

  new Uint8Array(buffer, 44).set(pcmBytes);

  return new Blob([buffer], { type: 'audio/wav' });
}

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [status, setStatus] = useState('Pronto (Ready)');
  const socketRef = useRef<WebSocket | null>(null);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const nextPlayTimeRef = useRef<number>(0);
  const audioBufferAccumulator = useRef<Uint8Array>(new Uint8Array(0));

  useEffect(() => {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'ws://localhost:8080/ws/pizza_user/pizza_session_live';
    
    const connect = async () => {
      console.log('Connecting to:', backendUrl);
      const socket = new WebSocket(backendUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setStatus('Connesso (Connected)');
        const initialText = "Ciao! I am here for the pizza.";
        setMessages(prev => [...prev, { role: 'user', text: initialText }]);
        socket.send(JSON.stringify({
          type: "text",
          text: initialText
        }));
      };
      socket.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.outputTranscription?.text) {
             setMessages(prev => {
                const newMsgs = [...prev];
                // Replace the last agent message if it was a partial transcription
                if (newMsgs.length > 0 && newMsgs[newMsgs.length - 1].role === 'agent_partial') {
                    newMsgs[newMsgs.length - 1] = { role: data.outputTranscription.finished ? 'agent' : 'agent_partial', text: data.outputTranscription.text };
                } else {
                    newMsgs.push({ role: data.outputTranscription.finished ? 'agent' : 'agent_partial', text: data.outputTranscription.text });
                }
                return newMsgs;
             });
          }

          if (data.inputTranscription?.text) {
             setMessages(prev => {
                const newMsgs = [...prev];
                if (newMsgs.length > 0 && newMsgs[newMsgs.length - 1].role === 'user_partial') {
                    newMsgs[newMsgs.length - 1] = { role: data.inputTranscription.finished ? 'user' : 'user_partial', text: data.inputTranscription.text };
                } else {
                    newMsgs.push({ role: data.inputTranscription.finished ? 'user' : 'user_partial', text: data.inputTranscription.text });
                }
                return newMsgs;
             });
          }
          
          if (data.content?.parts) {
            const textParts = data.content.parts.filter((p: any) => p.text).map((p: any) => p.text);
            if (textParts.length > 0) {
              setMessages(prev => [...prev, { role: 'agent', text: textParts.join('') }]);
            }

            // Handle ADK Event model audio (inlineData with base64)
            const audioPart = data.content.parts.find((p: any) => p.inlineData && p.inlineData.mimeType?.includes('audio'));
            if (audioPart) {
                 let standardBase64 = audioPart.inlineData.data.replace(/-/g, '+').replace(/_/g, '/');
                 while (standardBase64.length % 4) {
                   standardBase64 += '=';
                 }
                 const binaryString = window.atob(standardBase64);
                 const len = binaryString.length;
                 const bytes = new Uint8Array(len);
                 for (let i = 0; i < len; i++) {
                     bytes[i] = binaryString.charCodeAt(i);
                 }

                 if (!playbackContextRef.current) {
                     console.warn("Audio context not initialized yet!");
                     return;
                 }
                 const audioCtx = playbackContextRef.current;
                 
                 const pcm16Data = new Int16Array(bytes.buffer);
                 const float32Data = new Float32Array(pcm16Data.length);
                 let maxAmplitude = 0;
                 for (let i = 0; i < pcm16Data.length; i++) {
                     const val = pcm16Data[i] / 32768.0;
                     float32Data[i] = val;
                     if (Math.abs(val) > maxAmplitude) maxAmplitude = Math.abs(val);
                 }
                 
                 console.log(`Received audio chunk: ${float32Data.length} samples. Max amplitude: ${maxAmplitude}`);

                 if (maxAmplitude > 0) {
                     const audioBuffer = audioCtx.createBuffer(1, float32Data.length, 24000);
                     audioBuffer.getChannelData(0).set(float32Data);
                     
                     const source = audioCtx.createBufferSource();
                     source.buffer = audioBuffer;
                     source.connect(audioCtx.destination);
                     
                     if (nextPlayTimeRef.current < audioCtx.currentTime) {
                         nextPlayTimeRef.current = audioCtx.currentTime + 0.1; // 100ms buffer
                     }
                     
                     source.start(nextPlayTimeRef.current);
                     nextPlayTimeRef.current += audioBuffer.duration;
                     console.log(`Queued audio to play at ${nextPlayTimeRef.current - audioBuffer.duration}, duration: ${audioBuffer.duration}`);
                 }
            }
            }
            } catch (e) {
            console.error('Error parsing event:', e);
            }
      };
      socket.onclose = () => {
        setStatus('Disconnesso (Disconnected). Riconnettendo...');
        setTimeout(connect, 3000);
      };
      socket.onerror = (err) => console.error('WebSocket Error:', err);
    };

    connect();

    return () => {
      socketRef.current?.close();
    };
  }, []);

  const startRecording = async () => {
    try {
      // Create playback context on user gesture to avoid autoplay block
      if (!playbackContextRef.current) {
          playbackContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
      }
      
      if (playbackContextRef.current.state === 'suspended') {
          playbackContextRef.current.resume();
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
      }});
      mediaStreamRef.current = stream;

      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcmData = floatTo16BitPCM(inputData);
          socketRef.current.send(pcmData.buffer);
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      setIsRecording(true);
      setStatus('Registrando... (Recording...)');
    } catch (err) {
      console.error('Error starting recording:', err);
      setStatus('Errore Microfono (Mic Error)');
    }
  };

  const stopRecording = () => {
    if (processorRef.current && audioContextRef.current) {
        processorRef.current.disconnect();
        audioContextRef.current.close();
    }
    if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
    }
    
    setIsRecording(false);
    setStatus('Connesso (Connected)');
  };

  const testAudioPlayback = () => {
    // Generate 1 second of 440Hz sine wave at 24kHz, 16-bit PCM
    const sampleRate = 24000;
    const duration = 1;
    const numSamples = sampleRate * duration;
    const pcmData = new Int16Array(numSamples);
    for (let i = 0; i < numSamples; i++) {
        const t = i / sampleRate;
        const val = Math.sin(2 * Math.PI * 440 * t);
        pcmData[i] = val * 0x7FFF;
    }
    
    // Use the exact same playback logic as the agent response
    const wavBlob = pcmToWav(new Uint8Array(pcmData.buffer), sampleRate);
    const audioUrl = URL.createObjectURL(wavBlob);
    const audio = new Audio(audioUrl);
    audio.play().then(() => console.log("Test audio played successfully")).catch(e => console.error("Test audio playback failed:", e));
    audio.onended = () => URL.revokeObjectURL(audioUrl);
  };

  return (
    <main style={{
      fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
      backgroundColor: '#fffdf0',
      color: '#333',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '2rem'
    }}>
      <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 style={{ color: '#d32f2f', fontSize: '3rem', margin: 0 }}>🍕 Mama\'s Pizza Chef! 🍕</h1>
        <p style={{ fontSize: '1.2rem', fontStyle: 'italic', color: '#1b5e20' }}>"Mamma Mia! Let\'s build the perfect pie!"</p>
        <button onClick={testAudioPlayback} style={{ marginTop: '1rem', padding: '0.5rem 1rem', cursor: 'pointer' }}>Test Audio Playback (Beep)</button>
      </header>

      <div style={{
        width: '100%',
        maxWidth: '600px',
        backgroundColor: '#fff',
        borderRadius: '15px',
        boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        border: '3px solid #1b5e20'
      }}>
        <div style={{
          height: '400px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
          padding: '1rem',
          borderBottom: '2px dashed #ccc'
        }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#888', marginTop: '2rem' }}>
              "Ciao! Tell me, what kind of pizza makes your heart sing?"
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} style={{
              alignSelf: m.role.includes('user') ? 'flex-end' : 'flex-start',
              backgroundColor: m.role.includes('user') ? '#e8f5e9' : '#fff9c4',
              padding: '0.8rem 1rem',
              borderRadius: '12px',
              maxWidth: '80%',
              border: m.role.includes('user') ? '1px solid #1b5e20' : '1px solid #fbc02d',
              opacity: m.role.includes('partial') ? 0.7 : 1
            }}>
              <strong>{m.role.includes('user') ? 'You' : 'Chef'}:</strong> {m.text}
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem' }}>
          {!isRecording ? (
            <button 
              onClick={startRecording}
              style={{
                backgroundColor: '#d32f2f',
                color: 'white',
                border: 'none',
                padding: '1rem 2rem',
                borderRadius: '50px',
                fontSize: '1.1rem',
                cursor: 'pointer',
                fontWeight: 'bold',
                boxShadow: '0 4px 0 #b71c1c'
              }}>
              🎤 Start Talking (Parlare)
            </button>
          ) : (
            <button 
              onClick={stopRecording}
              style={{
                backgroundColor: '#1b5e20',
                color: 'white',
                border: 'none',
                padding: '1rem 2rem',
                borderRadius: '50px',
                fontSize: '1.1rem',
                cursor: 'pointer',
                fontWeight: 'bold',
                boxShadow: '0 4px 0 #1b5e20'
              }}>
              🛑 Stop Talking (Fermare)
            </button>
          )}
        </div>
        <div style={{ textAlign: 'center', fontSize: '0.9rem', color: '#666' }}>
          Status: <span style={{ fontWeight: 'bold' }}>{status}</span>
        </div>
      </div>

      <footer style={{ marginTop: '2rem', textAlign: 'center', color: '#888' }}>
        <p>Built with ❤️ and 🍝 using Google ADK</p>
      </footer>
    </main>
  );
}
