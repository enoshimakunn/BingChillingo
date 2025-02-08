import sys
import os
import io
import json

import streamlit as st
import pandas as pd

from streamlit_elements import elements, dashboard


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
if "assessment" not in st.session_state: st.session_state['assessment'] = []


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
            for data in st.session_state['assessment']:
                if st.button(f"Assessment {st.session_state['assessment'].index(data) + 1}"):
                    with elements(f"Assessment {st.session_state['assessment'].index(data) + 1}"):
                        
                        layout = [
                            # First row - two charts
                            dashboard.Item("accuracy_chart", 0, 0, 6, 4),  # First chart, left half
                            dashboard.Item("fluency_chart", 6, 0, 6, 4),   # Second chart, right half
                            
                            # Second row - two charts
                            dashboard.Item("completeness_chart", 0, 4, 6, 4),  # Third chart, left half
                            dashboard.Item("prosody_chart", 6, 4, 6, 4),       # Fourth chart, right half
                            
                            # Third row - one centered chart
                            dashboard.Item("pronunciation_chart", 3, 8, 6, 4),  # Fifth chart, centered
                        ]
                        
                        with dashboard.Grid(layout):
                            with elements("accuracy_chart"):
                                st.plotly_chart(create_gauge_chart(
                                    data['NBest'][0]['PronunciationAssessment']['AccuracyScore'], 
                                    "Accuracy Score"
                                ), use_container_width=True)
                            
                            with elements("fluency_chart"):
                                st.plotly_chart(create_gauge_chart(
                                    data['NBest'][0]['PronunciationAssessment']['FluencyScore'], 
                                    "Fluency Score"
                                ), use_container_width=True)
                            
                            # Second row
                            with elements("completeness_chart"):
                                st.plotly_chart(create_gauge_chart(
                                    data['NBest'][0]['PronunciationAssessment']['CompletenessScore'], 
                                    "Completeness Score"
                                ), use_container_width=True)
                            
                            with elements("prosody_chart"):
                                st.plotly_chart(create_gauge_chart(
                                    data['NBest'][0]['PronunciationAssessment']['ProsodyScore'], 
                                    "Prosody Score"
                                ), use_container_width=True)
                            
                            # Third row
                            with elements("pronunciation_chart"):
                                st.plotly_chart(create_gauge_chart(
                                    data['NBest'][0]['PronunciationAssessment']['PronScore'], 
                                    "Pronunciation Score"
                                ), use_container_width=True)
                    
    
    # Transcript section at the bottom
    st.header("Transcript")
    with st.container():
        st.text_area("Video Transcript", value='\n'.join(st.session_state['transcript']), height=200, disabled=True)

def main():
    create_layout()
    
if __name__ == "__main__":
    main()