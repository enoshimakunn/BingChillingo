import os
import sys

import azure.cognitiveservices.speech as speechsdk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Env import AZURE_ASR_KEY, AZURE_ASR_REGION
from Backend.Store import Store


class ASR:
    def __init__(self, user_id: int = None):
        self.speech_config = speechsdk.SpeechConfig(subscription=AZURE_ASR_KEY, region=AZURE_ASR_REGION)
        self.speech_config.speech_recognition_language="zh-CN"
        
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config)
        self.user_id = user_id
        # self.store = Store() if user_id else None
        
        pronunciation_config = speechsdk.PronunciationAssessmentConfig( 
            reference_text="", 
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark, 
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme, 
            enable_miscue=False) 
        pronunciation_config.enable_prosody_assessment() 
        pronunciation_config.enable_content_assessment_with_topic("greeting")
        
        pronunciation_config.apply_to(self.speech_recognizer)
        
    def recognize_from_microphone(self):
        print("Speak into your microphone.")
        speech_recognition_result = self.speech_recognizer.recognize_once_async().get()
        pronunciation_assessment_result_json = speech_recognition_result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)

        print("JSON: {}".format(pronunciation_assessment_result_json))
        
        recognized_text = ""
        
        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = speech_recognition_result.text
            print("Recognized: {}".format(recognized_text))
<<<<<<< HEAD
            
            # Store in database if user_id is provided
            # if self.store and self.user_id:
            #     self.store.save_speech_record(self.user_id, recognized_text, confidence_score)
=======
>>>>>>> backend
                
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")
        
        return [recognized_text, pronunciation_assessment_result_json]

    # def __del__(self):
    #     if self.store:
    #         self.store.close()


if __name__ == "__main__":
    # Create a test user
<<<<<<< HEAD
    # store = Store()
    # user_id = store.get_or_create_user('test_user', 'test@example.com')
    # store.close()
=======
    store = Store()
    user_id = store.get_or_create_user('test_user', 'test@example.com', language_level='1')
    store.close()
>>>>>>> backend

    # Test speech recognition
    # asr = ASR(user_id=user_id)
    asr = ASR()
    asr.recognize_from_microphone()