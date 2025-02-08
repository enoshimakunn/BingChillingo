import requests
import base64
import os
import sys

from pydub import AudioSegment

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Env import SIMLI_API_KEY

class SimliAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.simli.ai"
        self.headers = {"api-key": self.api_key}

    def encode_audio_to_base64(self, audio_path):
        with open(audio_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode("utf-8")

    def convert_audio(self, audio_path, target_sample_rate=16000, target_channels=1):
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_frame_rate(target_sample_rate).set_channels(target_channels)
        converted_path = "output_audio.wav"
        audio.export(converted_path, format="wav")
        return converted_path

    def generate_face_id(self, image_path, face_name="untitled_avatar"):
        url = f"{self.base_url}/generateFaceID"
        files = {"image": open(image_path, "rb")}
        data = {"face_name": face_name}
        headers = {"api-key": self.api_key}

        response = requests.post(url, headers=headers, files=files, data=data)
        response_data = response.json()

        if "faceId" in response_data:
            return response_data["faceId"]
        else:
            raise ValueError(f"Failed to generate Face ID: {response_data}")

    def audio_to_video(self, face_id, audio_path, audio_format="pcm16", sample_rate=16000, channel_count=1, video_start_frame=0): 
        url = f"{self.base_url}/audioToVideoStream"

        processed_audio = self.convert_audio(audio_path)    
        audio_base64 = self.encode_audio_to_base64(processed_audio)

        payload = {
            "simliAPIKey": self.api_key,
            "faceId": face_id,
            "audioBase64": audio_base64,
            "audioFormat": audio_format,
            "audioSampleRate": sample_rate,
            "audioChannelCount": channel_count,
            "videoStartingFrame": video_start_frame
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)

        return response.json()
    
if __name__ == "__main__":
    api = SimliAPI(SIMLI_API_KEY)
    image_path = "Samples/1.jpg"
    face_id = api.generate_face_id(image_path)

    print(f"API Response: {face_id}")