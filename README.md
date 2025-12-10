# Medical-Chatbot-using-RASA

AI Medical Assistant
A conversational medical data collection system built with RASA that helps streamline patient intake and identifies critical symptoms requiring immediate attention.

## Overview
This project demonstrates how conversational AI can be applied to healthcare workflows. The assistant collects patient demographics and symptoms through natural conversation, stores the information in a structured database, and flags potentially serious medical conditions.

There are 2 tables which I have created in database:
1. Demographic table: It stores patient personal information like name, age, gender, location, occupation, and medical history. This is handled by the RASA form mechanism.
2. Medical Symptoms table: It stores the patient's symptoms, its severity and duration. This is done via the LLM (Ollama with Gemma3:4b) running locally. A prompt is given to the LLM, and it extracts the symptoms, severity and duration from the patient's free-form description. There is also a red flag(severe condition) trigger which checks if the patient has any red flag symptoms. If yes, it flags the patient as having a severe condition and advices the patient to seek urgent medical care.

To access the chatbot with a user-friendly interface, you can use the html file in the project directory. It is a simple web interface with a gradient background that allows users to interact with the chatbot.

Requirements:
1. Python 3.8
2. RASA 3.1 
3. Ollama (Gemma3:4b) - Local LLM for symptom extraction (You can run any other model if you want.)

Some important commands:
1. Train the RASA model: `rasa train`
2. Run the RASA server: `rasa run --enable-api`
3. Run the RASA actions: `rasa run actions`
4. ollama serve


Note:
This is a demonstration project. It should not be used for actual medical diagnosis, treatment decisions, or in clinical settings. Always consult qualified healthcare professionals for medical advice.

Future Planned Upgrades:
1. NLP: As for now the model is only text based. I am planning to implement a voice to text feature to allow users to interact with the chatbot using their voice adn vice versa. 

Author: Wajeeh Ullah