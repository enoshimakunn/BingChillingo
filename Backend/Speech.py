import os
import sys

import azure.cognitiveservices.speech as speechsdk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Env import AZURE_ASR_KEY, AZURE_ASR_REGION


class ASR:
    def __init__(self):
        self.speech_config = speechsdk.SpeechConfig(subscription=AZURE_ASR_KEY, region=AZURE_ASR_REGION)
        self.speech_config.speech_recognition_language="zh-CN"
        
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config)
        
    def recognize_from_microphone(self):
        print("Speak into your microphone.")
        speech_recognition_result = self.speech_recognizer.recognize_once_async().get()
        
        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized: {}".format(speech_recognition_result.text))
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")
        
        return speech_recognition_result.text
    
class Analytics:
    def __init__(self):
        pass
    
    def analyze(self):
        return NotImplementedError


if __name__ == "__main__":
    asr = ASR()
    asr.recognize_from_microphone()