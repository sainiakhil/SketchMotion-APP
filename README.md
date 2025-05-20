# SketchMotion-APP

A Streamlit web application that uses Google's Gemini AI to generate short (1-2 seconds) mathematical animations with Manim based on user descriptions.

**Live Demo (if you deploy it):** [Link to your deployed app - e.g., on Streamlit Community Cloud]

![Screenshot of Manim Quick Animator](placeholder_screenshot.png)
*(Replace `placeholder_screenshot.png` with an actual screenshot of your app)*

## Features

*   **AI-Powered Animation Generation:** Describe a simple mathematical concept, and the AI (Gemini) will attempt to write Manim code for it.
*   **Instant Manim Rendering:** The generated code is executed using Manim to produce a short MP4 video.
*   **User-Friendly Interface:** Built with Streamlit, providing an intuitive way to input requests and view results.
*   **Prompt Suggestions:** Offers quick ideas to get users started.
*   **Short Animations:** Designed to create very brief animations (approx. 20-25 frames, 1-2 seconds run time) for quick previews and experimentation.
*   **Informative Sidebar:** Explains how the bot works and how to use it effectively.

## How It Works

1.  **User Input:** The user describes a mathematical animation concept in natural language.
2.  **LLM Code Generation:** The description is sent to a Google Gemini model (e.g., `gemini-1.5-flash-latest`) with a specialized prompt instructing it to generate Python code for a short Manim animation.
3.  **Manim Execution:**
    *   The generated Python code is saved to a temporary file.
    *   Manim (Community Edition) is invoked as a subprocess to render the scene described in the code.
    *   Low quality (`-ql`) rendering is used for speed.
4.  **Video Display:** The resulting MP4 video file is displayed in the Streamlit interface.

## Tech Stack

*   **Frontend:** Streamlit
*   **AI Model:** Google Gemini (via `google-generativeai` Python SDK)
*   **Animation Engine:** Manim (Community Edition)
*   **Language:** Python


*This project was created to explore the intersection of LLMs, creative coding, and mathematical visualization.*
