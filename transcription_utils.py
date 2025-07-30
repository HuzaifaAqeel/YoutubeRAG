def transcribe_video_file(uploaded_file, st, whisper, tempfile, os):
    """
    Transcribes an uploaded video file using Whisper.
    """
    try:
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp:
            temp.write(uploaded_file.getbuffer())
            video_path = temp.name
        
        # Load whisper model
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