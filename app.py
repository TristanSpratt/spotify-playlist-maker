import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables
load_dotenv()

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Spotify OAuth config (global, no token yet)
SCOPE = "user-library-read playlist-modify-public playlist-modify-private"
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope=SCOPE,
    show_dialog=True
)

#### Backend functions ####

def get_search_query_from_prompt(prompt):
    system_msg = (
        "You are a helpful assistant that converts user prompts into Spotify search query strings.\n"
        "You always respond with a short string that can be used to search for songs through the Spotify API.\n"
        "Use the following filters only, separated by spaces (no commas):\n"
        "- artist: (e.g., artist:\"Taylor Swift\")\n"
        "- album: (e.g., album:\"Thriller\")\n"
        "- genre: (e.g., genre:rock)\n"
        "- year: (e.g., year:1995 or year:2010-2020)\n"
        "- tag:new or tag:hipster (optional editorial tags)\n"
        "- isrc: or upc: (only if explicitly mentioned)\n\n"
        "If the user prompt is abstract or mood-based (e.g. 'I want to fall asleep', 'music for a rainy day'), do your best to infer appropriate search filters like genre or artist to match the vibe.\n"
        "Do not include any other filters like mood, tempo, or popularity.\n"
        "Do not reply with any explanation, only return the search query string."
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def get_search_results(sp, query):
    results = sp.search(q=query, type="track", limit=50)
    return [track["uri"] for track in results["tracks"]["items"]]

def create_playlist(sp, name, track_uris):
    user_id = sp.current_user()["id"]
    playlist = sp.user_playlist_create(user=user_id, name=name, public=True)
    sp.user_playlist_add_tracks(user=user_id, playlist_id=playlist["id"], tracks=track_uris)
    return playlist["external_urls"]["spotify"]

def generate_title(prompt):
    title_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Generate a very short title for this playlist prompt."},
            {"role": "user", "content": prompt}
        ]
    )
    return title_response.choices[0].message.content.strip()

#### Frontend ####

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Vibe Maker", layout="centered")
st.markdown("<style>body { font-family: 'Helvetica Neue', sans-serif; }</style>", unsafe_allow_html=True)
st.markdown("## 🎶 Vibe Maker 🎶")

# --- Spotify Login Flow --- #

token_info = None
query_params = st.query_params

# Step 1: Handle Spotify redirect and get token from auth code
if "code" in query_params and "token_info" not in st.session_state:
    code = query_params["code"][0]
    try:
        token_info = sp_oauth.get_access_token(code)
        if token_info:
            st.session_state["token_info"] = token_info
            st.query_params.pop("code")
            st.rerun()
        else:
            st.error("Failed to retrieve Spotify token.")
            st.stop()
    except Exception as e:
        st.error("Spotify authentication failed.")
        st.exception(e)
        st.stop()

# Step 2: If we already have a token, use it
if "token_info" in st.session_state:
    token_info = st.session_state["token_info"]
else:
    # Step 3: Prompt user to log in
    st.markdown("To generate your own playlists, please:")
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f"[Log in to Spotify]({auth_url})")
    st.stop()

# Step 4: Create Spotipy client with user token
sp = spotipy.Spotify(auth=token_info["access_token"])

# --- Main UI Content --- #
st.success("You're logged in!")
st.markdown("---")
st.markdown("*Describe the vibe you're going for, and I'll generate a playlist on your Spotify*")

prompt = st.text_input("Your playlist idea:", placeholder="e.g., I need some chill music to study to")

if st.button("Make My Playlist"):
    with st.spinner("🎵 Cooking up some sounds..."):
        try:
            query = get_search_query_from_prompt(prompt)
            logger.info(f"Query string sent to Spotify: {query}")  # for debugging

            track_uris = get_search_results(sp, query)
            if not track_uris:
                st.error("😕 Sorry, couldn't find any songs for that vibe. Try rewording your prompt!")
                st.stop()
            title = generate_title(prompt)
            playlist_url = create_playlist(sp, title, track_uris)

            st.balloons()
            st.success(f"✅ Playlist created: **{title}**")
            st.markdown(f"🔗 [Open on Spotify]({playlist_url})")

        except Exception as e:
            st.error("Something went wrong while generating the playlist.")
            st.exception(e)
