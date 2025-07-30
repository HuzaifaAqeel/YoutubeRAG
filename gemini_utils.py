def generate_gemini_response(transcript, prompt, genai, st, exceptions):
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