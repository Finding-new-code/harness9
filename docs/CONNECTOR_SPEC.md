# External Connectors & Providers: Harness 9 Studio OS

**Document Version:** 1.0.0  
**Status:** Approved & Canonical  
**Package:** `src/`  
**Cross-References:** `docs/ARCHITECTURE.md`, `docs/SYSTEM_DESIGN.md`, `docs/SECURITY_MODEL.md`  

---

## 1. Connector Layer Architecture

Harness 9 uses an abstract provider pattern for all third-party and external OS interfaces. Every connector implements:
1. **`is_available() -> bool`**: Deterministic capability probe without throwing unhandled exceptions.
2. **Resilient Fallback Hierarchy**: Automatic degradation to local or deterministic offline providers if cloud APIs fail or credentials are missing.
3. **Itemized Unit Cost Attribution**: Automatic reporting of units consumed to the `CreatorEconomics` ledger.
4. **Sandboxed Network Egress**: Egress restricted to approved hostnames by the `SecurityGuard`.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONNECTOR HIERARCHIES                             │
│                                                                             │
│  Research Search:    Tavily API  ──► Exa / Serper  ──► Offline Mock         │
│  Voice Synthesis:    ElevenLabs  ──► OpenAI TTS    ──► SAPI  ──► Harmonic  │
│  Media Discovery:    Wikimedia   ──► Pexels API    ──► Procedural SVG       │
│  Video Rendering:    Playwright  ──► Headless PTY  ──► FFmpeg H.264/AAC     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Research & Knowledge Retrieval Connectors

### 2.1 Tavily / Exa Search API
- **Endpoint**: `https://api.tavily.com/search`
- **Method**: `POST`
- **Parameters**: `query`, `search_depth: "advanced"`, `include_domains`, `max_results: 5`
- **Unit Cost**: $\$0.0050$ per search query.
- **Rate Limit**: 100 requests/minute with exponential backoff.

### 2.2 Wikimedia Commons & API
- **Endpoint**: `https://commons.wikimedia.org/w/api.php`
- **Actions**: `query`, `list=search`, `srnamespace=6`, `prop=imageinfo`, `iiprop=url|size|mime|extmetadata`
- **Unit Cost**: Free / Open Access (Attribution required: CC-BY / CC-SA / Public Domain).

### 2.3 Offline Mock Research Connector
- **Implementation**: Pure local dictionary matcher operating over pre-cached topic corpora (semiconductors, computing, aerospace, biology, physics).
- **Unit Cost**: $\$0.00$. Zero network egress required.

---

## 3. Voice & Audio Synthesis Connectors

### 3.1 ElevenLabs Neural TTS Provider
- **Endpoint**: `https://api.elevenlabs.io/v1/text-to-speech/{voice_id}`
- **Authentication**: `xi-api-key` header (resolved via environment variable).
- **Audio Output**: 16-bit PCM WAV / MP3 ($44.1\text{kHz}$).
- **Unit Cost**: $\$0.000030$ per character ($\$0.030 / 1\text{k chars}$).
- **Parameters**: `stability: 0.5`, `similarity_boost: 0.75`, `style: 0.0`, `use_speaker_boost: true`.

### 3.2 OpenAI Audio / TTS Provider
- **Endpoint**: `https://api.openai.com/v1/audio/speech`
- **Authentication**: Bearer token (`OPENAI_API_KEY`).
- **Model**: `tts-1-hd`
- **Unit Cost**: $\$0.000030$ per character.

### 3.3 Windows SAPI Provider
- **Mechanism**: PowerShell execution of `System.Speech.Synthesis.SpeechSynthesizer`.
- **Requirements**: Windows OS environment.
- **Unit Cost**: $\$0.00$. Zero external API calls.

### 3.4 Harmonic WAV Synthesizer (Deterministic Fallback)
- **Mechanism**: Pure-Python PCM synthesis generating harmonic wave audio with formant shaping ($F_0=130\text{Hz}$, $F_1=500\text{Hz}$, $F_2=1500\text{Hz}$, $F_3=2500\text{Hz}$) and natural amplitude envelopes.
- **Audio Format**: 16-bit signed PCM WAV, $22050\text{Hz}$ / $44100\text{Hz}$, mono.
- **Unit Cost**: $\$0.00$. 100% offline, reproducible, and zero external binary dependencies.

---

## 4. Media Ingestion & Asset Freezers

### 4.1 Asset Freezer & Safety Limits
- **Max Asset Size**: $25\text{MB}$ per asset.
- **Allowed MIME Types**: `image/jpeg`, `image/png`, `image/webp`, `image/svg+xml`, `video/mp4`, `audio/wav`.
- **Magic-Byte Sniffing**: Header validation prevents extension spoofing.
- **Hash Attestation**: Computes SHA-256 during streaming download and indexes against `asset_ledger.json`.

### 4.2 Procedural Vector (SVG) Generator
- **Mechanism**: Generates clean, responsive SVG illustrations with inline gradient styling for technical concepts (transistors, logic gates, neural nets, charts).
- **Unit Cost**: $\$0.00$. Instantaneous generation with zero external network dependencies.

---

## 5. Video Rendering & Encoding Engine

### 5.1 Playwright Headless Chromium Frame Grabber
- **Viewport Resolution**: $1920\times 1080$ ($16:9$) or $1080\times 1920$ ($9:16$).
- **Frame Rate**: Constant 30 FPS (`fps=30`).
- **Timing Synchronization**: Advances GSAP master timeline deterministically frame-by-frame via `window.__timelines["root"].seek(t)`.

### 5.2 FFmpeg Video/Audio Multiplexer
- **Video Encoder**: `libx264` (Preset: `fast`, Pixel Format: `yuv420p`, CRF: `20`).
- **Audio Encoder**: `aac` (Bitrate: $192\text{kbps}$, Sample Rate: $44.1\text{kHz}$).
- **Output Container**: MP4 (`+faststart` for web streaming optimization).
