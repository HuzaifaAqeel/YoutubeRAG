import streamlit as st
import os
import google.generativeai as genai
from google.api_core import exceptions
from youtube_transcript_api import YouTubeTranscriptApi
import whisper
import tempfile

from youtube_utils import get_youtube_transcript
from transcription_utils import transcribe_video_file
from gemini_utils import generate_gemini_response

# Configure Google Gemini API
genai.configure(api_key="AIzaSyDKw7kpq842fo6QZMbOH4PXYtLV7wnK5x8")

# Function to get transcript from YouTube link
def get_youtube_transcript(youtube_url):
    """
    Retrieves the transcript of a YouTube video from its URL.
    """
    try:
        video_id = youtube_url.split("v=")[1].split("&")[0]
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([d['text'] for d in transcript_list])
        return transcript
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None

# Function to transcribe an uploaded video file
def transcribe_video_file(uploaded_file):
    """
    Transcribes an uploaded video file using Whisper.
    """
    try:
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp:
            temp.write(uploaded_file.getbuffer())
            video_path = temp.name
        
        # Load whisper model
        # The first time this is run, it will download the model.
        model = whisper.load_model("base")
        
        # Transcribe
        result = model.transcribe(video_path)
        
        # Clean up temporary file
        os.remove(video_path)
        
        return result["text"]
    except FileNotFoundError:
        st.error("Error transcribing video: FFmpeg not found.")
        st.info("The video upload feature requires FFmpeg to be installed on your system. Please install it and ensure it is available in your system's PATH.")
        st.info("On Windows, you can use a package manager like Chocolatey (`choco install ffmpeg`) or download it from the official ffmpeg.org website.")
        return None
    except Exception as e:
        st.error(f"Error transcribing video: {e}")
        return None


# Function to generate content using Gemini
def generate_gemini_response(transcript, prompt):
    """
    Generates a response from Gemini based on the transcript and a prompt.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    final_prompt = f"""
    You are a helpful assistant that answers questions based on the provided video transcript.
    Here is the transcript:
    ---
    {transcript}
    ---
    Based on this transcript, please answer the following question:
    {prompt}
    """
    
    try:
        response = model.generate_content(final_prompt)
        return response.text
    except exceptions.NotFound as e:
        st.error("The specified model was not found. Please check the model name in the code and your API key's access permissions.")
        return None
    except exceptions.ResourceExhausted as e:
        st.error("API Rate Limit Exceeded. Please check your Google Cloud project quota and billing settings.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None


# Streamlit App
st.set_page_config(page_title="YouTube RAG System", layout="wide")
st.title("YouTube Video RAG System")
st.write("Ask questions about a YouTube video using its link or by uploading a video file.")

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'transcript' not in st.session_state:
    st.session_state['transcript'] = ""

# Input options
st.sidebar.header("Input Options")
input_option = st.sidebar.radio("Choose an input method:", ("YouTube Link", "Upload Video File"))

if input_option == "YouTube Link":
    youtube_link = st.sidebar.text_input("Enter YouTube Video Link:")
    if st.sidebar.button("Get Transcript"):
        if youtube_link:
            with st.spinner("Fetching transcript..."):
                transcript = get_youtube_transcript(youtube_link)
                if transcript:
                    st.session_state.transcript = transcript
                    st.success("Transcript loaded!")
        else:
            st.sidebar.warning("Please enter a YouTube link.")

elif input_option == "Upload Video File":
    uploaded_file = st.sidebar.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])
    if st.sidebar.button("Transcribe Video"):
        if uploaded_file is not None:
            with st.spinner("Transcribing video... This may take a while."):
                transcript = transcribe_video_file(uploaded_file)
                if transcript:
                    st.session_state.transcript = transcript
                    st.success("Video transcribed!")
        else:
            st.sidebar.warning("Please upload a video file.")

# Display Transcript
if st.session_state.transcript:
    with st.expander("Show Transcript"):
        st.write(st.session_state.transcript)

# Chat Interface
st.header("Chat with the Video")

for role, text in st.session_state.chat_history:
    st.chat_message(role).write(text)

user_prompt = st.chat_input("Ask a question about the video...")

if user_prompt:
    if st.session_state.transcript:
        st.session_state.chat_history.append(("user", user_prompt))
        st.chat_message("user").write(user_prompt)
        
        with st.spinner("Thinking..."):
            response = generate_gemini_response(st.session_state.transcript, user_prompt)
            if response:
                st.session_state.chat_history.append(("assistant", response))
                st.chat_message("assistant").write(response)
    else:
        st.warning("Please provide a video transcript first.") 