import io
import base64
import time
import configparser
from pathlib import Path

import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components
from PIL import Image

config = configparser.ConfigParser()


def setup_config():
    config_path = Path('config.ini')
    if not config_path.exists():
        st.warning("Please set your Google API key in the config.ini file")
        return False
    else:
        config.read(config_path)
        api_key = config['API']['GOOGLE_API_KEY']
        return api_key


def configure_genai(api_key):
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0.4,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 4096,
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    return model


def analyze_image(model, image, question):
    try:
        response = model.generate_content([image, question])
        return response.text
    except Exception as e:
        return f"Error analyzing image: {str(e)}"


def speech_recognition_component():
    speech_js = """
    <div>
        <button id="start-button" style="background-color: #4CAF50; color: white; padding: 10px 24px; border: none; border-radius: 4px; cursor: pointer;">Start Listening</button>
        <button id="stop-button" style="background-color: #f44336; color: white; padding: 10px 24px; border: none; border-radius: 4px; cursor: pointer; display: none;">Stop</button>
        <p id="status">Click 'Start Listening' to activate speech recognition</p>
        <div id="result" style="margin-top: 10px; min-height: 20px;"></div>
    </div>

    <script>
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            document.getElementById('status').innerHTML = 'Speech recognition not supported in this browser. Try Chrome, Edge, or Safari.';
            document.getElementById('start-button').disabled = true;
        } else {
            const recognition = new SpeechRecognition();
            recognition.lang = 'en-US';
            recognition.continuous = true;
            recognition.interimResults = true;

            const startButton = document.getElementById('start-button');
            const stopButton = document.getElementById('stop-button');
            const statusElement = document.getElementById('status');
            const resultElement = document.getElementById('result');

            startButton.addEventListener('click', () => {
                recognition.start();
                startButton.style.display = 'none';
                stopButton.style.display = 'inline-block';
                statusElement.innerHTML = 'Listening...';
            });

            stopButton.addEventListener('click', () => {
                recognition.stop();
                stopButton.style.display = 'none';
                startButton.style.display = 'inline-block';
                statusElement.innerHTML = 'Stopped listening';
            });

            recognition.onresult = (event) => {
                let finalTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    }
                }

                if (finalTranscript) {
                    resultElement.innerHTML = finalTranscript;

                    window.parent.postMessage({
                        type: "streamlit:setComponentValue",
                        value: finalTranscript
                    }, "*");
                }
            };

            recognition.onerror = (event) => {
                statusElement.innerHTML = 'Error: ' + event.error;
                stopButton.style.display = 'none';
                startButton.style.display = 'inline-block';
            };
        }
    </script>
    """
    return components.html(speech_js, height=150)


def main():
    st.set_page_config(page_title="Real-Time Image Query Assistant", layout="wide")
    st.title("Real-Time Image Query Assistant")

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    if 'voice_text' not in st.session_state:
        st.session_state['voice_text'] = ""

    api_key = setup_config()
    if not api_key:
        st.stop()

    model = configure_genai(api_key)

    st.sidebar.title("Image Input")
    input_option = st.sidebar.radio("Select input method:", ["Upload Image", "Capture from Camera"])

    image_file = None
    if input_option == "Upload Image":
        image_file = st.sidebar.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    else:
        image_file = st.sidebar.camera_input("Take a picture")

    col1, col2 = st.columns([1, 1])

    gemini_image = None
    with col1:
        st.subheader("Image")
        if image_file:
            image = Image.open(image_file)
            st.image(image, use_container_width=True)

            if image.mode == 'RGBA':
                image = image.convert('RGB')

            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            image_bytes = buffered.getvalue()

            gemini_image = {"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode("utf-8")}

    with col2:
        st.subheader("Ask about the image")

        use_voice = st.checkbox("Enable voice input", value=True)

        if use_voice:
            st.write("Click 'Start Listening' and speak your question:")
            speech_text = speech_recognition_component()

            if speech_text:
                st.session_state['voice_text'] = speech_text

        question = st.text_input("Type your question or speak:",
                                 value=st.session_state['voice_text'],
                                 key="question-input")

        if st.session_state['voice_text'] and question == st.session_state['voice_text']:
            st.session_state['voice_text'] = ""

        send_button = st.button("Send")

        if send_button and question and image_file and gemini_image:
            with st.spinner("Analyzing image..."):
                st.session_state['chat_history'].append({"role": "user", "content": question})

                try:
                    answer = analyze_image(model, gemini_image, question)

                    st.session_state['chat_history'].append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")

        st.subheader("Conversation")
        chat_container = st.container()

        with chat_container:
            typing_enabled = st.checkbox("Show real-time typing", value=True, key="typing_global")

            for chat in st.session_state['chat_history']:
                if chat["role"] == "user":
                    st.markdown(f"**You:** {chat['content']}")
                else:
                    message_placeholder = st.empty()
                    full_response = chat["content"]

                    if typing_enabled:
                        simulated_response = ""
                        for char in full_response:
                            simulated_response += char
                            message_placeholder.markdown(f"**Assistant:** {simulated_response}▌")
                            time.sleep(0.01)
                        message_placeholder.markdown(f"**Assistant:** {full_response}")
                    else:
                        st.markdown(f"**Assistant:** {full_response}")


if __name__ == "__main__":
    main()