import streamlit as st
import asyncio
import httpx
from profiler import OSINTProfiler
import pandas as pd

# Set page config for a premium feel
st.set_page_config(
    page_title="OSINT Profiler",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for that premium look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        background-color: #00f2ff;
        color: black;
        border-radius: 10px;
        font-weight: bold;
        width: 100%;
        border: none;
        padding: 10px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.5);
        transform: translateY(-2px);
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    .profile-card {
        background-color: #1a1c24;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #00f2ff;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title(" OSINT Profiler")
    st.markdown("### Digital Identity Mapping Engine")
    
    search_mode = st.radio("Search Mode", ["By Name", "By Username"], horizontal=True)
    
    first_name = None
    last_name = None
    direct_username = None
    
    if search_mode == "By Name":
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name", placeholder="e.g. John")
        with col2:
            last_name = st.text_input("Last Name", placeholder="e.g. Doe")
    else:
        direct_username = st.text_input("Username", placeholder="e.g. johndoe123")
        
    if st.button("INITIATE SCAN"):
        if search_mode == "By Name" and (not first_name or not last_name):
            st.error("Please enter both names.")
        elif search_mode == "By Username" and not direct_username:
            st.error("Please enter a username.")
        else:
            with st.spinner("Scanning Global Networks..."):
                # Initialize profiler
                profiler = OSINTProfiler()
                
                # Run the scan asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                if search_mode == "By Name":
                    results = loop.run_until_complete(profiler.scan(first=first_name, last=last_name))
                else:
                    results = loop.run_until_complete(profiler.scan(username=direct_username))
                
                # Display Results
                st.markdown("---")
                st.subheader("Found Profiles")

                # Build Facebook and LinkedIn links based on search mode
                if search_mode == "By Name":
                    label = f"{first_name} {last_name}"
                    fb_url = f"https://www.facebook.com/search/people/?q={first_name}%20{last_name}"
                    li_url = f"https://www.linkedin.com/search/results/all/?keywords={first_name}%20{last_name}"
                    google_url = f"https://www.google.com/search?q=%22{first_name}+{last_name}%22"
                else:
                    label = direct_username
                    fb_url = f"https://www.facebook.com/{direct_username}"
                    li_url = f"https://www.linkedin.com/in/{direct_username}"
                    google_url = f"https://www.google.com/search?q=%22{direct_username}%22"

                # Build combined card list: FB + LI always present, then other found platforms
                all_cards = [
                    {"platform": "Facebook", "username": label, "url": fb_url},
                    {"platform": "LinkedIn", "username": label, "url": li_url},
                ] + [r for r in results if r["status"] == "Found" and r["platform"] not in ("Facebook", "LinkedIn")]

                cols = st.columns(3)
                for idx, card in enumerate(all_cards):
                    if idx > 0 and idx % 3 == 0:
                        cols = st.columns(3)
                    with cols[idx % 3]:
                        st.markdown(f"""
                            <div class="profile-card">
                                <h4>{card['platform']}</h4>
                                <p>@{card['username']}</p>
                                <a href="{card['url']}" target="_blank" style="color: #00f2ff; text-decoration: none; font-weight: bold;">View Profile →</a>
                            </div>
                        """, unsafe_allow_html=True)

                # Google Search button at the bottom
                st.markdown("---")
                st.link_button("Search on Google", google_url)

if __name__ == "__main__":
    main()