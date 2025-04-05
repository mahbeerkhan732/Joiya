import streamlit as st 
import requests 
from datetime import datetime, timedelta

# YouTube API Key 
API_KEY = st.text_input("AIzaSyBA-WdCo1FfkfQ1G5k5M3AFTV0x-kq9Il", type="password")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search" 
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos" 
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title 
st.title("YouTube Viral Topics Tool")

# Input Fields 
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# Allow custom keywords
custom_keywords = st.text_area("Enter keywords (one per line):", 
"""Affair Relationship Stories
Reddit Update
Reddit Relationship Advice
Reddit Relationship
Reddit Cheating
AITA Update
Open Marriage
Open Relationship
X BF Caught
Stories Cheat
X GF Reddit
AskReddit Surviving Infidelity
GurlCan Reddit
Cheating Story Actually Happened
Cheating Story Real
True Cheating Story
Reddit Cheating Story
R/Surviving Infidelity
Surviving Infidelity
Reddit Marriage
Wife Cheated I Can't Forgive
Reddit AP
Exposed Wife
Cheat Exposed""")

keywords = [k.strip() for k in custom_keywords.split('\n') if k.strip()]
max_subscriber_count = st.number_input("Maximum Subscriber Count:", min_value=100, value=3000)

# Fetch Data Button 
if st.button("Fetch Data"): 
    if not API_KEY:
        st.error("Please enter your YouTube API Key")
    else:
        try: 
            with st.spinner("Fetching data from YouTube..."):
                # Calculate date range 
                start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z" 
                all_results = []

                progress_bar = st.progress(0)
                
                # Iterate over the list of keywords 
                for i, keyword in enumerate(keywords):
                    progress_bar.progress((i+1)/len(keywords))
                    st.write(f"Searching for keyword: {keyword}")

                    # Define search parameters 
                    search_params = { 
                        "part": "snippet", 
                        "q": keyword, 
                        "type": "video", 
                        "order": "viewCount", 
                        "publishedAfter": start_date, 
                        "maxResults": 5, 
                        "key": API_KEY, 
                    }

                    # Fetch video data 
                    response = requests.get(YOUTUBE_SEARCH_URL, params=search_params) 
                    data = response.json()

                    # Check if "items" key exists 
                    if "items" not in data or not data["items"]: 
                        st.warning(f"No videos found for keyword: {keyword}") 
                        continue

                    videos = data["items"] 
                    video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]] 
                    channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

                    if not video_ids or not channel_ids: 
                        st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.") 
                        continue

                    # Fetch video statistics 
                    stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY} 
                    stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params) 
                    stats_data = stats_response.json()

                    if "items" not in stats_data or not stats_data["items"]: 
                        st.warning(f"Failed to fetch video statistics for keyword: {keyword}") 
                        continue

                    # Fetch channel statistics 
                    channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY} 
                    channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params) 
                    channel_data = channel_response.json()

                    if "items" not in channel_data or not channel_data["items"]: 
                        st.warning(f"Failed to fetch channel statistics for keyword: {keyword}") 
                        continue

                    stats = stats_data["items"] 
                    channels = channel_data["items"]

                    # Collect results 
                    for video, stat, channel in zip(videos, stats, channels): 
                        title = video["snippet"].get("title", "N/A") 
                        description = video["snippet"].get("description", "")[:200] 
                        video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}" 
                        views = int(stat["statistics"].get("viewCount", 0)) 
                        subs = int(channel["statistics"].get("subscriberCount", 0))

                        if subs < max_subscriber_count:  # Only include channels with fewer subscribers than specified
                            all_results.append({ 
                                "Title": title, 
                                "Description": description, 
                                "URL": video_url, 
                                "Views": views, 
                                "Subscribers": subs,
                                "Keyword": keyword
                            })

            # Display results 
            if all_results: 
                st.success(f"Found {len(all_results)} results across all keywords!")
                
                # Option to sort results
                sort_by = st.selectbox("Sort results by:", ["Views (high to low)", "Subscribers (low to high)"])
                if sort_by == "Views (high to low)":
                    all_results.sort(key=lambda x: x["Views"], reverse=True)
                else:
                    all_results.sort(key=lambda x: x["Subscribers"])
                
                for result in all_results: 
                    with st.expander(f"{result['Title']} ({result['Views']} views)"):
                        st.markdown( 
                            f"**Keyword:** {result['Keyword']}  \n"
                            f"**Description:** {result['Description']}  \n" 
                            f"**URL:** [Watch Video]({result['URL']})  \n" 
                            f"**Views:** {result['Views']:,}  \n" 
                            f"**Subscribers:** {result['Subscribers']:,}" 
                        ) 
            else: 
                st.warning(f"No results found for channels with fewer than {max_subscriber_count:,} subscribers.")

        except Exception as e: 
            st.error(f"An error occurred: {e}")
