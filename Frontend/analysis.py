import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from streamlit_elements import nivo, mui

def load_pronunciation_data(json_data):
    """Parse the JSON data and extract relevant metrics"""
    data = json.loads(json_data)
    assessment = data['NBest'][0]['PronunciationAssessment']
    words = data['NBest'][0]['Words'][0]
    phonemes = words['Phonemes']
    
    return {
        'display_text': data['DisplayText'],
        'scores': assessment,
        'phonemes': phonemes
    }

def create_gauge_chart(value, title):
    """Create a circular gauge chart for a score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 60], 'color': 'lightgray'},
                {'range': [60, 80], 'color': 'lightblue'},
                {'range': [80, 100], 'color': 'azure'}
            ],
        }
    ))
    
    fig.update_layout(
        height=250,
        font={'size': 16}
    )
    return fig

def create_phoneme_gauges(phonemes):
    """Create gauge charts for phoneme accuracy scores"""
    return [
        {
            'phoneme': p['Phoneme'],
            'accuracy': p['PronunciationAssessment']['AccuracyScore'],
            'duration': p['Duration'] / 1000000  # Convert to seconds
        }
        for p in phonemes
    ]
    
def render_radar_chart(data, assessment_index):
    """Render Nivo radar chart with consistent styling."""
    assessment_key = f"Assessment {assessment_index + 1}"
    
    with mui.Box(sx={"height": 500}):
        nivo.Radar(
            data=data,
            keys=[assessment_key],
            indexBy="Score",
            valueFormat=">-.2f",
            margin={
                "top": 70,
                "right": 80,
                "bottom": 40,
                "left": 80
            },
            borderColor={"from": "color"},
            gridLabelOffset=36,
            dotSize=10,
            dotColor={"theme": "background"},
            dotBorderWidth=2,
            motionConfig="wobbly",
            legends=[{
                "anchor": "top-right",
                "direction": "column",
                "translateX": -50,
                "translateY": -40,
                "itemWidth": 80,
                "itemHeight": 20,
                "itemTextColor": "#999",
                "symbolSize": 12,
                "symbolShape": "circle",
                "effects": [{
                    "on": "hover",
                    "style": {
                        "itemTextColor": "#000"
                    }
                }]
            }],
            theme={
                "background": "#FFFFFF",
                "textColor": "#31333F",
                "tooltip": {
                    "container": {
                        "background": "#FFFFFF",
                        "color": "#31333F",
                    }
                }
            }
        )

def main():
    st.set_page_config(layout="wide")
    st.title("Pronunciation Assessment Dashboard")
    
    # Sample JSON data
    json_data = """{"Id":"4f938d61d22a46018cf01346d8bdd41a","RecognitionStatus":"Success","Offset":5800000,"Duration":13100000,"Channel":0,"DisplayText":"你好吗？","SNR":35.06624,"NBest":[{"Confidence":0.8023237,"Lexical":"你好吗","ITN":"你好吗","MaskedITN":"你好吗","Display":"你好吗？","PronunciationAssessment":{"AccuracyScore":90.0,"FluencyScore":100.0,"ProsodyScore":0.0,"CompletenessScore":100.0,"PronScore":38.0},"Words":[{"Word":"你好吗","Offset":5800000,"Duration":13100000,"PronunciationAssessment":{"AccuracyScore":90.0,"ErrorType":"None","Feedback":{"Prosody":{"Break":{"ErrorTypes":["None"],"BreakLength":0},"Intonation":{"ErrorTypes":[],"Monotone":{"SyllablePitchDeltaConfidence":1.0}}}}},"Phonemes":[{"Phoneme":"ni 3","PronunciationAssessment":{"AccuracyScore":60.0},"Offset":5800000,"Duration":4500000},{"Phoneme":"hao 3","PronunciationAssessment":{"AccuracyScore":100.0},"Offset":10400000,"Duration":2100000},{"Phoneme":"ma 5","PronunciationAssessment":{"AccuracyScore":99.0},"Offset":12600000,"Duration":6300000}]}]}]}"""
    
    data = load_pronunciation_data(json_data)
    
    # Display the text being analyzed
    st.header("Analyzed Text")
    st.subheader(data['display_text'])
    
    # Display overall scores using gauge charts
    st.header("Overall Assessment Scores")
    
    # Create columns for the gauge charts
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.plotly_chart(create_gauge_chart(
            data['scores']['AccuracyScore'], 
            "Accuracy Score"
        ), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_gauge_chart(
            data['scores']['FluencyScore'], 
            "Fluency Score"
        ), use_container_width=True)
    
    with col3:
        st.plotly_chart(create_gauge_chart(
            data['scores']['CompletenessScore'], 
            "Completeness Score"
        ), use_container_width=True)
    
    # Additional scores in new row
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.plotly_chart(create_gauge_chart(
            data['scores']['ProsodyScore'], 
            "Prosody Score"
        ), use_container_width=True)
    
    with col5:
        st.plotly_chart(create_gauge_chart(
            38.0,  # PronScore from data
            "Pronunciation Score"
        ), use_container_width=True)
    
    # Phoneme Analysis
    st.header("Phoneme Analysis")
    phoneme_data = create_phoneme_gauges(data['phonemes'])
    
    # Create columns for phoneme gauges
    phoneme_cols = st.columns(len(phoneme_data))
    
    for idx, phoneme in enumerate(phoneme_data):
        with phoneme_cols[idx]:
            st.plotly_chart(create_gauge_chart(
                phoneme['accuracy'],
                f"'{phoneme['phoneme']}'"
            ), use_container_width=True)
            st.metric("Duration", f"{phoneme['duration']:.2f}s")

    # Display detailed metrics in a table
    st.header("Detailed Metrics")
    metrics_df = pd.DataFrame(phoneme_data)
    st.dataframe(metrics_df)

if __name__ == "__main__":
    main()