"""
YouTube Channel - Watch videos from Daring Lime
"""

import streamlit as st
try:
    import yt_dlp
except ImportError:
    yt_dlp = None
from components.nav_banner import render_nav_banner, render_page_header, render_footer

render_nav_banner("youtube-channel")

render_page_header("Daring Lime Videos", "Marvel Champions gameplay, strategy, and tier list breakdowns")

# Fetch videos from the channel
st.markdown("### 📺 Latest Videos")

@st.cache_data(ttl=3600)
def get_channel_videos():
    """Fetch all public videos from the channel using yt-dlp"""
    if yt_dlp is None:
        return []
    try:
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

if yt_dlp is None:
    st.warning("The `yt-dlp` package is not installed. Install it with `pip install yt-dlp` to load videos.")
    videos = []
else:
    with st.spinner("Loading videos..."):
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
                        <img src="{video['thumbnail']}" width="100%" loading="lazy" style="border-radius: 8px; cursor: pointer;">
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

render_footer()
