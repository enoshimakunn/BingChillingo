import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from Backend.Speech import ASR
from Backend.Chatbot import Chat
from Backend.SadTalker.SadTalker import SadTalker

sadtalker = SadTalker(checkpoint_dir='./checkpoints', result_dir='./results', device='cpu')

input_image = "./examples/source_image/full_body_1.png" #TODO
input_audio = "./examples/driven_audio/bus_chinese.wav" #TODO

output_video = sadtalker.generate_video(
    source_image=input_image,
    driven_audio=input_audio,
    pose_style=0,
    batch_size=1,
    size=256,
    enhancer="gfpgan",
    still_mode=False,
    ref_eyeblink=None,  
    ref_pose=None,
    input_yaw=[-15, 0, 15], 
    input_pitch=[0, 5, -5],  
    input_roll=[0, 3, -3], 
    verbose=True
)

print(f"Generated video saved at: {output_video}")