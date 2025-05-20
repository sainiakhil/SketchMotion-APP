import streamlit as st
import google.generativeai as genai
import subprocess
import tempfile
import os
import re
import shutil
from pathlib import Path


# --- Streamlit Page Configuration (MUST BE FIRST Streamlit command) ---
st.set_page_config(page_title="SketchMotion APP", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")


# --- Sidebar Content ---
with st.sidebar:
    st.image("https://www.manim.community/logo.png", width=100) # Manim logo for branding
    st.title("Animator ChatBot Using Manim")
    st.markdown(
        "This bot uses LLM to generate Python code for **Manim**, "
        "a powerful mathematical animation engine. It then renders a "
        "video (4-5 seconds) based on your textual description."
    )
    st.markdown("---")
    st.subheader("🚀 How to Use")
    st.markdown(
        """
        1.  **Describe your animation idea** in the text box on the main page.
            *   Keep it simple and mathematical (e.g., "a circle transforming into a square").
            *   The bot aims for animations around 20-25 frames.
        2.  **Click \"🎬 Generate Animation!\"**
        3.  **Wait for the magic!**
    
        """
    )
    st.markdown("---")
    st.info("💡 **Tip:** For best results, be specific but concise. Complex scenes might time out or not render as expected due to the short animation constraint.")
    st.markdown(
        "<br><br><div style='text-align: center;'>Made with ❤️ using <a href='https://streamlit.io' target='_blank'>Streamlit</a> & <a href='https://www.manim.community/' target='_blank'>Manim</a></div>",
        unsafe_allow_html=True
    )


# --- Configuration ---

genai.configure(api_key="api_key") # Replace with your key
MODEL_NAME = "gemini-2.0-flash-001" 

# Manim output quality: -ql (low), -qm (medium), -qh (high), -qk (4k)
MANIM_QUALITY = "-ql" # Low quality for faster rendering

# --- LLM Prompt (Original code - unchanged) ---
LLM_PROMPT_TEMPLATE = """
You are an expert Manim programmer specializing in creating concise and precise mathematical animations.
Your task is to generate Python code for a Manim animation based on the user's request.

Follow these strict instructions:
1.  The animation should be a high-quality mathematical visualization.
2.  The generated Manim code **must** produce an animation that is very short, ideally resulting in approximately 20 to 25 frames. To achieve this, use very short `run_time` values for your `self.play()` calls (e.g., `run_time=0.25` or `run_time=0.5`). The total sum of `run_time`s for all animations in the `construct` method should not exceed 1.0 to 1.5 seconds. Avoid long `self.wait()` calls.
3.  **Only output the Python code block.** Do NOT include any explanations, introductory text, "Here's the code:", or markdown code fences (like ```python ... ```). Just the raw Python code.
4.  The code must start with `from manim import *` and any other necessary imports (like `import numpy as np`).
5.  The code must define a single Manim `Scene` class. The class name should be descriptive of the animation (e.g., `class CircleAnimation(Scene):`).
6.  The scene must contain a `construct(self)` method where all animation logic resides.
7.  Ensure the code is complete, runnable, and will produce a video file when executed with Manim.
8.  Focus on clarity, precision, and mathematical correctness.
9.  If the user asks for something non-mathematical, too complex for a very short animation (20-25 frames), or potentially unsafe, politely generate a very simple default animation (e.g., a circle appearing and disappearing quickly) and do not attempt the complex request.

User Request: {user_prompt}

Generated Manim Code:
"""

# --- Helper Functions (Original code - largely unchanged, minor subprocess improvement) ---

def generate_manim_code_from_llm(user_query: str) -> str | None:
    """Generates Manim code using the LLM."""
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = LLM_PROMPT_TEMPLATE.format(user_prompt=user_query)
        response = model.generate_content(prompt)
        
        generated_text = response.text
        if generated_text.strip().startswith("```python"):
            generated_text = generated_text.strip()[9:] 
        if generated_text.strip().endswith("```"):
            generated_text = generated_text.strip()[:-3] 
        
        return generated_text.strip()
    except Exception as e:
        st.error(f"Error calling LLM ({MODEL_NAME}): {e}")
        return None

def extract_scene_name(manim_code: str) -> str | None:
    """Extracts the Manim scene class name from the code."""
    match = re.search(r"class\s+(\w+)\(Scene\):", manim_code)
    if match:
        return match.group(1)
    st.error("Could not find Scene name in the generated code. The LLM might have provided an invalid Manim script.")
    return None

def run_manim(manim_code: str, scene_name: str) -> str | None:
    """
    Runs Manim to render the animation.
    Returns the path to the rendered video file or None on failure.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_script:
        tmp_script_path = tmp_script.name
        tmp_script.write(manim_code)

    script_path_obj = Path(tmp_script_path)
    script_name_no_ext = script_path_obj.stem 

    quality_folder_map = {
        "-ql": "480p15",
        "-qm": "720p30",
        "-qh": "1080p60",
        "-qk": "2160p60", 
    }
    quality_folder = quality_folder_map.get(MANIM_QUALITY, "720p30") 

    media_dir = Path("media")
    video_output_dir = media_dir / "videos" / script_name_no_ext / quality_folder
    expected_video_path = video_output_dir / f"{scene_name}.mp4"

    if media_dir.exists():
        temp_script_media_dir = media_dir / "videos" / script_name_no_ext
        if temp_script_media_dir.exists():
            try:
                shutil.rmtree(temp_script_media_dir)
            except Exception as e:
                st.warning(f"Could not clean up old media for {script_name_no_ext}: {e}")
        
    command = ["manim", MANIM_QUALITY, tmp_script_path, scene_name]
    
    process = None # Initialize process to None
    try:
        # Added creationflags to hide console window on Windows for a cleaner UX
        process_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=process_flags)
        stdout, stderr = process.communicate(timeout=120) 

        if process.returncode != 0:
            st.error(f"Manim execution failed! (Return code: {process.returncode})")
            with st.expander("Manim Output Details"):
                st.subheader("Manim Standard Output:")
                st.code(stdout if stdout else "No standard output.", language=None)
                st.subheader("Manim Standard Error:")
                st.code(stderr if stderr else "No standard error.", language=None)
            return None
        
        if expected_video_path.exists():
            return str(expected_video_path)
        else:
            st.error(f"Manim seemed to succeed, but the video file was not found at: {expected_video_path}")
            with st.expander("Manim Output & File System Details (Video Not Found)"):
                st.info(f"Manim STDOUT:\n{stdout if stdout else 'No standard output.'}")
                st.info(f"Manim STDERR:\n{stderr if stderr else 'No standard error.'}")
                possible_parent = media_dir / "videos" / script_name_no_ext
                if possible_parent.exists():
                    st.info(f"Contents of {possible_parent}: {list(p.name for p in possible_parent.iterdir() if p.is_dir())}")
                    if (possible_parent / quality_folder).exists():
                         st.info(f"Contents of {possible_parent / quality_folder}: {list(p.name for p in (possible_parent / quality_folder).iterdir())}")
                else:
                    st.info(f"Media directory for script ({possible_parent}) does not exist.")
            return None

    except subprocess.TimeoutExpired:
        st.error("Manim rendering timed out after 120 seconds. The animation might be too complex or long.")
        if process: # Ensure process is not None
            process.kill()
            stdout, stderr = process.communicate()
            with st.expander("Manim Output Details (Timeout)"):
                st.subheader("Manim Standard Output (on timeout):")
                st.code(stdout if stdout else "No standard output.", language=None)
                st.subheader("Manim Standard Error (on timeout):")
                st.code(stderr if stderr else "No standard error.", language=None)
        return None
    except FileNotFoundError:
        st.error("Manim command not found. Please ensure Manim is installed and added to your system's PATH.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during Manim execution: {e}")
        return None
    finally:
        try:
            if os.path.exists(tmp_script_path):
                 os.remove(tmp_script_path)
        except OSError:
            pass # st.warning(f"Could not remove temporary script {tmp_script_path}")


# --- Streamlit UI ---
st.title(" 🎬 SketchMotion APP")
st.markdown("---") 

# Initialize session state
if "video_path" not in st.session_state:
    st.session_state.video_path = None
if "last_user_prompt" not in st.session_state:
    st.session_state.last_user_prompt = ""
if "current_prompt_text" not in st.session_state:
    st.session_state.current_prompt_text = ""

suggestions = {
        "Simple Circle": "Show a circle appearing and then disappearing quickly.",
        "Basic Tree": "Animate a very simple tree: a root node, then two child nodes appear one by one.",
        "Square to Circle": "A square transforms into a circle.",
        "Growing Line": "Animate a line growing from left to right from the center.",
    }
num_suggestion_cols = min(len(suggestions), 4)
suggestion_cols = st.columns(num_suggestion_cols)
suggestion_items = list(suggestions.items())

for i, (button_label, prompt_text) in enumerate(suggestion_items):
        col_index = i % num_suggestion_cols
        # Regular st.button inside a form does NOT submit the form.
        # It triggers its own script rerun if its callback logic executes st.rerun()
        if suggestion_cols[col_index].button(
            button_label,
            key=f"suggest_btn_form_{button_label.replace(' ', '_')}", # Unique key
            use_container_width=True
        ):
            st.session_state.current_prompt_text = prompt_text # Update session state
            st.rerun() # Rerun to update the text_input value within the form

with st.form(key="animation_form"):
    user_typed_prompt_in_form = st.text_area(
        "**Enter your animation request (or use suggestions above):**",
        value=st.session_state.current_prompt_text, # Pre-fills from session state
        placeholder="e.g., 'A circle growing and shrinking'",
        key="user_input_main_field_in_form",
        help="Try: 'Square to circle', 'Sine wave plot', 'Rotating arrow'"
    )
    # Form submit button
    submitted_form = st.form_submit_button("Generate Animation!", type="primary", use_container_width=True)


# --- Processing Logic ---
if submitted_form:
    # When form is submitted, get the current text from the input field.
    # This value might have been typed by user or set by a suggestion.
    user_prompt_to_process = user_typed_prompt_in_form.strip()
    st.session_state.current_prompt_text = user_prompt_to_process # Keep session state in sync

    if user_prompt_to_process:
        st.session_state.last_user_prompt = user_prompt_to_process
        st.session_state.video_path = None # Clear previous video

        with st.spinner("Crafting Animation Visuals..."):
            manim_code = generate_manim_code_from_llm(user_prompt_to_process)

        if manim_code:
            # For debugging:
            # with st.expander("Generated Manim Code (Debug View)"):
            #    st.code(manim_code, language="python")

            scene_name = extract_scene_name(manim_code)
            if scene_name:
                with st.spinner(f"Rendering '{scene_name}' with Manim... 🎞️ (can take a moment)"):
                    video_file_path = run_manim(manim_code, scene_name)

                if video_file_path:
                    st.session_state.video_path = video_file_path
                # Error messages for failed generation are handled within run_manim
            # Error messages for scene name extraction are handled within extract_scene_name
        # Error messages for LLM call are handled within generate_manim_code_from_llm
    else:
        st.warning("Empty prompt! Please type a description or click a suggestion, then hit 'Generate!'. 🤔")

# --- Display Video or Status Messages ---
if st.session_state.video_path:
    st.subheader(f"Your Animation: '{st.session_state.last_user_prompt}'")
    try:
        with open(st.session_state.video_path, 'rb') as video_file:
            video_bytes = video_file.read()
        st.video(video_bytes)

        if st.button("🔄 Create Another Animation", help="Clear current animation and prompt"):
            # Clean up the displayed video file if it exists and is from our temp storage
            if st.session_state.video_path and (Path(tempfile.gettempdir()) / "manim_chatbot_videos") in Path(st.session_state.video_path).parents:
                try:
                    os.remove(st.session_state.video_path)
                except OSError:
                    pass # Already removed or inaccessible

            st.session_state.video_path = None
            st.session_state.current_prompt_text = "" # Clear for the form's text_input
            st.session_state.last_user_prompt = ""
            st.rerun()

    except FileNotFoundError:
        st.error(f"Critical Error: Video file not found at '{st.session_state.video_path}'. This might indicate an issue with file paths or cleanup processes. Please check Manim output if available from a previous step.")
    except Exception as e:
        st.error(f"An error occurred while trying to display the video: {e}")
#else:
#   # Show initial message only if no generation has been attempted yet (no last_user_prompt)
#    if not st.session_state.last_user_prompt and not submitted_form : # and not any([st.session_state.get(f"suggest_btn_form_{s.replace(' ', '_')}") for s in suggestions]):
#        st.info("☝️ Describe your animation in the form above or pick a suggestion, then hit 'Generate Animation!'")


