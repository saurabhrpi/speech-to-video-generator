### Speech to Video (Veo 3 pipeline)

This project converts spoken audio into a video using a multi-step pipeline:

- **Transcription (OpenAI Whisper)**: Converts speech audio to text.
- **Scene Planning (OpenAI Chat)**: Breaks the concept into sequential scenes for longer videos.
- **Video Generation (AIMLAPI Veo 3)**: Generates video (with native audio when supported) via the AIMLAPI Veo 3 model.
- **Optional Stitching**: For durations over the single-call limit, segments are generated and optionally stitched. v1.0 doesn't use this.

The code is organized into clients (OpenAI and AIMLAPI), a service orchestrating the Veo 3 pipeline, utilities, and a simple CLI.

### Requirements

- Python 3.10+
- An `OPENAI_API_KEY` (for transcription and scene planning)
- An `AIMLAPI_API_KEY` (for Veo 3 video generation via `api.aimlapi.com`)

### Setup

1) Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies.

```powershell
pip install -r requirements.txt
```

3) Create a `.env` file from the example and fill your keys.

```powershell
copy .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=sk-...
AIMLAPI_API_KEY=aiml_...
# Optional: organization/project-scoped usage
OPENAI_ORG_ID=
OPENAI_PROJECT=
AIMLAPI_BASE_URL=https://api.aimlapi.com/v2
## Provider route configuration (per sample program)
AIMLAPI_GENERATE_PATH=/generate/video/google/generation
AIMLAPI_STATUS_PATH=/generate/video/google/generation
AIMLAPI_STATUS_QUERY_PARAM=generation_id
OPENAI_CHAT_MODEL=gpt-4
OPENAI_TRANSCRIBE_MODEL=whisper-1
```

### Usage

#### Web UI (recommended for speech input)

```powershell
python -m src.speech_to_video.webui.app
```

This launches a local Gradio UI in your browser to record or upload audio and generate the video. Ensure your `.env` has API keys set.

- If you hit OpenAI quota (429), enter a Prompt in the UI to bypass transcription and generate directly via AIMLAPI.

#### CLI

Run the CLI for end-to-end speech-to-video generation:

```powershell
python -m src.speech_to_video.cli speech-to-video --audio path\to\audio.wav --duration 60 --quality high
```

Other commands:

```powershell
# Transcribe only
python -m src.speech_to_video.cli transcribe --audio path\to\audio.wav

# Generate video from prompt only
python -m src.speech_to_video.cli generate --prompt "A serene beach at sunset" --duration 10 --quality high
```

Outputs will include URLs returned by the AIMLAPI. If stitching is enabled and `moviepy` is installed with `ffmpeg`, a local stitched file path will be returned.

### Notes

- AIMLAPI Veo 3 API schema is inferred from common patterns. Adjust endpoints/fields as the provider finalizes documentation.
- Costs are estimated at ~`$0.788 / second` as described. Update the rate as pricing evolves.

### Troubleshooting

- Error in UI windows (JSON and Video):
  - Open the "Setup status" panel in the UI and verify both `OPENAI_API_KEY` and `AIMLAPI_API_KEY` are present.
  - Check the JSON error for details and stack trace. Common causes:
    - Missing API keys or wrong values.
    - Network issues (timeouts) when calling AIMLAPI.
    - `moviepy`/`ffmpeg` not installed if stitching is needed.
  - Try a short 5–10s duration test.
  - Run from terminal to see logs: `python -m src.speech_to_video.webui.app`.
  - For 429 insufficient_quota: add billing/credits, wait/reset, or use Prompt override to bypass transcription.

- h11 LocalProtocolError: "Too little data for declared Content-Length"
  - Usually a transient upload/protocol issue. We retry uploads in-memory, but if it persists:
    - Update `openai`: `pip install -U openai`
    - Try a small WAV/MP3 file (5–10s) to isolate
    - Check network/VPN proxies

- AIMLAPI 404 "Cannot POST /v1/generate"
  - Your provider may expose a different route. Set in `.env`:
    - `AIMLAPI_BASE_URL` (e.g., `https://api.aimlapi.com` or a full versioned path)
    - `AIMLAPI_GENERATE_PATH` (e.g., `/video/generate`)
    - `AIMLAPI_STATUS_PATH` (e.g., `/jobs/{job_id}`)
  - Use the UI "Test AIMLAPI Paths" to see what URL was attempted.

### Project-based OpenAI keys (sk-proj-...)

- If your key starts with `sk-proj-`, it may be tied to a specific project.
- You can optionally set:
  - `OPENAI_ORG_ID=org_...`
  - `OPENAI_PROJECT=proj_...`
- Use the UI's "Test OpenAI Key" in the Setup status panel to validate your credentials quickly.

### Cost considerations:

- Current cost is $3 for a 10 sec clip.

### TBD: 

- Deploy on public URL.
- Decrease the cost per 10 sec clip.
- To create multi scene stitching.
