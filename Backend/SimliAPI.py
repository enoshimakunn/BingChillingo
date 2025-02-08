import requests
import base64

class SimliAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.simli.ai"
        self.headers = {"api-key": self.api_key}

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

        with open(audio_path, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode("utf-8")

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