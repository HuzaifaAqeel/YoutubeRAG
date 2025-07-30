# YouTube RAG System

## 1. Overview

This project is a **Retrieval-Augmented Generation (RAG)** system designed to answer questions about YouTube videos. It allows a user to provide a YouTube video—either via a URL or by uploading a video file—and then engage in a conversation with a Large Language Model (LLM) to ask questions about the video's content.

The system first extracts the full audio transcript from the video. This transcript then serves as the foundational context for the Google Gemini LLM. When the user asks a question, the system feeds both the transcript and the user's prompt to the LLM, enabling it to generate accurate, context-aware answers based *only* on the information contained within that specific video.

## 2. How It Works

The application follows a simple yet powerful workflow:

1.  **User Input**: The user chooses one of two methods to provide a video:
    *   **YouTube Link**: The user pastes the URL of a YouTube video.
    *   **Video Upload**: The user uploads a video file (e.g., MP4, MOV, AVI) directly from their computer.

2.  **Transcript Extraction**:
    *   For a YouTube link, the system uses the `youtube-transcript-api` to fetch the pre-existing, auto-generated or manually-created captions for the video.
    *   For an uploaded video file, the system uses the powerful `openai-whisper` library to perform local speech-to-text transcription, generating a transcript from the video's audio.

3.  **Context Loading**: The extracted transcript text is loaded into the application's memory and displayed to the user in an expandable section. This text becomes the sole source of truth for the RAG system.

4.  **Question Answering**:
    *   The user types a question into the chat interface.
    *   The system creates a carefully structured prompt containing the user's question along with the entire video transcript.
    *   This combined prompt is sent to the **Google Gemini API**.
    *   The Gemini model (`gemini-1.5-flash`) analyzes the request and generates an answer based on the provided transcript.

5.  **Chat Interface**: The user's question and the LLM's answer are displayed in a familiar chat format. The conversation history is maintained, allowing for follow-up questions.

## 3. Prerequisites

Before running the application, you must have the following software installed on your system:

*   **Python**: Version 3.9 or higher.
*   **FFmpeg**: This is a critical dependency required for processing audio from uploaded video files.
    *   **Installation (Windows)**: The easiest way to install it is with a package manager like Chocolatey or Winget. Open PowerShell **as an administrator** and run one of the following commands:
        ```powershell
        # Using Winget
        winget install -e --id Gyan.FFmpeg --accept-source-agreements

        # Using Chocolatey
        choco install ffmpeg
        ```
    *   After installation, you **must restart your terminal and/or code editor** for the system to recognize the change.

## 4. Dependencies & Their Roles

All required Python libraries are listed in the `requirements.txt` file. Below is a detailed explanation of each one's role in the project.

*   `streamlit`: The core framework used to build the entire interactive web application, including the UI components, chat interface, and input forms.
*   `google-generativeai`: The official Google Python SDK used to communicate with the Gemini API. It handles the sending of prompts and the receiving of generated content.
*   `youtube-transcript-api`: A specialized library for fetching transcripts directly from YouTube. It is highly efficient for videos that have existing captions.
*   `openai-whisper`: A state-of-the-art speech-to-text model developed by OpenAI. It is used to transcribe the audio from user-uploaded video files locally, ensuring privacy and eliminating the need for an external audio processing API.
*   `python-dotenv`: A utility for managing environment variables. Although we hardcoded the API key in the final version, this library is essential for securely managing secret keys by loading them from a `.env` file, which is a best practice.

## 5. Code Explanation

This section breaks down the structure and functionality of the main application file, `app.py`.

### Imports

The script begins by importing all necessary libraries. `google.api_core.exceptions` is specifically imported to gracefully handle API errors like rate limiting or invalid models.

```python
import streamlit as st
import os
import google.generativeai as genai
from google.api_core import exceptions
from youtube_transcript_api import YouTubeTranscriptApi
import whisper
import tempfile
```

### API Configuration

The Google Gemini API is configured immediately with the API key.

