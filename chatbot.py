import streamlit as st
import requests
import json
from PyPDF2 import PdfReader
from docx import Document
from elevenlabs import ElevenLabs
import pygame
import tempfile

# Define the Chatbot API URL and headers
api_url = "https://llm.kindo.ai/v1/chat/completions"
headers = {
    "api-key": "09e75bff-6192-436d-936e-2d0f9230a3a6-a896f6311e363485",  # Replace with your API key
    "content-type": "application/json"
}

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key="ae38aba75e228787e91ac4991fc771f8")  # Replace with your ElevenLabs API key

# Function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from Word file
def extract_text_from_word(file):
    doc = Document(file)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text

# Function to query the Chatbot API
def ask_question(question, context, model_name="azure/gpt-4o"):
    messages = [
        {"role": "system", "content": "You are Navin Kale, the co-founder of Swayam Talks. Answer in short paragraphs, not more than 100 words."},
        {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
    ]
    
    data = {
        "model": model_name,
        "messages": messages
    }
    
    response = requests.post(api_url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', "").strip()
    else:
        st.error(f"API request failed with status code {response.status_code}")
        return None

# Function to play audio using pygame
def play_audio_stream(audio_stream):
    pygame.mixer.init()
    
    # Save audio stream to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        for chunk in audio_stream:
            temp_audio.write(chunk)
        temp_audio_name = temp_audio.name

    # Load and play the audio file
    pygame.mixer.music.load(temp_audio_name)
    pygame.mixer.music.play()
    
    # Wait until the audio is finished
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# Function to convert text to speech
def text_to_speech(text, voice_id="voice_id"):
    try:
        audio_stream = elevenlabs_client.text_to_speech.convert_as_stream(
            voice_id=voice_id,
            text=text
        )
        play_audio_stream(audio_stream)
    except Exception as e:
        st.error(f"Text-to-speech conversion failed: {e}")

# Streamlit app
def main():
    st.title("Document-based Chatbot with Real-Time TTS")

    # Initialize session state for Q&A history
    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []
    
    # File upload
    uploaded_file = st.file_uploader("Upload a PDF or Word file", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        # Extract text based on file type
        if uploaded_file.type == "application/pdf":
            context = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            context = extract_text_from_word(uploaded_file)
        else:
            st.error("Unsupported file type")
            return
        
        st.write("File uploaded successfully. You can now ask questions based on the content.")
        
        # Input for questions
        question = st.text_input("Ask a question:")
        if question:
            # Get the answer from the API
            answer = ask_question(question, context, model_name="azure/gpt-4o")
            if answer:
                # Add question and answer to session state
                st.session_state.qa_history.append((question, answer))
                
                # Convert answer to speech
                text_to_speech(answer, voice_id="ersxGpVMrHVtVO398Vc5")  # Replace with your ElevenLabs voice ID

        # Display Q&A history
        if st.session_state.qa_history:
            st.write("### Question-Answer History:")
            for i, (q, a) in enumerate(st.session_state.qa_history, 1):
                with st.expander(f"Q{i}: {q}"):
                    st.write(a)

if __name__ == "__main__":
    main()
