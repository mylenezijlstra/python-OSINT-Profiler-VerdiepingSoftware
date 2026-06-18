import streamlit as st
import asyncio
import httpx
from profiler import OSINTProfiler
import pandas as pd
import security

# Set page config for a premium feel
st.set_page_config(
    page_title="OSINT Profiler",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
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

def show_scanner():
    st.subheader("🔍 Scan Profile")
    
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
                    label = f"{first_name} {last_name}"
                    fb_url = f"https://www.facebook.com/search/people/?q={first_name}%20{last_name}"
                    li_url = f"https://www.linkedin.com/search/results/all/?keywords={first_name}%20{last_name}"
                    google_url = f"https://www.google.com/search?q=%22{first_name}+{last_name}%22"
                else:
                    results = loop.run_until_complete(profiler.scan(username=direct_username))
                    label = direct_username
                    fb_url = f"https://www.facebook.com/{direct_username}"
                    li_url = f"https://www.linkedin.com/in/{direct_username}"
                    google_url = f"https://www.google.com/search?q=%22{direct_username}%22"
                
                # Build combined card list: FB + LI always present, then other found platforms
                all_cards = [
                    {"platform": "Facebook", "username": label, "url": fb_url},
                    {"platform": "LinkedIn", "username": label, "url": li_url},
                ] + [r for r in results if r["status"] == "Found" and r["platform"] not in ("Facebook", "LinkedIn")]
                
                # Save scan to session state
                st.session_state.last_scan_mode = search_mode
                st.session_state.last_scan_query = label
                st.session_state.last_scan_results = all_cards
                st.session_state.last_scan_google_url = google_url
                st.session_state.save_success = False

    # Display results if present
    if "last_scan_results" in st.session_state:
        st.markdown("---")
        
        # Header with Save Button
        col_header, col_save = st.columns([3, 1])
        with col_header:
            st.subheader(f"Results for: {st.session_state.last_scan_query}")
        with col_save:
            if st.button("💾 SAVE PROFILE"):
                security.save_profile(
                    search_mode=st.session_state.last_scan_mode,
                    search_query=st.session_state.last_scan_query,
                    results=st.session_state.last_scan_results,
                    key=st.session_state.encryption_key
                )
                st.session_state.save_success = True
                
        if st.session_state.get("save_success"):
            st.success("Profile successfully encrypted and saved to your history database!")
            
        all_cards = st.session_state.last_scan_results
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
        st.link_button("Search on Google", st.session_state.last_scan_google_url)

def show_saved_profiles():
    st.subheader("📋 Saved Profiles")
    st.markdown("All data in this dashboard is encrypted at rest and decrypted in memory only.")
    
    profiles = security.get_saved_profiles(st.session_state.encryption_key)
    
    if not profiles:
        st.info("No saved profiles found. Start by scanning and saving profiles in the scanner.")
        return
        
    profile_options = {}
    for p in profiles:
        label = f"{p['search_query']} ({p['search_mode']} | {p['created_at']})"
        profile_options[label] = p
        
    selected_label = st.selectbox("Select a Profile to view details:", list(profile_options.keys()))
    
    if selected_label:
        profile = profile_options[selected_label]
        
        st.markdown("---")
        col_meta, col_del = st.columns([3, 1])
        with col_meta:
            st.markdown(f"### Profile: **{profile['search_query']}**")
            st.caption(f"Search Mode: {profile['search_mode']} | Saved: {profile['created_at']}")
        with col_del:
            if st.button("🗑️ DELETE PROFILE"):
                security.delete_saved_profile(profile['id'])
                st.success("Profile deleted successfully.")
                st.rerun()
                
        # Display the decrypted platform cards
        all_cards = profile['results']
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

def main():
    st.title("🛡️ OSINT Profiler Hub")
    
    # Initialize SQLite database schema
    security.init_db()
    
    # Initialize authentication session states
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "encryption_key" not in st.session_state:
        st.session_state.encryption_key = None
        
    # Check if master password exists
    if not security.is_master_password_set():
        st.subheader("Database Setup Required")
        st.warning("To protect personal intelligence data, a Master Password is required to initialize AES-256 local database encryption.")
        
        with st.form("setup_form"):
            password = st.text_input("Create Master Password", type="password", help="Use a strong password. This cannot be recovered.")
            confirm = st.text_input("Confirm Master Password", type="password")
            submitted = st.form_submit_button("INITIALIZE SYSTEM")
            
            if submitted:
                if not password:
                    st.error("Password cannot be empty.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    key = security.set_master_password(password)
                    st.session_state.authenticated = True
                    st.session_state.encryption_key = key
                    st.success("Master password created! Database is now initialized and unlocked.")
                    st.rerun()
        return

    # If master password exists, prompt login if not authenticated
    if not st.session_state.authenticated:
        st.subheader("System Locked")
        st.info("Please enter your Master Password to decrypt and access the database.")
        
        with st.form("login_form"):
            password = st.text_input("Master Password", type="password")
            submitted = st.form_submit_button("UNLOCK SYSTEM")
            
            if submitted:
                key = security.verify_password(password)
                if key:
                    st.session_state.authenticated = True
                    st.session_state.encryption_key = key
                    st.success("System Unlocked.")
                    st.rerun()
                else:
                    st.error("Incorrect Master Password.")
        return

    # --- Authenticated App View ---
    st.sidebar.title("🔐 Secure Session")
    
    # Navigation
    menu = st.sidebar.radio("Navigation", ["🔍 Profile Scanner", "📋 Saved Profiles"])
    
    # Logout action
    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 LOCK / LOGOUT"):
        st.session_state.authenticated = False
        st.session_state.encryption_key = None
        # Clean scan buffers
        st.session_state.pop("last_scan_results", None)
        st.session_state.pop("last_scan_mode", None)
        st.session_state.pop("last_scan_query", None)
        st.session_state.pop("last_scan_google_url", None)
        st.rerun()
        
    # Render selected view
    if menu == "🔍 Profile Scanner":
        show_scanner()
    elif menu == "📋 Saved Profiles":
        show_saved_profiles()

if __name__ == "__main__":
    main()