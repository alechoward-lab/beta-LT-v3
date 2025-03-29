import streamlit as st
socials_banner = st.markdown(
    """
    <style>
        .social-bar {
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: transparent; /* Transparent background */
            padding: 5px;
            border: 2px solid white; /* White border */
            border-radius: 8px;
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
        }
        .social-bar .left-content {
            display: flex;
            align-items: center;
            margin-right: auto; /* Aligns logo and text to the left */
        }
        .social-bar .left-content .logo {
            height: 40px;
            margin-right: 10px;
        }
        .social-bar .social-links {
            display: flex;
            justify-content: center;
        }
        .social-links a {
            margin-right: 20px; /* Increased margin between logos */
            transition: opacity 0.3s ease-in-out;
        }
        .social-links a:hover {
            opacity: 0.7;
        }
        .social-text {
            font-family: Arial, sans-serif;
            font-size: 16px;
            font-weight: bold;
            margin-right: 15px;
            color: white;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
        }
    </style>
    <div class="social-bar">
        <div class="left-content">
            <img class="logo" src="https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/logo/Daring_Lime_Logo.png?raw=true" alt="Your Logo">
            <span class="social-text">Click the icons to see my YouTube Channel and Discord:</span>
        </div>
        <div class="social-links">
            <a href="https://www.youtube.com/channel/UCpV2UWmBTAeIKUso1LkeU2A" target="_blank">
                <img src="https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/logo/youtube_logo.png?raw=true" alt="YouTube" style="height: 30px;">
            </a>
            <a href="https://discord.gg/ReF5jDSHqV" target="_blank">
                <img src="https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/logo/Discord-Logo.png?raw=true" alt="Discord" style="height: 30px;">
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)