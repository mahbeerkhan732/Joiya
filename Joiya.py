import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time
import configparser

# Handle streamlit-tags dependency
try:
    from streamlit_tags import st_tags
except ImportError:
    st.error("Required package missing! Install with: pip install streamlit-tags")
    st.stop()

# Configuration
config = configparser.ConfigParser()
config.read('config.ini')

# YouTube API Configuration
API_KEY = config.get('YOUTUBE', 'API_KEY', fallback='AIzaSyBA-WdCo1FfkfQ1G5k5M3AFTV0x-kq9IlE')
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# App Configuration
st.set_page_config(
    page_title="AI YouTube Trend Analyzer Pro",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    .reportview-container .main .block-container {padding-top: 2rem;}
    .st-bb {background-color: #ffffff;}
    .st-at {background-color: #eef2f7;}
    h1 {color: #2b5876;}
    h2 {color: #4e4376;}
    .stProgress > div > div > div > div {background-color: #2b5876;}
</style>
""", unsafe_allow_html=True)

# App Header
st.title("🔍 AI-Powered YouTube Trend Analyzer Pro")
st.markdown("### Discover Viral Content Opportunities with Advanced AI Insights")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Control Panel")
    
    # API Check
    if API_KEY == 'ENTER_YOUR_API_KEY_HERE':
        st.error("YouTube API Key Required!")
        st.markdown("Get API Key: [Google Cloud Console](https://console.cloud.google.com/)")
        st.stop()

    # Date Configuration
    st.subheader("📅 Date Range")
    days = st.slider("Analysis Period (Days)", 1, 3650, 365, 
                    help="Select time range for content analysis")

    # Channel Filters
    st.subheader("👥 Channel Filters")
    min_subs, max_subs = st.slider(
        "Subscriber Range",
        0, 1000000, (0, 10000),
        help="Filter channels by subscriber count"
    )

    # Content Settings
    st.subheader("🎯 Content Parameters")
    col1, col2 = st.columns(2)
    with col1:
        min_results = st.number_input("Min Results/Keyword", 1, 50, 3)
    with col2:
        max_results = st.number_input("Max Results/Keyword", 1, 50, 10)

    # Keyword Management
    st.header("🔑 Keyword Configuration")
    keyword_presets = {
        "Relationships": ["Dating Advice", "Marriage Tips", "Breakup Stories"],
        "True Stories": ["Crime Documentaries", "Survival Stories"],
        "Viral Content": ["Reddit Recap", "TikTok Compilations"]
    }
    
    selected_categories = st.multiselect(
        "Content Categories",
        list(keyword_presets.keys()),
        default=["Relationships"]
    )
    
    custom_keywords = st_tags(
        label="Custom Keywords:",
        text="Press enter to add",
        value=["Viral Stories"],
        suggestions=["Scary Stories", "Family Drama"]
    )

    # Export Options
    st.header("📤 Export Options")
    export_format = st.selectbox(
        "Report Format",
        ["CSV", "Excel", "JSON"],
        index=0
    )

# Initialize Keywords
keywords = []
for category in selected_categories:
    keywords.extend(keyword_presets[category])
keywords.extend(custom_keywords)
keywords = list(set(keywords))

# API Functions
@st.cache_data(ttl=3600)
def fetch_youtube_data(url, params):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Video Processing (Fixed subs variable handling)
def process_video(video_data, channel_data):
    try:
        stats = video_data.get("statistics", {})
        snippet = video_data.get("snippet", {})
        
        # Safely get channel information
        channel_info = next(
            (c for c in channel_data.get("items", [])
             if c.get("id") == snippet.get("channelId")), None
        )
        
        if not channel_info:
            return None
            
        # Handle missing subscriber count
        subs = int(channel_info.get("statistics", {}).get("subscriberCount", 0))
        if not (min_subs <= subs <= max_subs):
            return None

        return {
            "Title": snippet.get("title", "Untitled"),
            "Views": int(stats.get("viewCount", 0)),
            "Likes": int(stats.get("likeCount", 0)),
            "Comments": int(stats.get("commentCount", 0)),
            "Subscribers": subs,  # Now properly defined
            "Channel": snippet.get("channelTitle", "Unknown"),
            "Published": snippet.get("publishedAt", ""),
            "URL": f"https://youtu.be/{video_data.get('id', '')}",
            "Tags": ", ".join(snippet.get("tags", [])[:5]),
            "Description": snippet.get("description", "")[:500]
        }
    except Exception as e:
        return None

# Rest of the code remains unchanged...
