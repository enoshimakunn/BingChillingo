import os
import sys
import psycopg2

import azure.cognitiveservices.speech as speechsdk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Env import AZURE_ASR_KEY, AZURE_ASR_REGION, DATABASE_URL


class ASR:
    def __init__(self, user_id: int = None):
        self.speech_config = speechsdk.SpeechConfig(subscription=AZURE_ASR_KEY, region=AZURE_ASR_REGION)
        self.speech_config.speech_recognition_language="zh-CN"
        
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config)
        self.user_id = user_id
        self.conn = psycopg2.connect(DATABASE_URL) if user_id else None
        
    def recognize_from_microphone(self):
        print("Speak into your microphone.")
        speech_recognition_result = self.speech_recognizer.recognize_once_async().get()
        
        recognized_text = ""
        confidence_score = 0.0
        
        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = speech_recognition_result.text
            confidence_score = 1.0  # Azure doesn't provide confidence scores directly
            print("Recognized: {}".format(recognized_text))
            
            # Store in database if user_id is provided
            if self.conn and self.user_id:
                with self.conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO speech_records (user_id, text, confidence_score)
                        VALUES (%s, %s, %s)
                    """, (self.user_id, recognized_text, confidence_score))
                    self.conn.commit()
                
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")
        
        return recognized_text

    def __del__(self):
        if self.conn:
            self.conn.close()

class Analytics:
    def __init__(self):
        pass
    
    def analyze(self):
        return NotImplementedError


if __name__ == "__main__":
    # Create a test user if needed
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username = 'test_user' LIMIT 1")
        user = cur.fetchone()
        if not user:
            cur.execute("""
                INSERT INTO users (username, email)
                VALUES ('test_user', 'test@example.com')
                RETURNING id
            """)
            user = cur.fetchone()
        user_id = user[0]
    conn.close()

    asr = ASR(user_id=user_id)
    asr.recognize_from_microphone()