import sys
import os
import io
import json

import streamlit as st
import pandas as pd

from streamlit_elements import elements, dashboard
import streamlit_authenticator as stauth

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Env import XI_API_KEY, SIMLI_API_KEY

from Backend.Speech import ASR
from Backend.Chatbot import ChatConversation
from Backend.VoiceCloning import GenSpeech, PostVoice
from Backend.SimliAPI import SimliAPI
from Frontend.analysis import *

import yaml
from yaml.loader import SafeLoader

from PIL import Image

with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)


levels = [
    "Unit 1.1 - Introduce Yourself",
    "Unit 1.2 - Basic Greetings",
    "Unit 1.3 - Talking About Your Hobbies",
    "Unit 1.4 - Describing Your Family",
    "Unit 1.5 - Daily Routines",
    "Unit 1.6 - Asking for Directions",
    "Unit 1.7 - Ordering Food at a Restaurant",
    "Unit 1.8 - Talking About the Weather",
    "Unit 2.1 - Making Plans with Friends",
    "Unit 2.2 - Describing Your Job or Studies",
    "Unit 2.3 - Talking About Vacations",
    "Unit 2.4 - Expressing Opinions and Preferences",
    "Unit 2.5 - Shopping and Bargaining",
    "Unit 2.6 - Talking About Health and Fitness",
    "Unit 2.7 - Sharing Cultural Traditions",
    "Unit 2.8 - Writing Simple Emails or Messages",
    "Unit 3.1 - Giving a Presentation",
    "Unit 3.2 - Discussing Current Events",
    "Unit 3.3 - Talking About Technology Trends",
    "Unit 3.4 - Negotiating and Problem-Solving",
    "Unit 3.5 - Explaining Complex Ideas Simply",
    "Unit 3.6 - Debating Pros and Cons of a Topic",
    "Unit 3.7 - Preparing for an Interview",
    "Unit 3.8 - Reflecting on Personal Growth",
]


asr = ASR()
simli = SimliAPI(SIMLI_API_KEY)
tts = GenSpeech(XI_API_KEY)

if "conversation" not in st.session_state: st.session_state['conversation'] = ChatConversation(rounds=2, vocab=["你好", "再见", "谢谢"])
if "rounds" not in st.session_state: st.session_state['rounds'] = 0
if "transcript" not in st.session_state: st.session_state['transcript'] = []
# if "assessment" not in st.session_state: st.session_state['assessment'] = [json.load(open('test.json', 'r'))]
if "assessment" not in st.session_state: st.session_state['assessment'] = []
if "current_level" not in st.session_state: st.session_state['current_level'] = "Dashboard"
if "image_file" not in st.session_state: st.session_state["image_file"] = None
if "audio_file" not in st.session_state: st.session_state["audio_file"] = None


def empty_state():
    st.session_state['conversation'] = ChatConversation(rounds=2, vocab=["你好", "再见", "谢谢"])
    st.session_state['rounds'] = 0
    st.session_state['transcript'] = []
    st.session_state['assessment'] = []


