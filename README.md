# Vibe Maker 🎶

Vibe Maker is a Streamlit app that generates Spotify playlists from natural language prompts using the OpenAI Spotify APIs. It lets users create custom playlists by describing the mood they’re going for, like “I want something peaceful to wind down before bed” or “give me hype songs to get ready for a night out.” 

It uses:
- **OpenAI GPT-4o** to convert text prompts into structured Spotify search queries
- **Spotipy** (Spotify Web API) to fetch tracks and create playlists directly in the user's account
- **Streamlit** to provide a simple, interactive UI

## Features

- Spotify OAuth login (creates playlists in *your* Spotify account)
- Prompt-to-query LLM conversion (GPT-4o)
- Playlist creation with up to 50 tracks
- Automatic playlist title generation
- Streamlit mobile-friendly UI

## Try it!

Try it here: [https://spotify-playlist-maker.streamlit.app/](https://spotify-playlist-maker.streamlit.app/)

---

License
MIT License

Author
Tristan Spratt