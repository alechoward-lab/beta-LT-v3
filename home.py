    """
    The Living Marvel Champions Tier List
    """
    #%%
    import streamlit as st
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    import pandas as pd
    import copy
    import os
    from PIL import Image
    import json
    from hero_image_urls import hero_image_urls
    from default_heroes import default_heroes
    from preset_options import preset_options
    from help_tips import help_tips

    # Socials banner (unchanged)
    socials_banner = st.markdown(
        """
        <style>
            .social-bar {
                display: flex;
                justify-content: center;
                align-items: center;
                background-color: transparent;
                padding: 5px;
                border: 2px solid white;
                border-radius: 8px;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
            }
            .social-bar .left-content {
                display: flex;
                align-items: center;
                margin-right: auto;
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
                margin-right: 20px;
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
                <span class="social-text">Click the icons to see my YouTube channel and Discord:</span>
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

    # Callback and weighting UI (unchanged)
    def update_preset():
        preset = st.session_state.preset_choice
        if preset != "Custom":
            vals = preset_options[preset]
            keys = ["Economy","Tempo","Card Value","Survivability","Villain Damage","Threat Removal",
                    "Reliability","Minion Control","Control Boon","Support Boon","Unique Broken Builds Boon",
                    "Late Game Power Boon","Simplicity","Stun/Confuse Boon","Multiplayer Consistency Boon"]
            for i,key in enumerate(keys):
                st.session_state[key] = int(vals[i])

    # Header and description
    st.title("The Living Tier List")
    st.subheader("For Marvel Champions Heroes by Daring Lime")
    st.markdown(
        "Adjust the weighting based on how much you value each aspect of hero strength. "
        "You can choose from preset weighting functions, adjust the sliders manually, or both! "
        "After updating the hero stats and weighting factors to your liking, you can save your settings and upload them next time you return to the site."
    )
    st.markdown(
        "For a video tutorial of how to use this, check out this YouTube video: [Daring Lime](https://youtu.be/TxU1NcryRS8). "
        "If you enjoy this tool, please consider subscribing to support more Marvel Champions content."
    )

    # Layout columns
    col1, col2 = st.columns(2)
    with col1:
        # ... weighting settings UI ...
        pass
    with col2:
        # ... hero stats UI ...
        pass

    # Use heroes from session state
    heroes = st.session_state.get('heroes', default_heroes)

    # Calculate weights and scores
    def compute_score(stats, w): return np.dot(stats, w)
    weighting = st.session_state.get('weighting', np.array(list(st.session_state.values())[:15]))
    scores = {h: compute_score(stats, weighting) for h, stats in heroes.items()}
    sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

    # Determine tier thresholds
    arr = np.array(list(scores.values()))
    m, s = arr.mean(), arr.std()
    thresholds = {
        'S': m+1.5*s, 'A': m+0.5*s, 'B': m-0.5*s, 'C': m-1.5*s
    }

    tiers = {'S':[], 'A':[], 'B':[], 'C':[], 'D':[]}
    for hero, sc in scores.items():
        if sc >= thresholds['S']:
            tiers['S'].append((hero, sc))
        elif sc >= thresholds['A']:
            tiers['A'].append((hero, sc))
        elif sc >= thresholds['B']:
            tiers['B'].append((hero, sc))
        elif sc >= thresholds['C']:
            tiers['C'].append((hero, sc))
        else:
            tiers['D'].append((hero, sc))
    for t in tiers: tiers[t].sort(key=lambda x: x[1], reverse=True)

    plot_title = st.session_state.get('preset_choice', 'Custom')
    st.header(f"{plot_title}")

    # Display tiers with local images
    for level in ['S','A','B','C','D']:
        st.markdown(f"<h2>{level}</h2>", unsafe_allow_html=True)
        rows = [tiers[level][i:i+5] for i in range(0, len(tiers[level]), 5)]
        for row in rows:
            cols = st.columns(5)
            for idx, (hero, _) in enumerate(row):
                with cols[idx]:
                    path = hero_image_urls.get(hero)
                    if path and os.path.exists(path):
                        img = Image.open(path)
                        st.image(img, caption=hero, use_container_width=True)
                    else:
                        st.write(f"Image for {hero} not found.")

    # Plotting
    st.header("Hero Scores")
    fig, ax = plt.subplots(figsize=(14,7), dpi=300)
    names, vals = zip(*sorted_scores.items())
    colors = [ {'S':'red','A':'orange','B':'green','C':'blue','D':'purple'}[next(t for t,v in scores.items() if t==n)] for n in names ]
    bars = ax.bar(names, vals, color=colors)
    ax.set_ylabel("Scores", fontsize="x-large")
    ax.set_title(plot_title, fontsize=18, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    legend = [Patch(color=c, label=f"Tier {t}") for t,c in {'S':'red','A':'orange','B':'green','C':'blue','D':'purple'}.items()]
    ax.legend(handles=legend, loc='upper left', fontsize='x-large', title="Tier")
    plt.tight_layout()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    st.pyplot(fig)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("-Stay Zesty")
    st.markdown("Most card images are from the Cerebro Discord bot developed by UnicornSnuggler. Thank you!")