def chat_layout():    
    # Create the main layout
    center_col, right_col = st.columns([2, 1])

    with center_col:
        st.header("Video Content")
        # Video player placeholder
        # Note: Replace with actual video file or URL
        video_file = st.empty()
        # st.video("https://example.com/sample-video.mp4")

        if st.button(f"Click to speak"):
            stu_reply = asr.recognize_from_microphone()
            assessment = stu_reply[1]
            stu_reply = stu_reply[0]
            
            st.session_state['transcript'].append("User: " + stu_reply)
            st.session_state['conversation'].context.append("学生:" + stu_reply)
            
            if st.session_state['rounds'] < st.session_state['conversation'].rounds:
                sys_reply = st.session_state['conversation'].respond()
                st.session_state['conversation'].context.append("老师:" + sys_reply)
                st.session_state['transcript'].append("System: " + sys_reply)
                
                st.session_state["rounds"] += 1
                st.session_state["assessment"].append(json.loads(assessment))
                    
            elif st.session_state['rounds'] == st.session_state['conversation'].rounds:
                sys_reply = st.session_state['conversation'].respond(if_end=True)
                st.session_state['conversation'].context.append("老师:" + sys_reply)
                st.session_state['transcript'].append("System: " + sys_reply)
            
            if not os.path.exists("Samples"):
                os.mkdir("Samples")

            tts.generate(sys_reply, out_path="Samples/test.mp3")
            url = simli.audio_to_video(
                "679fc967-ae0c-4824-a426-03eea6161c72", "Samples/test.mp3"
            )["mp4_url"]
            st.video(url, autoplay=True)
            
            if st.session_state['rounds'] == st.session_state['conversation'].rounds:
                assess = st.session_state['conversation'].assess(st.session_state['assessment'])
                feedback(assess)
                empty_state()

            

    with right_col:
        st.header("Assessment")
        # Add comments section
        with st.container():
            if len(st.session_state['assessment']) > 0:
                tabs = st.tabs([f"Assessment {idx + 1}" for idx in range(len(st.session_state['assessment']))])
                
                for idx, (tab, data) in enumerate(zip(tabs, st.session_state['assessment'])):
                    with tab:
                        with elements(f"assessment_{idx}"):  # Unique key for each assessment
                            d = [
                                {
                                    "Score": "Accuracy",
                                    f"Assessment {idx + 1}": data['NBest'][0]['PronunciationAssessment']['AccuracyScore'],
                                },
                                {
                                    "Score": "Fluency",
                                    f"Assessment {idx + 1}": data['NBest'][0]['PronunciationAssessment']['FluencyScore'],
                                },
                                {
                                    "Score": "Completeness",
                                    f"Assessment {idx + 1}": data['NBest'][0]['PronunciationAssessment']['CompletenessScore'],
                                },
                                {
                                    "Score": "Prosody",
                                    f"Assessment {idx + 1}": data['NBest'][0]['PronunciationAssessment']['ProsodyScore'],
                                },
                                {
                                    "Score": "Pronunciation",
                                    f"Assessment {idx + 1}": data['NBest'][0]['PronunciationAssessment']['PronScore'],
                                }
                            ]
                            
                            render_radar_chart(data=d, assessment_index=idx)

    # Transcript section at the bottom
    st.header("Transcript")
    with st.container():
        st.text_area(
            "Video Transcript",
            value="\n".join(st.session_state["transcript"]),
            height=200,
            disabled=True,
        )


def upload_and_display_image():

    # Allow the user to upload a file (only jpg, jpeg, png are allowed)
    image_file = st.file_uploader("Choose an image for your avatar...", type=["jpg", "jpeg", "png"])

    if image_file is not None:
        st.session_state["image_file"] = image_file
    
    if st.session_state["image_file"] is not None:
        # Open the image file using Pillow (PIL)
        image = Image.open(st.session_state["image_file"])
        # Display the image with an optional caption and automatic width scaling
        st.image(image, caption="Uploaded Image", width=300)


def upload_and_play_audio():
    
    # Allow the user to upload an audio file (only mp3, wav, ogg are allowed)
    audio_file = st.file_uploader("Choose an audio sample for your voice...", type=["mp3", "wav", "ogg"])

    if audio_file is not None:
        st.session_state["audio_file"] = audio_file
    
    if st.session_state["audio_file"] is not None:
        # Play the uploaded audio file
        st.audio(audio_file)


def dashboard():
    st.title("Bing Chillingo")
    st.write(f'Welcome *{st.session_state["name"]}*')

    upload_and_display_image()
    upload_and_play_audio()


def level_selector(user_level=5):
    for idx, level in enumerate(levels):
        if st.sidebar.button(
            level, type="primary" if idx <= user_level else "secondary",
            use_container_width=True
        ):
            st.session_state["current_level"] = level

    st.write("Current Level:", st.session_state["current_level"])


def create_layout():
    # Set page config to wide mode
    st.set_page_config(layout="wide")

    authenticator = stauth.Authenticate(config["credentials"])

    try:
        authenticator.login("sidebar")
    except Exception as e:
        st.error(e)

    with st.sidebar:
        if st.session_state["authentication_status"]:
            st.title("Bing Chillingo")
            if st.button("Dashboard", type="secondary"):
                st.session_state["current_level"] = "Dashboard"
            st.write(f'Welcome *{st.session_state["name"]}*')
            level_selector()
        elif st.session_state["authentication_status"] is False:
            st.error("Username/password is incorrect")
        elif st.session_state["authentication_status"] is None:
            st.warning("Please enter your username and password")

    if st.session_state["current_level"] == "Dashboard":
        dashboard()
    else:
        st.title(st.session_state["current_level"])
        chat_layout()

    with st.sidebar:
        authenticator.logout()


def main():
    create_layout()


if __name__ == "__main__":
    main()
