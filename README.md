﻿
# 🎯 SentimentSearch

**SentimentSearch** is a voice-powered and emotion-driven tool that helps you rediscover meaningful photo memories based on human emotions!

You can say things like:

> "Show me the top 3 happiest photos from January 2022 from Paris"

And it will:
1. Transcribe your voice to text (or allow you to type your query)
2. Understand the emotion, timeframe, location, etc. you're asking for along with your desired amount of pictures (along with allowing you to upload your own custom image for emotions to be captured)
5. Return and display the top matching images based on the user-requested queries

---

## 🧑‍💻 Setup Instructions

### 1. Clone or Download the Project

```bash
git clone https://github.com/farooqashar/SentimentSearch.git
cd SentimentSearch
```

### 2. Create a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv         # On Windows
venv\Scripts\activate       

python3 -m venv venv        # On macOS/Linux
source venv/bin/activate    
```

### 3. Install Dependencies

Install the required Python packages using:

```bash
pip install -r requirements.txt
```

This installs:

- `opencv-python` – image display
- `Pillow` – reading EXIF data from images
- `vaderSentiment` – lightweight sentiment analysis to get intelligent speech to text based on intended meaning
- `deepface` – facial emotion detection
- `RealtimeSTT` – microphone-to-text transcription
- `spacy`- For advanced Natural Language Processing tasks
- `geopy`- For geocoding and location-related features
- `dotenv` - For loading environment variables from a `.env` file
- `google-genai` - For interacting with Google's generative AI models

---

## 🏁 Running the Program

Place a few test images into the `/static/images_v2` folder. Images with faces, EXIF timestamps, and other metadata work best.

Then run:

```bash
python app.py
```

Once prompted, follow the instructions on the web interface.

---

## 💡 Features
- 🎤 Live Speech Input via Microphone: Capture your queries in real-time using your microphone.
- 🔍 Intelligent Emotion & Metadata Extraction from Natural Speech: The system understands the emotions you're looking for (e.g., "joyful," "angry") and timeframes (e.g., "last week," "2023") along with other metadata from your natural spoken language, leveraging NLP.
- 🗺️ Location-Based Filtering: Filter your photo memories based on the location where they were taken, using geographic information potentially embedded in the image metadata.
- ✨ Enhanced Natural Language Understanding: Utilizes sophisticated Natural Language Processing to better interpret the nuances and context of your spoken requests, leading to more accurate search results.
- 🖼️ Photo Filtering: Filter images based on the user spoken or user written queries.
- 😄 Emotion Detection from Facial Expressions using DeepFace: Analyze the facial expressions in your photos to identify and quantify the emotions present in each image.
- 🏆 Ranking Based on Emotional Strength: The retrieved photos are ranked and displayed according to the intensity of the detected emotion, allowing you to see the strongest matches first.
- 🧠 Advanced AI-Powered Search: Integrates with Google's generative AI capabilities to provide more intelligent and context-aware search results, potentially understanding complex emotional scenarios or relationships within your memories.
- 🤫 Secure Configuration Management: Utilizes environment variables loaded from a .env file for secure handling of sensitive configuration.
- 💾 Caching to Speed Up Repeated Analysis: Emotion analysis results are stored in a cache, so repeated searches for the same images are significantly faster.
- 🖥️ Auto-Resized Image Previews: Image previews are automatically resized to fit your screen for easy viewing within the web interface.
- 👤 User-Specific Emotion Analysis: The system can capture and analyze your current emotional state (e.g., via webcam) and use this information to prioritize or filter your photo memories based on how you're feeling in the moment.
- 🌐 Intuitive Web Interface: A user-friendly web application allows you to easily interact with SentimentSearch through voice commands and visual feedback.
- 📊 Evaluation and Feedback Logging: User interactions and evaluations are recorded to continuously improve the user experience.
---

## 📁 Folder Structure

```
├── .gitignore
├── app.py                 ← Main Flask application logic (V2)
├── evaluation.py          ← For evaluating system performance (V1)
├── emotion_cache.json     ← Auto-generated cache of emotion scores (local, not tracked by Git)
├── requirements.txt       ← List of Python dependencies
├── sentiment_search.py    ← Older version of the core logic (deprecated)
├── sentiment_search_v2.py ← Current core logic for emotion analysis and filtering
├── static/                ← Static files for the web application
│   ├── css/styles.css     ← Styling for the Flask web application
│   ├── images/            ← V1 images
│   ├── images_V2/         ← Place your image files here for V2
│   ├── js/script.js       ← Logic for changing the web interface
├── templates/             ← HTML templates for the web interface
│   └── index.html
├── user_evaluation.jsonl  ← Log of user evaluations and feedback
├── user_face_templates/   ← Stores captured user face/emotion data
└── util.py                ← Utility functions
```

## 🛠️ Development Tips

* **Leveraging Caching:** The `emotion_cache.json` file significantly speeds up processing by storing the emotion analysis results from DeepFace. This local cache prevents redundant computations on previously analyzed images.
* **Handling Images Without EXIF Dates:** Images lacking EXIF date information will still undergo emotion analysis. However, they won't be filterable by specific dates in your queries.
* **Utilizing Geolocation (geopy):** Images can be refined by search queries based on location names or geographical areas using `geopy`.
* **Managing API Keys Securely (.env with dotenv):** If the `google-genai` library or other services requiring API keys are used, store these sensitive keys in a `.env` file and access them using the `dotenv` library to prevent hardcoding them in your code.

## 🤝 Software Packages and Tools

* [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) – Enables real-time transcription of speech from your microphone.
* [DeepFace](https://github.com/serengil/deepface) – Provides state-of-the-art facial emotion recognition capabilities.
* [VADER Sentiment](https://github.com/cjhutto/vaderSentiment) – Offers a lexicon and rule-based sentiment analysis tool, useful for understanding the emotional tone of user queries.
* [Pillow](https://pillow.readthedocs.io/en/stable/) – A powerful image processing library used here for reading and manipulating image metadata, including EXIF data.
* [OpenCV](https://docs.opencv.org/4.x/) – A comprehensive computer vision library used for image processing tasks, such as resizing image previews for display in the web interface.
* [Python](https://www.python.org/) – The primary programming language that powers the entire SentimentSearch application.
* [Flask](https://flask.palletsprojects.com/en/3.0.x/) – A lightweight and flexible web framework used to build the user interface for SentimentSearch V2.
* [spaCy](https://spacy.io/) – A library for advanced Natural Language Processing, potentially used for more sophisticated understanding of user queries.
* [geopy](https://geopy.readthedocs.io/en/stable/) – A geocoding library that allows the application to work with geographic locations, potentially for location-based image filtering.
* [python-dotenv](https://pypi.org/project/python-dotenv/) – A library for reading key-value pairs from a `.env` file and setting them as environment variables, crucial for managing API keys and other sensitive configuration.
* [google-genai](https://github.com/googleapis/python-genai) – Google's Python library for interacting with their generative AI models, potentially enabling advanced search functionalities or memory descriptions.

-----

Happy SentimentSearching\! 📸🧠💬
