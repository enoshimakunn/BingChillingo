import streamlit as st
import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Backend.Speech import ASR

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
        st.video("https://example.com/sample-video.mp4")
        
        # Video controls
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Previous")
        with col2:
            st.button("Play/Pause")
        with col3:
            st.button("Next")
    
    with right_col:
        st.header("Commentary")
        # Add comments section
        with st.container():
            st.text_input("Add a comment...")
            
            # Example comments
            comments = [
                {"user": "John", "text": "Great explanation at 2:15"},
                {"user": "Sarah", "text": "Could you clarify the concept at 3:45?"}
            ]
            
            for comment in comments:
                with st.container():
                    st.markdown(f"**{comment['user']}**")
                    st.write(comment['text'])
                    st.button("Reply", key=f"reply_{comment['user']}")
    
    # Transcript section at the bottom
    st.header("Transcript")
    with st.container():
        transcript_text = """
        This is a sample transcript of the video content.
        You can replace this with actual transcript data.
        The transcript can be synchronized with the video playback.
        """
        st.text_area("Video Transcript", value=transcript_text, height=200, disabled=True)

def main():
    create_layout()
    
if __name__ == "__main__":
    main()