```python
genai.configure(api_key="YOUR_API_KEY_HERE")
```

### `get_youtube_transcript(youtube_url)`

*   **Purpose**: To fetch the transcript of a YouTube video given its URL.
*   **Logic**:
    1.  It extracts the unique `video_id` from the URL string. The logic `split("v=")[1].split("&")[0]` is robust, correctly handling both clean URLs and URLs with additional parameters.
    2.  It calls `YouTubeTranscriptApi.get_transcript(video_id)` to retrieve a list of transcript dictionaries.
    3.  It joins the `text` from each dictionary into a single, continuous string, which is then returned.
    4.  A `try...except` block wraps the logic to catch any errors during the API call (e.g., video not found, transcripts disabled) and displays an error in the Streamlit UI.

### `transcribe_video_file(uploaded_file)`

*   **Purpose**: To generate a transcript from a video file uploaded by the user.
*   **Logic**:
    1.  It uses `tempfile.NamedTemporaryFile` to create a secure, temporary file on the system. This is a best practice that avoids cluttering the project directory and ensures automatic cleanup.
    2.  The content of the uploaded video is written to this temporary file.
    3.  `whisper.load_model("base")` loads the Whisper speech-to-text model. The "base" model is chosen as a good balance between speed and accuracy. The first time this runs, it will download the model files.
    4.  `model.transcribe(video_path)` runs the transcription process on the temporary video file.
    5.  The temporary file is deleted using `os.remove()`.
    6.  The extracted `text` from the transcription result is returned.
    7.  Crucially, it includes specific error handling for `FileNotFoundError`, which occurs if **FFmpeg** is not installed, guiding the user with a clear, actionable error message.

### `generate_gemini_response(transcript, prompt)`

*   **Purpose**: To generate a response from the Gemini LLM based on the video transcript and a user's question.
*   **Logic**:
    1.  It initializes the Gemini model using `genai.GenerativeModel("gemini-1.5-flash")`.
    2.  It constructs a detailed `final_prompt`. This is a key part of the RAG technique. It explicitly tells the LLM its role ("You are a helpful assistant..."), provides the full video transcript as context, and then appends the user's specific question.
    3.  The `try...except` block robustly handles potential API errors:
        *   `exceptions.NotFound`: Catches errors if the model name is wrong.
        *   `exceptions.ResourceExhausted`: Catches rate limit and quota errors.
        *   `Exception`: A general catch-all for any other unexpected issues.
    4.  If successful, it returns the `text` part of the response from the model.

### Streamlit UI and Session State
\
*   **`st.set_page_config(...)`**: Sets the title and layout for the web page.
*   **Session State (`st.session_state`)**: This is a critical Streamlit feature used to maintain variables across user interactions.
    *   `chat_history`: A list that stores the conversation turns (user questions and assistant answers). This allows the chat to be redrawn every time the user interacts with the app.
    *   `transcript`: Stores the extracted video transcript so it doesn't have to be processed again every time the user asks a new question.

### Main Application Flow

The final part of the script handles the user interface and interaction logic:

1.  A sidebar is created with a radio button to select the input method ("YouTube Link" or "Upload Video File").
2.  Based on the user's choice, it displays either a text input box for the URL or a file uploader.
3.  Each input method has its own button ("Get Transcript" or "Transcribe Video"). When clicked, the corresponding function (`get_youtube_transcript` or `transcribe_video_file`) is called, and the result is saved to `st.session_state.transcript`. A spinner provides visual feedback during this process.
4.  If a transcript exists in the session state, it is displayed in an expandable `st.expander` box.
5.  The chat history is displayed by iterating through `st.session_state.chat_history`.
6.  `st.chat_input(...)` creates the text box for the user to ask questions.
7.  When a user submits a question, the script appends the question to the chat history, calls `generate_gemini_response()`, and if a valid response is received, appends the assistant's answer to the history as well. The app then automatically reruns, redrawing the chat with the new messages. 
