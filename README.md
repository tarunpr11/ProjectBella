# 🧠 Project Bella: A Voice-Driven Intelligent Automation System

A hands-free personal assistant that combines **Python**, **Google's Gemini AI**, and **UiPath RPA** to understand natural language voice commands and automate everyday desktop and web tasks.

---

## 🚀 Demo

Watch Bella in action!  
This Google Drive link contains video recordings of the assistant performing various tasks, from sending emails to fetching web data.

👉 **[Click here to access the drive link](https://drive.google.com/drive/folders/1lacGnduAQ10nC1vqxsa28FoxASPIKg9q?usp=sharing)**

---

## 📖 Overview

Project **Bella** is a voice-activated assistant designed to address the inefficiency of performing repetitive manual computer tasks.  

By integrating:
- **Python** for voice processing  
- **Google's Gemini AI** for natural language understanding (NLU)  
- **UiPath** for robotic process automation (RPA)  

Bella provides a seamless, hands-free interface for your computer.

The system interprets spoken instructions in plain English (tuned for an *en-IN* accent) and autonomously executes over 10 distinct tasks.  
It can handle both direct commands (e.g., “lock my computer”) and complex, multi-step tasks (e.g., “send an email,” which triggers AI-powered text correction and interactive login).

This project demonstrates a robust and scalable architecture for creating powerful, personalized digital assistants.

---

## ✨ Features

Bella can understand and execute the following tasks through voice commands:

- 📧 **Send Email** – Guides you to spell out the recipient's email (with AI correction), dictates the subject and body (with AI correction), confirms the details, and sends the email via Gmail.  
- 👀 **Read Unread Emails** – Checks your Gmail inbox and reads out the subject lines of your top 5 unread emails.  
- 📸 **Take Screenshot** – Takes a screenshot of your active window and saves it to your desktop with a unique timestamp.  
- 🔊 **Set System Volume** – Sets your computer's volume to a specific percentage (e.g., “set volume to 70 percent”) or mutes it (“mute volume”).  
- 📰 **Get Top News Headlines** – Scrapes the top 5 headlines from Google News and reads them back to you.  
- 🗺️ **Find Location on Google Maps** – Opens Google Maps in your browser and searches for any location you specify (e.g., “find nearby restaurants”).  
- ☀️ **Get Current Weather** – Fetches the current temperature and conditions for a specified location (or a default location if none is given).  
- 💻 **Lock Computer** – Immediately locks your Windows session.  
- 📝 **Create Sticky Note** – Opens a new sticky note and types your memo content.  
- 💱 **Convert Currency** – Looks up the latest conversion rate between two currencies (e.g., “convert 100 US dollars to Indian rupees”).  
- 📂 **Open Specific Folders** – Opens common folders like “Downloads” or “Documents.”  
- 🔍 **Google Search** – Opens your browser and performs a Google search for any query.  
- 💬 **Conversational Fallback** – If your command isn't a task, Bella engages in a general conversation using Gemini.

---

## 🛠️ Architecture & Tech Stack

The system is built on three core components that communicate in real-time:

### 🧩 Python (The Brain)
- **Main Script:** `assistant_brain.py` acts as the central coordinator.  
- **Wake Word:** Uses `pvporcupine` for offline, low-CPU detection of the "Bella" wake word.  
- **Voice I/O:** Uses `speech_recognition` (with 'en-IN' model) for transcription and `pygame` / `elevenlabs` for interruptible text-to-speech.  
- **Orchestration:** Calls the Gemini API, parses the JSON response, and triggers the UiPath robot using `subprocess`. It also reads output files from UiPath to provide spoken results.

### 🤖 Google Gemini AI (The NLU)
- Serves as the AI brain for understanding language.  
- **Intent Classification:** A primary prompt classifies user commands into tasks (e.g., "send_email") or general conversation.  
- **Entity Extraction:** Extracts key details (e.g., location, note_content, percentage).  
- **AI Correction:** Specialized prompts are used to correct errors in transcribed speech, especially for emails, subjects, and body text.

### 🪄 UiPath (The Hands)
- Performs all UI and system automation through the `Bella_Assistant_Process`.  
- **Main.xaml:** Central controller that receives a JSON command from Python and uses a Switch activity to call the correct sub-workflow.  
- **Reusable Workflows:** Includes `Login_To_Gmail.xaml` (voice-interactive email prompt).  
- **Task Workflows:** Individual `.xaml` files for each task (e.g., `Get_News_Headlines.xaml`, `Create_Sticky_Note.xaml`).  
- **Data Return:** Uses `Write Text File` to send task results back to Python.

---

## 🔧 Setup & Installation Guide

Follow these steps precisely to get Bella running on your machine.

### Prerequisites

* **Python:** 3.10 or 3.11.
* **UiPath:** UiPath Studio and UiPath Assistant installed.
* **NirCmd:** Download `nircmd.exe` (from nirsoft.net) and place it in `C:\Tools\nircmd.exe`. Add `C:\Tools\` to your Windows PATH environment variable.
* **API Keys:** You must have free accounts and API keys for:
    * Google Gemini
    * ElevenLabs
    * Picovoice

---

### 1. Python Setup (The Brain)

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/tarunpr11/ProjectBella.git](https://github.com/tarunpr11/ProjectBella.git)
    cd Project-Bella
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Python Libraries:**
    ```bash
    pip install google-generativeai speechrecognition pvporcupine pyaudio pygame keyboard python-dotenv elevenlabs
    ```

4.  **Configure API Keys:**
    * Create a file named `.env` in the root of the `Project-Bella` folder.
    * Add your secret keys to this file:
        ```
        GEMINI_API_KEY="AIzaSy...your_gemini_key"
        ELEVEN_API_KEY="your_elevenlabs_key"
        PICOVOICE_ACCESS_KEY="your_picovoice_key"
        ```

5.  **Add Wake Word Model:**
    * Place your custom `.ppn` file (e.g., `Bella.ppn`) in the same folder as `assistant_brain.py`.

---

### 2. UiPath Setup (The Hands)

1.  **Open the Project:**
    * Open the `Bella_Assistant_Process` folder in UiPath Studio.

2.  **CRITICAL: Install Dependencies (`.objects`):**
    * UiPath projects often fail to build correctly on a new machine if the local package dependencies are not present.
    * **Download the `.objects` folder** from the Google Drive link provided:
        * **Link:** `[Click here to access the drive link](https://drive.google.com/drive/folders/1lacGnduAQ10nC1vqxsa28FoxASPIKg9q?usp=sharing)`
    * **Place the folder:** Unzip and place the `.objects` folder inside the `Bella_Assistant_Process` directory. The final path should look like: `...\Project Bella\Bella_Assistant_Process\.objects`.

3.  **Review & Publish:**
    * **Update Paths:** Open `Main.xaml` and check the `Start Process` activity inside the `Login_To_Gmail.xaml` workflow. Ensure the file paths to `python.exe` and `voice_helper.py` are correct for your system.
    * **Check Selectors:** Open the workflows that interact with web pages (Gmail, News, Weather, etc.). Run them in Studio and ensure the selectors are still valid. You may need to re-indicate elements if Google's layout has changed.
    * **Publish:** In UiPath Studio, go to the **Design** tab and click **Publish**. This makes the automation available to your local UiPath Assistant.

---

### 3. Usage

1.  Ensure your **UiPath Assistant** is running and signed in.
2.  In your terminal (with the `venv` activated), run the main Python script:
    ```bash
    python assistant_brain.py
    ```
3.  Wait for the console to show: `Listening for wake word...`
4.  Say your wake word ("Bella").
5.  When Bella replies ("Yes, how can I help?"), give your command.

---

## 👥 Authors

* **Tarun Parthiban**
* **Beneta Johnson**
