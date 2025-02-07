import os
import sys

from elevenlabs import ElevenLabs

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Env import XI_API_KEY


class PostVoice:
    def __init__(self, api_key: str):
        self.xi_api_key = api_key
        
    def post(self, audio_path: str, voice_name: str):
        client = ElevenLabs(api_key=self.xi_api_key)
        response = client.voices.add(
            name=voice_name,
            files=[open(audio_path, "rb")]
        )
        
        return response
        
class GenSpeech:
    def __init__(self, api_key: str):
        self.xi_api_key = api_key
        
    def generate(self, text: str, voice_id: str, out_path: str):
        client = ElevenLabs(api_key=self.xi_api_key)
        response = client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
        )
        
        with open(out_path, 'wb') as mp3_file:
            for chunk in response:
                mp3_file.write(chunk)
        

if __name__ == "__main__":
    post = PostVoice(XI_API_KEY)
    get = GenSpeech(XI_API_KEY)
    # post.post("Samples/Carnegie Mellon University.wav", "dumbass")
    get.generate("你好", "KYKd9of0fJ9XG7bcwvmD", "Samples/test.mp3")
    