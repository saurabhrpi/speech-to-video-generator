# Overview

This is a Speech-to-Video generation application that converts spoken audio into AI-generated videos through a multi-step pipeline. The system:

1. Transcribes audio to text using OpenAI's Whisper model
2. Generates videos from text prompts using AIMLAPI's Veo 3 (Alibaba WAN 2.1 Turbo) model
3. Supports both single-shot and multi-segment video generation
4. Provides both CLI and web UI (Gradio) interfaces
5. Includes a clip storage system for managing generated videos

The application is built in Python and designed for creative content generation workflows.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Structure

The codebase follows a modular, service-oriented architecture organized into:

- **Clients Layer** (`src/speech_to_video/clients/`): Thin wrappers around external APIs (OpenAI, AIMLAPI)
- **Services Layer** (`src/speech_to_video/services/`): Business logic orchestration (VideoService)
- **Utilities Layer** (`src/speech_to_video/utils/`): Configuration, video processing, and clip storage
- **Interface Layer**: CLI (`cli.py`) and Web UI (`webui/app.py`)

**Design rationale**: This layered architecture separates concerns, making it easy to swap providers, modify business logic, or add new interfaces without touching core functionality.

## Configuration Management

Uses environment variables loaded via `python-dotenv` with a Settings dataclass pattern:
- All configuration centralized in `utils/config.py`
- `.env` file overrides system environment variables for development convenience
- Supports both required keys (API keys) and optional customization (models, paths, debug flags)

**Alternative considered**: Hard-coded configuration files were rejected in favor of environment variables for better security and deployment flexibility.

## Video Generation Pipeline

**Single Generation Mode** (≤10 seconds):
- Direct API call to AIMLAPI
- Simple request → poll → return flow

**Multi-Generation Mode** (>10 seconds):
- Breaks long content into segments
- Generates multiple clips
- Optional stitching using MoviePy (falls back to first clip if unavailable)

**Design decision**: The 10-second threshold accommodates API limitations while providing seamless UX. Stitching is optional to allow the system to degrade gracefully when ffmpeg/moviepy aren't available.

## API Client Architecture

### OpenAI Client
- Handles Whisper transcription with retry logic
- Uses in-memory streams to avoid h11 Content-Length issues
- Exponential backoff for transient failures

### AIMLAPI Client
- RESTful integration with configurable endpoints
- Built-in retry logic for rate limits (429) and server errors (5xx)
- Stateful session management for connection pooling

**Pros**: Isolated retry logic prevents cascading failures; configurable paths allow easy provider migrations
**Cons**: Duplicate retry patterns could be DRYed into shared middleware

## Web Interface (Gradio)

- Tab-based UI: Transcribe, Generate from Prompt, Speech-to-Video, Playlist management
- Rate limiting per IP address using sliding window algorithm
- File size validation (10MB default for audio)
- Maintenance mode toggle for operational control
- Public/private mode switching

**Design choice**: Gradio chosen for rapid prototyping and built-in component library. Rate limiting implemented at application level (not infrastructure) for portability.

## Data Persistence

### Clip Storage
- JSON-based playlist storage in `clips/playlist.json`
- Simple append-only log with timestamps
- No database required for MVP

**Trade-offs**: JSON file storage is simple but not concurrent-safe. Future scaling would require SQLite or proper database. Chosen for minimal dependencies and easy inspection/debugging.

## Error Handling Strategy

- Graceful degradation throughout (e.g., stitching fallback)
- Retry logic with exponential backoff for transient failures
- Detailed error responses with status codes preserved
- Debug mode for transcript visibility

## Video Processing

Uses MoviePy for video manipulation:
- Downloads remote URLs to temporary directory
- Concatenates clips with `compose` method
- Explicit resource cleanup (close clips) for Windows compatibility
- Fallback mechanisms when dependencies unavailable

**Alternative considered**: ffmpeg direct subprocess calls were rejected in favor of MoviePy's Python API for better error handling and cross-platform compatibility.

# External Dependencies

## Third-Party APIs

1. **OpenAI API**
   - Whisper model for audio transcription
   - GPT models for chat/scene planning (architecture present, not heavily used in v1)
   - Requires: `OPENAI_API_KEY`
   - Optional: Organization and project scoping

2. **AIMLAPI (api.aimlapi.com)**
   - Veo 3 video generation (Alibaba WAN 2.1 Turbo model)
   - RESTful API with generation and status polling endpoints
   - Requires: `AIMLAPI_API_KEY`
   - Configurable base URL and endpoint paths

## Python Dependencies

- **openai** (≥1.35.0): Official OpenAI SDK
- **requests** (≥2.31.0): HTTP client for AIMLAPI
- **python-dotenv** (≥1.0.1): Environment configuration
- **moviepy** (≥1.0.3): Video processing and stitching
- **tqdm** (≥4.66.0): Progress bars for long operations
- **gradio** (≥4.44.0): Web UI framework

## System Dependencies

- **FFmpeg**: Required by MoviePy for video processing (external binary)
- **Python 3.10+**: Language runtime requirement

## File System Dependencies

- Temporary directory access for video downloads and stitching
- `clips/` directory for playlist JSON storage
- `.env` file for configuration (optional, falls back to environment variables)