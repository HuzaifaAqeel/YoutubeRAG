def get_youtube_transcript(youtube_url, st, YouTubeTranscriptApi):
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