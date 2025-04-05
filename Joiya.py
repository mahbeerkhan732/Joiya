# YouTube Viral Topics Analyzer - Professional Edition

import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="YouTube Viral Topics Analyzer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF0000;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #606060;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: bold;
        color: #FF0000;
    }
    .metric-label {
        font-size: 1rem;
        color: #606060;
    }
    .stButton>button {
        background-color: #FF0000;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #CC0000;
    }
    .info-box {
        background-color: #f0f8ff;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #0066ff;
        margin-bottom: 10px;
    }
    .video-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .video-title {
        color: #1a1a1a;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .stProgress > div > div {
        background-color: #FF0000;
    }
    .view-count {
        font-weight: bold;
        color: #1a1a1a;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .pagination-button {
        background-color: #f8f9fa;
        border: 1px solid #dddddd;
        padding: 5px 10px;
        margin: 0 5px;
        border-radius: 5px;
    }
    .pagination-button:hover {
        background-color: #e9ecef;
    }
    .active-page {
        background-color: #FF0000;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Constants
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Session state initialization
if 'results' not in st.session_state:
    st.session_state.results = []
if 'filtered_results' not in st.session_state:
    st.session_state.filtered_results = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'search_complete' not in st.session_state:
    st.session_state.search_complete = False
if 'last_search_params' not in st.session_state:
    st.session_state.last_search_params = {}
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'items_per_page' not in st.session_state:
    st.session_state.items_per_page = 10
if 'saved_searches' not in st.session_state:
    st.session_state.saved_searches = []
if 'date_filter' not in st.session_state:
    st.session_state.date_filter = "all"

# Functions
def save_results(filename, data):
    """Save results to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not os.path.exists("saved_searches"):
        os.makedirs("saved_searches")
    
    filename = f"saved_searches/{filename}_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    
    st.session_state.saved_searches.append({
        "filename": filename,
        "timestamp": timestamp,
        "count": len(data),
        "keywords": st.session_state.last_search_params.get("keywords", [])
    })
    
    return filename

def load_results(filename):
    """Load results from a JSON file"""
    with open(filename, "r") as f:
        data = json.load(f)
    return data

def fetch_youtube_data(api_key, keywords, days, max_results_per_keyword, min_views, max_subscriber_count, order_by):
    """Fetch data from YouTube API"""
    all_results = []
    
    # Calculate date range
    start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, keyword in enumerate(keywords):
        progress = (i) / len(keywords)
        progress_bar.progress(progress)
        status_text.text(f"Searching for keyword: {keyword} ({i+1}/{len(keywords)})")
        
        # Define search parameters
        search_params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "order": order_by,
            "publishedAfter": start_date,
            "maxResults": max_results_per_keyword,
            "key": api_key,
        }
        
        try:
            # Fetch video data
            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()
            
            # Handle API errors
            if "error" in data:
                st.sidebar.error(f"API Error: {data['error']['message']}")
                continue
                
            # Check if "items" key exists
            if "items" not in data or not data["items"]:
                st.sidebar.info(f"No videos found for keyword: {keyword}")
                continue
            
            videos = data["items"]
            video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
            if not video_ids:
                continue
                
            channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]
            if not channel_ids:
                continue
            
            # Fetch video statistics
            stats_params = {"part": "statistics,contentDetails", "id": ",".join(video_ids), "key": api_key}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()
            
            if "items" not in stats_data:
                continue
                
            # Fetch channel statistics
            channel_params = {"part": "statistics,snippet", "id": ",".join(channel_ids), "key": api_key}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()
            
            if "items" not in channel_data:
                continue
                
            # Map video stats and channel data for easier access
            stats_map = {item["id"]: item for item in stats_data["items"]}
            channel_map = {item["id"]: item for item in channel_data["items"]}
            
            # Process each video
            for video in videos:
                video_id = video["id"]["videoId"]
                channel_id = video["snippet"]["channelId"]
                
                # Skip if we don't have stats or channel info
                if video_id not in stats_map or channel_id not in channel_map:
                    continue
                    
                # Get statistics
                video_stats = stats_map[video_id]["statistics"]
                channel_stats = channel_map[channel_id]["statistics"]
                
                # Get view count and subscriber count
                view_count = int(video_stats.get("viewCount", 0))
                subscriber_count = int(channel_stats.get("subscriberCount", 0))
                
                # Apply filters
                if view_count < min_views or subscriber_count > max_subscriber_count:
                    continue
                    
                # Parse and format dates
                published_at = video["snippet"]["publishedAt"]
                published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                
                # Parse duration
                duration = stats_map[video_id]["contentDetails"]["duration"]
                
                # Format duration from ISO 8601
                duration_str = duration.replace("PT", "")
                hours = 0
                minutes = 0
                seconds = 0
                
                if "H" in duration_str:
                    hours = int(duration_str.split("H")[0])
                    duration_str = duration_str.split("H")[1]
                
                if "M" in duration_str:
                    minutes = int(duration_str.split("M")[0])
                    duration_str = duration_str.split("M")[1]
                    
                if "S" in duration_str:
                    seconds = int(duration_str.split("S")[0])
                
                formatted_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
                
                # Channel info
                channel_title = channel_map[channel_id]["snippet"]["title"]
                
                # Likes, comments, etc
                like_count = int(video_stats.get("likeCount", 0))
                comment_count = int(video_stats.get("commentCount", 0))
                
                # Save the result
                all_results.append({
                    "Title": video["snippet"]["title"],
                    "Description": video["snippet"]["description"][:200] + "..." if len(video["snippet"]["description"]) > 200 else video["snippet"]["description"],
                    "Full Description": video["snippet"]["description"],
                    "Video ID": video_id,
                    "URL": f"https://www.youtube.com/watch?v={video_id}",
                    "Thumbnail": video["snippet"]["thumbnails"]["high"]["url"],
                    "Channel Name": channel_title,
                    "Channel ID": channel_id,
                    "Channel URL": f"https://www.youtube.com/channel/{channel_id}",
                    "Published Date": published_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "Duration": formatted_duration,
                    "Views": view_count,
                    "Likes": like_count,
                    "Comments": comment_count,
                    "Subscribers": subscriber_count,
                    "Engagement Rate": round((like_count + comment_count) / view_count * 100, 2) if view_count > 0 else 0,
                    "Keyword": keyword,
                    "Raw Published Date": published_date  # Keep the actual datetime for sorting
                })
                
        except Exception as e:
            st.sidebar.error(f"Error processing keyword '{keyword}': {str(e)}")
    
    # Update progress to 100%
    progress_bar.progress(1.0)
    status_text.text("Search completed!")
    
    # Remove duplicates based on Video ID
    unique_results = []
    seen_video_ids = set()
    
    for result in all_results:
        if result["Video ID"] not in seen_video_ids:
            seen_video_ids.add(result["Video ID"])
            unique_results.append(result)
    
    return unique_results

def apply_filters(results, filters):
    """Apply filters to the results"""
    filtered = results.copy()
    
    # Min views filter
    if filters.get("min_views", 0) > 0:
        filtered = [r for r in filtered if r["Views"] >= filters["min_views"]]
    
    # Max views filter
    if filters.get("max_views", 0) > 0:
        filtered = [r for r in filtered if r["Views"] <= filters["max_views"]]
    
    # Min subscribers filter
    if filters.get("min_subscribers", 0) > 0:
        filtered = [r for r in filtered if r["Subscribers"] >= filters["min_subscribers"]]
    
    # Max subscribers filter
    if filters.get("max_subscribers", 0) > 0:
        filtered = [r for r in filtered if r["Subscribers"] <= filters["max_subscribers"]]
    
    # Min engagement rate filter
    if filters.get("min_engagement", 0) > 0:
        filtered = [r for r in filtered if r["Engagement Rate"] >= filters["min_engagement"]]
    
    # Keyword filter
    if filters.get("keyword", "") != "":
        keyword = filters["keyword"].lower()
        filtered = [r for r in filtered if keyword in r["Title"].lower() or 
                                            keyword in r["Description"].lower() or 
                                            keyword in r["Keyword"].lower() or
                                            keyword in r["Channel Name"].lower()]
    
    # Date filter
    if filters.get("date_range") == "today":
        today = datetime.now().date()
        filtered = [r for r in filtered if r["Raw Published Date"].date() == today]
    elif filters.get("date_range") == "yesterday":
        yesterday = (datetime.now() - timedelta(days=1)).date()
        filtered = [r for r in filtered if r["Raw Published Date"].date() == yesterday]
    elif filters.get("date_range") == "last_week":
        week_ago = (datetime.now() - timedelta(days=7)).date()
        filtered = [r for r in filtered if r["Raw Published Date"].date() >= week_ago]
    elif filters.get("date_range") == "last_month":
        month_ago = (datetime.now() - timedelta(days=30)).date()
        filtered = [r for r in filtered if r["Raw Published Date"].date() >= month_ago]
    
    # Custom date range
    if filters.get("custom_start_date") and filters.get("custom_end_date"):
        start = filters["custom_start_date"]
        end = filters["custom_end_date"]
        filtered = [r for r in filtered if start <= r["Raw Published Date"].date() <= end]
    
    return filtered

def generate_charts(results):
    """Generate analytics charts from results"""
    if not results:
        return None, None, None, None
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(results)
    
    # 1. Views distribution by keywords
    keyword_views = df.groupby("Keyword")["Views"].sum().reset_index()
    keyword_views = keyword_views.sort_values("Views", ascending=False)
    
    views_by_keyword = px.bar(
        keyword_views, 
        x="Keyword", 
        y="Views", 
        title="Total Views by Keyword",
        color="Views",
        color_continuous_scale="reds"
    )
    views_by_keyword.update_layout(xaxis_title="Keyword", yaxis_title="Total Views")
    
    # 2. Subscriber distribution
    subscriber_bins = [0, 1000, 5000, 10000, 50000, 100000, float('inf')]
    subscriber_labels = ["0-1K", "1K-5K", "5K-10K", "10K-50K", "50K-100K", "100K+"]
    
    df["Subscriber Range"] = pd.cut(df["Subscribers"], bins=subscriber_bins, labels=subscriber_labels)
    subscriber_counts = df["Subscriber Range"].value_counts().reset_index()
    subscriber_counts.columns = ["Subscriber Range", "Count"]
    
    subscriber_chart = px.pie(
        subscriber_counts, 
        values="Count", 
        names="Subscriber Range", 
        title="Videos by Channel Size",
        color_discrete_sequence=px.colors.sequential.Reds
    )
    
    # 3. Publication time analysis
    df["Publication Hour"] = df["Raw Published Date"].apply(lambda x: x.hour)
    hourly_distribution = df.groupby("Publication Hour").size().reset_index()
    hourly_distribution.columns = ["Hour", "Count"]
    
    publication_time_chart = px.line(
        hourly_distribution, 
        x="Hour", 
        y="Count", 
        title="Publication Time Distribution (24-hour)",
        markers=True
    )
    publication_time_chart.update_layout(xaxis_title="Hour of Day", yaxis_title="Number of Videos")
    
    # 4. Engagement rate vs Views
    engagement_chart = px.scatter(
        df,
        x="Views",
        y="Engagement Rate",
        color="Subscribers",
        size="Comments",
        hover_name="Title",
        color_continuous_scale="reds",
        title="Engagement Rate vs. Views"
    )
    engagement_chart.update_layout(xaxis_title="Views", yaxis_title="Engagement Rate (%)")
    
    return views_by_keyword, subscriber_chart, publication_time_chart, engagement_chart

# Sidebar
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>Settings</h2>", unsafe_allow_html=True)
    
    # API Key input
    api_key = st.text_input("YouTube API Key:", type="password", value=st.session_state.api_key)
    st.session_state.api_key = api_key
    
    # Tabs for different sidebar sections
    sidebar_tab1, sidebar_tab2, sidebar_tab3 = st.tabs(["Search Parameters", "Filters", "Saved Searches"])
    
    # Tab 1: Search Parameters
    with sidebar_tab1:
        st.subheader("Search Parameters")
        
        # Date range selection
        days = st.slider("Days to Search:", min_value=1, max_value=30, value=7)
        
        # Results per keyword
        max_results_per_keyword = st.slider("Max Results per Keyword:", min_value=5, max_value=50, value=10)
        
        # Order by options
        order_by_options = {
            "viewCount": "View Count (High to Low)",
            "relevance": "Relevance",
            "date": "Date (Newest First)",
            "rating": "Rating"
        }
        order_by = st.selectbox("Order Results By:", options=list(order_by_options.keys()), 
                                format_func=lambda x: order_by_options[x])
        
        # Initial filters
        min_views = st.number_input("Minimum Views:", min_value=0, value=1000)
        max_subscriber_count = st.number_input("Maximum Subscriber Count:", min_value=0, value=10000)
        
        # Keywords input
        st.subheader("Keywords")
        default_keywords = """Affair Relationship Stories
Reddit Update
Reddit Relationship Advice
Reddit Relationship
Reddit Cheating
AITA Update
Open Marriage
Open Relationship"""
        
        keywords_text = st.text_area("Enter keywords (one per line):", value=default_keywords, height=200)
        keywords = [k.strip() for k in keywords_text.splitlines() if k.strip()]
        
        st.info(f"Total keywords: {len(keywords)}")
        
        # Search button
        if st.button("Start Search", use_container_width=True):
            if not api_key:
                st.error("Please enter your YouTube API Key")
            elif not keywords:
                st.error("Please enter at least one keyword")
            else:
                with st.spinner("Searching YouTube..."):
                    # Store search parameters
                    st.session_state.last_search_params = {
                        "days": days,
                        "min_views": min_views,
                        "max_subscriber_count": max_subscriber_count,
                        "keywords": keywords,
                        "order_by": order_by,
                        "max_results_per_keyword": max_results_per_keyword
                    }
                    
                    # Fetch data
                    results = fetch_youtube_data(
                        api_key=api_key,
                        keywords=keywords,
                        days=days,
                        max_results_per_keyword=max_results_per_keyword,
                        min_views=min_views,
                        max_subscriber_count=max_subscriber_count,
                        order_by=order_by
                    )
                    
                    # Store results in session state
                    st.session_state.results = results
                    st.session_state.filtered_results = results
                    st.session_state.search_complete = True
                    st.session_state.page = 1
    
    # Tab 2: Filters
    with sidebar_tab2:
        st.subheader("Filter Results")
        
        # Only show filters if we have results
        if st.session_state.search_complete and len(st.session_state.results) > 0:
            # View count range
            st.write("View Count Range")
            min_views_filter = st.number_input("Min Views:", min_value=0, value=0)
            max_views_filter = st.number_input("Max Views:", min_value=0, value=0)
            
            # Subscriber range
            st.write("Subscriber Range")
            min_subs_filter = st.number_input("Min Subscribers:", min_value=0, value=0)
            max_subs_filter = st.number_input("Max Subscribers:", min_value=0, value=0)
            
            # Engagement rate
            min_engagement = st.number_input("Min Engagement Rate (%):", min_value=0.0, value=0.0, step=0.1)
            
            # Date filter
            date_range = st.select_slider(
                "Date Range:",
                options=["all", "last_month", "last_week", "yesterday", "today", "custom"],
                value="all"
            )
            
            custom_start_date = None
            custom_end_date = None
            if date_range == "custom":
                col1, col2 = st.columns(2)
                with col1:
                    custom_start_date = st.date_input("Start Date:", value=datetime.now() - timedelta(days=7))
                with col2:
                    custom_end_date = st.date_input("End Date:", value=datetime.now())
            
            # Keyword text search
            keyword_filter = st.text_input("Search in results:", "")
            
            # Apply filters button
            if st.button("Apply Filters", use_container_width=True):
                filters = {
                    "min_views": min_views_filter,
                    "max_views": max_views_filter,
                    "min_subscribers": min_subs_filter,
                    "max_subscribers": max_subs_filter,
                    "min_engagement": min_engagement,
                    "keyword": keyword_filter,
                    "date_range": date_range,
                    "custom_start_date": custom_start_date,
                    "custom_end_date": custom_end_date
                }
                
                # Apply filters
                st.session_state.filtered_results = apply_filters(st.session_state.results, filters)
                st.session_state.page = 1  # Reset to first page
                
            # Reset filters button
            if st.button("Reset Filters", use_container_width=True):
                st.session_state.filtered_results = st.session_state.results
            
            st.info(f"Showing {len(st.session_state.filtered_results)} of {len(st.session_state.results)} total results")
        else:
            st.info("Run a search to enable filtering")
    
    # Tab 3: Saved Searches
    with sidebar_tab3:
        st.subheader("Saved Searches")
        
        if st.session_state.search_complete and len(st.session_state.results) > 0:
            save_name = st.text_input("Save search as:", "viral_topics")
            
            if st.button("Save Current Results", use_container_width=True):
                with st.spinner("Saving results..."):
                    saved_file = save_results(save_name, {
                        "results": st.session_state.results,
                        "search_params": st.session_state.last_search_params,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.success(f"Saved {len(st.session_state.results)} results to {saved_file}")
        
        # Display saved searches
        if st.session_state.saved_searches:
            st.write("Previous searches:")
            
            for i, saved in enumerate(st.session_state.saved_searches):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{i+1}. {saved['filename']} ({saved['count']} results)")
                with col2:
                    if st.button(f"Load #{i+1}", key=f"load_{i}"):
                        with st.spinner("Loading saved search..."):
                            loaded_data = load_results(saved['filename'])
                            st.session_state.results = loaded_data["results"]
                            st.session_state.filtered_results = loaded_data["results"]
                            st.session_state.last_search_params = loaded_data["search_params"]
                            st.session_state.search_complete = True
                            st.success(f"Loaded {len(loaded_data['results'])} results")
        else:
            st.info("No saved searches yet. Run a search and save it to see it here.")

# Main content
st.markdown("<h1 class='main-header'>YouTube Viral Topics Analyzer</h1>", unsafe_allow_html=True)

# Show welcome message if no search has been done
if not st.session_state.search_complete:
    st.markdown("""
    <div class="info-box">
        <h3>Welcome to the YouTube Viral Topics Analyzer!</h3>
        <p>This tool helps you find trending content on YouTube based on keywords and filters. It's perfect for:</p>
        <ul>
            <li>Content creators looking for viral topic ideas</li>
            <li>Marketers researching trending content</li>
            <li>Researchers analyzing YouTube trends</li>
        </ul>
        <p>Get started by entering your YouTube API key and search parameters in the sidebar.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display sample image
    st.image("https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg", caption="Discover viral content on YouTube!")
    
    # How to use section
    with st.expander("How to Use This Tool"):
        st.markdown("""
        1. **Enter your YouTube API key** in the sidebar (you can get one from the [Google Cloud Console](https://console.cloud.google.com/))
        2. **Set search parameters** like days to search and maximum results per keyword
        3. **Enter keywords** you want to search for (one per line)
        4. **Click "Start Search"** to fetch results
        5. **Filter results** using the Filters tab in the sidebar
        6. **Analyze the data** in the charts and tables
        7. **Save your searches** for future reference
        """)
    
    with st.expander("About YouTube API Keys"):
        st.markdown("""
        To use this tool, you need a YouTube Data API v3 key. Here's how to get one:
        
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project
        3. Enable the YouTube Data API v3
        4. Create an API key
        5. Copy the API key and paste it into the sidebar
        
        Note: The YouTube API has a daily quota limit. Each search uses a portion of your quota.
        """)

# Show results if search is complete
elif st.session_state.search_complete:
    # Top metrics
    total_results = len(st.session_state.results)
    total_filtered = len(st.session_state.filtered_results)
    total_views = sum(r["Views"] for r in st.session_state.filtered_results)
    avg_engagement = sum(r["Engagement Rate"] for r in st.session_state.filtered_results) / total_filtered if total_filtered > 0 else 0
    
    # Display metrics
    st.markdown("<div class='sub-header'>Search Results Overview</div>", unsafe_allow_html=True)
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_filtered:,}</div>
            <div class="metric-label">Videos Found</div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_views:,}</div>
            <div class="metric-label">Total Views</div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col3:
        avg_views = int(total_views / total_filtered) if total_filtered > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_views:,}</div>
            <div class="metric-label">Avg. Views</div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_engagement:.2f}%</div>
            <div class="metric-label">Avg. Engagement Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Tabs for different views of the data
    tab1, tab2, tab3 = st.tabs(["Videos", "Analytics", "Export"])
    
    # Tab 1: Videos
    with tab1:
        # Sorting options
        st.subheader("Videos")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            sort_options = {
                "Views": "Views (High to Low)",
                "Subscribers": "Subscribers (Low to High)",
                "Engagement Rate": "Engagement Rate (High to Low)",
                "Raw Published Date": "Newest First"
            }
            sort_by = st.selectbox("Sort by:", options=list(sort_options.keys()), 
                                format_func=lambda x: sort_options[x])
        with col2:
            display_mode = st.radio("Display:", ["Cards", "Table"], horizontal=True)
        
        # Sort results
        sorted_results = sorted(
            st.session_state.filtered_results, 
            key=lambda x: x[sort_by], 
            reverse=sort_by != "Subscribers"
        )
        
        # Pagination
        items_per_page = st.session_state.items_per_page
        total_pages = max(1, (len(sorted_results) + items_per_page - 1) // items_per_page)
        
        if display_mode == "Cards":
            # Card view
            start_idx = (st.session_state.page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(sorted_results))
            
            # Display page info
            st.write(f"Showing {start_idx + 1}-{end_idx} of {len(sorted_results)} results")
            
            # Display results as cards
            for result in sorted_results[start_idx:end_idx]:
                st.markdown(f"""
                <div class="video-card">
                    <div style="display: flex; align-items: flex-start;">
                        <div style="flex: 0 0 200px; margin-right: 15px;">
                            <img src="{result['Thumbnail']}" style="width: 100%; border-radius: 5px;">
                        </div>
                        <div style="flex-grow: 1;">
                            <div class="video-title">{result['Title']}</div>
                            <div style="margin-top: 5px; font-size: 0.9rem;">{result['Description']}</div>
                            <div style="margin-top: 10px; font-size: 0.9rem;">
                                <span class="view-count">{result['Views']:,}</span> views • 
                                <span>{result['Duration']}</span> • 
                                Published on {result['Published Date'].split()[0]}
                            </div>
                            <div style="margin-top: 5px; font-size: 0.9rem;">
                                Channel: <b>{result['Channel Name']}</b> ({result['Subscribers']:,} subscribers)
                            </div>
                            <div style="margin-top: 5px; font-size: 0.9rem;">
                                <span style="background-color: #f0f0f0; padding: 3px 8px; border-radius: 3px;">{result['Keyword']}</span>
                                <span style="margin-left: 10px; background-color: #ffecec; padding: 3px 8px; border-radius: 3px;">
                                    {result['Engagement Rate']}% engagement
                                </span>
                            </div>
                            <div style="margin-top: 10px;">
                                <a href="{result['URL']}" target="_blank" style="background-color: #FF0000; color: white; padding: 5px 10px; border-radius: 3px; text-decoration: none;">
                                    Watch on YouTube
                                </a>
                                <a href="{result['Channel URL']}" target="_blank" style="margin-left: 10px; background-color: #606060; color: white; padding: 5px 10px; border-radius: 3px; text-decoration: none;">
                                    Visit Channel
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Pagination controls
            if total_pages > 1:
                cols = st.columns(7)
                
                with cols[0]:
                    if st.button("« First"):
                        st.session_state.page = 1
                        st.experimental_rerun()
                
                with cols[1]:
                    if st.button("‹ Prev") and st.session_state.page > 1:
                        st.session_state.page -= 1
                        st.experimental_rerun()
                
                # Page numbers
                for i in range(3):
                    page_num = st.session_state.page - 1 + i
                    if 0 < page_num <= total_pages:
                        with cols[i + 2]:
                            button_text = f"{page_num}"
                            if page_num == st.session_state.page:
                                button_text = f"[{page_num}]"
                            if st.button(button_text):
                                st.session_state.page = page_num
                                st.experimental_rerun()
                
                with cols[5]:
                    if st.button("Next ›") and st.session_state.page < total_pages:
                        st.session_state.page += 1
                        st.experimental_rerun()
                
                with cols[6]:
                    if st.button("Last »"):
                        st.session_state.page = total_pages
                        st.experimental_rerun()
        
        else:  # Table view
            # Convert to DataFrame
            df = pd.DataFrame(sorted_results)
            
            # Select columns for display
            if not df.empty:
                display_df = df[["Title", "Channel Name", "Subscribers", "Views", "Engagement Rate", "Published Date", "Keyword"]]
                
                # Build grid options
                gb = GridOptionsBuilder.from_dataframe(display_df)
                gb.configure_column("Title", width=300)
                gb.configure_column("Channel Name", width=150)
                gb.configure_column("Subscribers", width=120, type=["numericColumn", "numberColumnFilter"], valueFormatter="data.Subscribers.toLocaleString()")
                gb.configure_column("Views", width=120, type=["numericColumn", "numberColumnFilter"], valueFormatter="data.Views.toLocaleString()")
                gb.configure_column("Engagement Rate", width=120, type=["numericColumn", "numberColumnFilter"], valueFormatter="data.Engagement Rate.toFixed(2) + '%'")
                gb.configure_column("Published Date", width=150)
                gb.configure_column("Keyword", width=150)
                
                # Configure pagination
                gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
                
                # Sorting
                gb.configure_default_column(sortable=True, filterable=True)
                
                # Selection
                gb.configure_selection(selection_mode="single", use_checkbox=False)
                
                grid_options = gb.build()
                
                # Create the grid
                grid_response = AgGrid(
                    display_df,
                    gridOptions=grid_options,
                    allow_unsafe_jscode=True,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    height=600
                )
                
                # Show details if a row is selected
                if grid_response["selected_rows"]:
                    selected = grid_response["selected_rows"][0]
                    selected_title = selected["Title"]
                    
                
