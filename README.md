# 🎓 Chillno - Chinese Language Learning Assistant

![Chillno Logo](./Frontend/chillno_logo_black.jpg)

An intelligent AI-powered platform for interactive Chinese language learning, featuring real-time conversation practice, pronunciation assessment, and personalized learning paths.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Framework](https://img.shields.io/badge/framework-streamlit-red.svg)

## ✨ Features

- 🤖 **AI-Powered Conversations**: Engage in natural Chinese conversations with an AI teacher that adapts to your proficiency level
- 🎯 **Dynamic Level Assessment**: Automatic evaluation of your Chinese language proficiency using HSK standards
- 🗣️ **Speech Recognition**: Real-time speech recognition and pronunciation assessment powered by Azure Cognitive Services
- 👥 **Voice Cloning**: Generate natural Chinese speech with customizable voices using ElevenLabs
- 📊 **Progress Tracking**: Monitor your learning progress with detailed conversation history and performance metrics
- 🎮 **Interactive UI**: User-friendly interface built with Streamlit for seamless learning experience
- 🔄 **Adaptive Learning**: Vocabulary and conversations tailored to your current HSK level

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- API Keys for:
  - Google Gemini Pro
  - Azure Speech Services
  - ElevenLabs
  - Simli AI

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/chinese-learning-assistant.git
cd chinese-learning-assistant
```

2. Install dependencies
```bash
pip install -r requirements.txt
brew install ffmpeg
brew install postgresql
brew services start postgresql
```

3. Set up environment variables in `Backend/Env.py`:
```python
GEMINI_API_KEY="your_gemini_api_key"
AZURE_ASR_KEY="your_azure_key"
AZURE_ASR_REGION="your_azure_region"
XI_API_KEY="your_elevenlabs_key"
SIMLI_API_KEY="your_simli_key"
DATABASE_URL="postgresql://username:password@localhost:5432/dbname"
```

4. Initialize the database
```bash
python -c "from Backend.Store import Store; Store()"
```

## 💻 Usage

Start the application
```bash
streamlit run Frontend/app.py
```

## 🏗️ Architecture

The project is structured into several key components:

- **Frontend**: Streamlit-based web interface
- **Backend**:
  - `Chatbot.py`: AI conversation management
  - `ChatAnalysis.py`: Language proficiency assessment
  - `Speech.py`: Speech recognition and assessment
  - `VoiceCloning.py`: Text-to-speech generation
  - `Store.py`: Database management
  - `SimliAPI.py`: Avatar generation

## 📚 Data Structure

The system uses two main CSV files for vocabulary and character data:
- `word.csv`: Contains word-level HSK vocabulary
- `char.csv`: Contains character-level HSK data

## 🔐 Security

- Secure database connections with connection pooling
- API key management through environment variables
- User authentication and session management

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini Pro for AI conversations
- Azure Cognitive Services for speech recognition
- ElevenLabs for voice synthesis
- Simli AI for avatar generation
- Streamlit for the web framework

## 📞 Contact

For any questions or feedback, please open an issue in the repository.
