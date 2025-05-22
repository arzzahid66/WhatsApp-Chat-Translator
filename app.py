import streamlit as st
import base64
import os
from PIL import Image
import io

# For Gemini
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# For OpenAI
from openai import OpenAI

# Set page config with dark theme
st.set_page_config(
    page_title="WhatsApp Chat Translator",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Minimal custom CSS - only essential styling
st.markdown("""
<style>
    /* WhatsApp colors */
    :root {
        --whatsapp-green: #25D366;
        --whatsapp-dark-green: #075E54;
        --whatsapp-light-green: #128C7E;
    }
    
    /* Hide deprecation warnings */
    .stWarning {
        display: none !important;
    }
    
    /* Custom header styling */
    .main-header {
        color: var(--whatsapp-green);
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Custom button styling */
    .stButton > button {
        background-color: var(--whatsapp-dark-green) !important;
        color: white !important;
    }
    
    .stButton > button:hover {
        background-color: var(--whatsapp-light-green) !important;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        margin-top: 30px;
        font-size: 0.8rem;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>WhatsApp Chat Translator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Upload WhatsApp conversation screenshots and translate them to Arabic</p>", unsafe_allow_html=True)

# Initialize session state for storing API keys
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""
if 'selected_provider' not in st.session_state:
    st.session_state.selected_provider = "OpenAI"
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []
if 'translation_results' not in st.session_state:
    st.session_state.translation_results = []

# Sidebar for provider selection and API key input
with st.sidebar:
    st.header("Settings")
    
    # Provider selection
    st.subheader("Select AI Provider")
    provider = st.radio(
        "Choose your AI provider:",
        ("OpenAI", "Gemini"),
        index=0 if st.session_state.selected_provider == "OpenAI" else 1,
        key="provider_radio"
    )
    st.session_state.selected_provider = provider
    
    # API Key input
    st.subheader("API Key")
    
    if provider == "OpenAI":
        st.write("Enter your OpenAI API key:")
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.openai_api_key,
            key="openai_key_input"
        )
        st.session_state.openai_api_key = openai_key
        st.markdown("[Get an OpenAI API key](https://platform.openai.com/api-keys)")
    else:
        st.write("Enter your Google Gemini API key:")
        gemini_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=st.session_state.gemini_api_key,
            key="gemini_key_input"
        )
        st.session_state.gemini_api_key = gemini_key
        st.markdown("[Get a Gemini API key](https://aistudio.google.com/apikey)")
    
    # Information about the app
    st.subheader("About")
    st.write("""
    This app allows you to translate WhatsApp conversation screenshots to Arabic.
    
    You can choose between OpenAI's GPT-4.1-nano or Google's Gemini models for translation.
    
    Upload one or multiple screenshots and process them sequentially.
    """)

# Main content area
st.subheader("Upload WhatsApp Screenshots")

# Image upload
uploaded_files = st.file_uploader(
    "Upload one or more WhatsApp conversation screenshots",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    st.session_state.uploaded_images = uploaded_files
    st.success(f"{len(uploaded_files)} image(s) uploaded successfully!")
    
    # Display thumbnails of uploaded images
    cols = st.columns(min(4, len(uploaded_files)))
    for i, uploaded_file in enumerate(uploaded_files):
        with cols[i % min(4, len(uploaded_files))]:
            st.image(uploaded_file, caption=f"Image {i+1}", width=150)

# Function to encode image to base64
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode("utf-8")

# Function to translate using OpenAI
def translate_with_openai(image_file, api_key):
    try:
        # Use the official OpenAI library
        client = OpenAI(api_key=api_key)
        
        encoded_image = encode_image(image_file)
        
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "translate this chat to arabic as it is preserve it's original structure translate this whole conversation to arabic with nothing extra text.pleaes strcture the response line by line keep each message in a new line."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
                        }
                    ]
                }
            ],
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Function to translate using Gemini
def translate_with_gemini(image_file, api_key):
    try:
        encoded_image = encode_image(image_file)
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=api_key,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": "translate this chat to arabic as it is preserve it's original structure translate this whole conversation to arabic with nothing extra text.pleaes strcture the response line by line keep each message in a new line."},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{encoded_image}"},
            ]
        )
        
        result = llm.invoke([message])
        return result.content
    except Exception as e:
        return f"Error: {str(e)}"

# Process button
if st.button("Translate to Arabic"):
    if not st.session_state.uploaded_images:
        st.error("Please upload at least one image.")
    else:
        if st.session_state.selected_provider == "OpenAI" and not st.session_state.openai_api_key:
            st.error("Please enter your OpenAI API key.")
        elif st.session_state.selected_provider == "Gemini" and not st.session_state.gemini_api_key:
            st.error("Please enter your Gemini API key.")
        else:
            st.session_state.translation_results = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, image_file in enumerate(st.session_state.uploaded_images):
                status_text.write(f"Processing image {i+1} of {len(st.session_state.uploaded_images)}...")
                
                if st.session_state.selected_provider == "OpenAI":
                    result = translate_with_openai(image_file, st.session_state.openai_api_key)
                else:
                    result = translate_with_gemini(image_file, st.session_state.gemini_api_key)
                
                st.session_state.translation_results.append({
                    "image": image_file,
                    "translation": result
                })
                
                progress_bar.progress((i + 1) / len(st.session_state.uploaded_images))
            
            status_text.success("All images processed successfully!")
            progress_bar.empty()

# Display results
if st.session_state.translation_results:
    st.subheader("Translation Results")
    
    for i, result in enumerate(st.session_state.translation_results):
        with st.expander(f"Image {i+1} Translation", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # Use use_container_width instead of use_column_width
                st.image(result["image"], caption=f"Original Image {i+1}", use_container_width=True)
            
            with col2:
                st.subheader("Arabic Translation:")
                st.markdown(f"<div dir='rtl'>{result['translation']}</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div class='footer'>WhatsApp Chat Translator © 2025</div>", unsafe_allow_html=True)
