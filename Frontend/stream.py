import streamlit as st
import cv2
import numpy as np
import time
import threading
import queue
from PIL import Image
import io
import base64
import html

class VideoGenerationStreamer:
    def __init__(self):
        self.frame_queue = queue.Queue()
        self.is_generating = False
        self.current_frame = 0
        
    def mock_generate_frame(self, prompt, frame_number):
        """
        Mock video generation - replace this with your actual video generation model
        In reality, this would call your video generation model's function
        """
        # Create a simple animation as a placeholder
        image = np.zeros((256, 256, 3), dtype=np.uint8)
        center = (128, 128)
        radius = int(20 + 10 * np.sin(frame_number * 0.1))
        color = ((frame_number * 2) % 255, (frame_number * 3) % 255, (frame_number * 5) % 255)
        cv2.circle(image, center, radius, color, -1)
        
        # Add frame number and prompt text
        cv2.putText(image, f"Frame {frame_number}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(image, f"Prompt: {prompt[:20]}...", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return image

    def generate_video_frames(self, prompt, total_frames):
        """
        Generate video frames and put them in the queue
        """
        self.is_generating = True
        self.current_frame = 0
        
        try:
            while self.current_frame < total_frames and self.is_generating:
                # Generate frame - replace mock_generate_frame with your model's generation
                frame = self.mock_generate_frame(prompt, self.current_frame)
                
                # Convert to RGB format
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Put frame in queue
                self.frame_queue.put(frame_rgb)
                
                self.current_frame += 1
                
                # Simulate generation time
                time.sleep(0.1)  # Remove this in actual implementation
                
        except Exception as e:
            st.error(f"Error generating frames: {str(e)}")
        finally:
            self.is_generating = False

    def start_generation(self, prompt, total_frames):
        """
        Start video generation in a separate thread
        """
        generation_thread = threading.Thread(
            target=self.generate_video_frames,
            args=(prompt, total_frames)
        )
        generation_thread.start()
        return generation_thread

    def stop_generation(self):
        """
        Stop video generation
        """
        self.is_generating = False

def create_video_player_html(frame):
    """
    Create HTML for displaying the video frame
    """
    # Convert frame to base64
    im = Image.fromarray(frame)
    buffer = io.BytesIO()
    im.save(buffer, format="JPEG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # Create HTML with styling
    html_code = f"""
        <div style="display: flex; justify-content: center; align-items: center;">
            <img src="data:image/jpeg;base64,{img_str}" 
                 style="max-width: 100%; height: auto; border: 2px solid #ccc; border-radius: 5px;">
        </div>
    """
    return html_code

def main():
    st.title("Real-time Video Generation Streaming")
    
    # Initialize session state
    if 'streamer' not in st.session_state:
        st.session_state.streamer = VideoGenerationStreamer()
    
    # Input parameters
    prompt = st.text_input("Enter generation prompt:", "A dancing robot")
    total_frames = st.slider("Number of frames to generate:", 10, 100, 30)
    
    # Control columns
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start Generation"):
            if not st.session_state.streamer.is_generating:
                # Clear any existing frames
                while not st.session_state.streamer.frame_queue.empty():
                    st.session_state.streamer.frame_queue.get()
                
                # Start generation
                st.session_state.streamer.start_generation(prompt, total_frames)
    
    with col2:
        if st.button("Stop Generation"):
            st.session_state.streamer.stop_generation()
    
    # Progress bar
    progress_bar = st.progress(0)
    
    # Frame display
    frame_placeholder = st.empty()
    
    # Statistics
    stats_placeholder = st.empty()
    
    # Display frames as they're generated
    while st.session_state.streamer.is_generating or not st.session_state.streamer.frame_queue.empty():
        try:
            # Get frame from queue with timeout
            frame = st.session_state.streamer.frame_queue.get(timeout=1)
            
            # Update progress
            progress = min(1.0, st.session_state.streamer.current_frame / total_frames)
            progress_bar.progress(progress)
            
            # Display frame
            frame_placeholder.markdown(
                create_video_player_html(frame),
                unsafe_allow_html=True
            )
            
            # Update statistics
            stats_placeholder.write({
                "Frames Generated": st.session_state.streamer.current_frame,
                "Frames Remaining": total_frames - st.session_state.streamer.current_frame,
                "Generation Active": st.session_state.streamer.is_generating
            })
            
            # Small delay to prevent overwhelming the UI
            time.sleep(0.1)
            
        except queue.Empty:
            continue
        except Exception as e:
            st.error(f"Error displaying frame: {str(e)}")
            break

if __name__ == "__main__":
    main()