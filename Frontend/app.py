import sys
import os
import io
import json

import streamlit as st
import pandas as pd

from streamlit_elements import elements, mui, nivo


from Env import XI_API_KEY, SIMLI_API_KEY

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Backend.Speech import ASR
from Backend.Chatbot import ChatConversation
from Backend.VoiceCloning import GenSpeech, PostVoice
from Backend.SimliAPI import SimliAPI
from Frontend.analysis import *


asr = ASR()
simli = SimliAPI(SIMLI_API_KEY)
tts = GenSpeech(XI_API_KEY)

if "conversation" not in st.session_state: st.session_state['conversation'] = ChatConversation(vocab=["你好", "再见", "谢谢"])
if "rounds" not in st.session_state: st.session_state['rounds'] = 0
if "transcript" not in st.session_state: st.session_state['transcript'] = []
if "assessment" not in st.session_state: st.session_state['assessment'] = [json.load(open('test.json', 'r'))]

def create_layout():    
    # Set page config to wide mode
    st.set_page_config(layout="wide")
    
    # Add title
    st.title("Video Learning Dashboard")
    
    # Create the main layout
    left_col, center_col, right_col = st.columns([1, 2, 1])
    
    with left_col:
        st.header("Learning Progress")
        # Progress bar
        progress = st.progress(0)
        
        # Example metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Videos Completed", value="3/10")
        with col2:
            st.metric(label="Time Spent", value="45 min")
            
        # Progress details
        with st.expander("Detailed Progress"):
            progress_data = pd.DataFrame({
                'Module': ['Intro', 'Basics', 'Advanced'],
                'Status': ['Completed', 'In Progress', 'Not Started']
            })
            st.dataframe(progress_data)
    
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
                    
            elif st.session_state['rounds'] == st.session_state['conversation'].rounds:
                sys_reply = st.session_state['conversation'].respond(if_end=True)
                st.session_state['conversation'].context.append("老师:" + sys_reply)
                st.session_state['transcript'].append("System: " + sys_reply)
                st.session_state['rounds'] = 0
            
            tts.generate(sys_reply, out_path="Samples/test.mp3")
            url = simli.audio_to_video("679fc967-ae0c-4824-a426-03eea6161c72", "Samples/test.mp3")["mp4_url"]
            st.video(url, autoplay=True)
            
            st.session_state['rounds'] += 1
            st.session_state['assessment'].append(json.loads(assessment))
        
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
        st.text_area("Video Transcript", value='\n'.join(st.session_state['transcript']), height=200, disabled=True)

def main():
    create_layout()
    
if __name__ == "__main__":
    main()