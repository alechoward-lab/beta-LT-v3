"""
YouTube Channel - Watch videos from Daring Lime
"""

import streamlit as st
import yt_dlp
from datetime import datetime

# Add header with logo similar to homepage
st.markdown(
    """
    <style>
        .header-bar {
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: transparent;
            padding: 5px;
            border: 2px solid white;
            border-radius: 8px;
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
        }
        .header-bar .logo {
            height: 50px;
            margin-right: 15px;
        }
        .header-title {
            font-family: Arial, sans-serif;
            font-size: 28px;
            font-weight: bold;
            color: white;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
        }
    </style>
    <div class="header-bar">
        <img class="logo" src="https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/logo/Daring_Lime_Logo.png?raw=true" alt="Daring Lime Logo">
        <span class="header-title">Daring-Lime-Videos</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Fetch videos from the channel
st.markdown("### 📺 Latest Videos")

@st.cache_data(ttl=3600)
def get_channel_videos():
    """Fetch all public videos from the channel using yt-dlp"""
    try:
        with st.spinner("Loading videos..."):
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist',
                'playlist_items': '1:100',  # Get first 100 videos
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info('https://www.youtube.com/channel/UCpV2UWmBTAeIKUso1LkeU2A/videos', download=False)
                videos = []
                
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:  # Skip None entries
                            video_id = entry.get('id', '')
                            # Construct thumbnail URL from video_id
                            thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                            
                            videos.append({
                                'title': entry.get('title', 'Untitled'),
                                'video_id': video_id,
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'thumbnail': thumbnail,
                                'upload_date': entry.get('upload_date', ''),
                            })
                return videos
    except Exception as e:
        st.error(f"Error loading videos: {e}")
        return []

videos = get_channel_videos()

if videos:
    # Display videos in a grid using Streamlit components
    cols = st.columns(2)
    for idx, video in enumerate(videos):
        with cols[idx % 2]:
            # Make thumbnail a clickable link
            if video['thumbnail']:
                st.markdown(
                    f"""
                    <a href="{video['url']}" target="_blank" style="text-decoration: none;">
                        <img src="{video['thumbnail']}" width="100%" style="border-radius: 8px; cursor: pointer;">
                    </a>
                    """,
                    unsafe_allow_html=True
                )
            
            # Display video title
            st.subheader(video['title'])
            
            # Display upload date
            if video['upload_date'] and len(video['upload_date']) >= 8:
                date_str = f"{video['upload_date'][:4]}-{video['upload_date'][4:6]}-{video['upload_date'][6:8]}"
                st.caption(f"📅 {date_str}")
            
            st.divider()
else:
    st.info("Loading videos or none available at the moment.")

st.markdown("---")

# Information box
st.info(
    """
    🎥 **Tip:** Click any video thumbnail to watch it on YouTube! 
    You can also like, comment, and subscribe directly on YouTube.
    """
)
