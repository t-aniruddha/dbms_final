import streamlit as st
import pandas as pd
from db_connection import get_connection

st.set_page_config(page_title="🎵 Music DBMS Frontend", layout="wide")
st.title("🎶 Music Database Management System")

menu = menu = ["View Tables", "Add Song", "Search Songs", "View Playlists", "User Playlists"]

choice = st.sidebar.selectbox("Menu", menu)

conn = get_connection()
cursor = conn.cursor(dictionary=True)

if choice == "View Tables":
    st.header("📋 View Tables")
    tables = ["users", "songs", "albums", "artists", "playlists"]
    selected = st.selectbox("Choose a table", tables)
    cursor.execute(f"SELECT * FROM {selected}")
    rows = cursor.fetchall()
    st.dataframe(pd.DataFrame(rows))

elif choice == "Add Song":
    st.header("➕ Add New Song")
    sid = st.text_input("Song ID")
    title = st.text_input("Title")
    release = st.date_input("Release Date")
    duration = st.text_input("Duration (HH:MM:SS)")
    link = st.text_input("Song Link")

    if st.button("Add Song"):
        cursor.execute(
            "INSERT INTO songs (songId, title, releaseDate, duration, song_link) VALUES (%s, %s, %s, %s, %s)",
            (sid, title, release, duration, link)
        )
        conn.commit()
        st.success(f"✅ '{title}' added successfully!")

elif choice == "Search Songs":
    st.header("🔍 Search Songs by Title")
    query = st.text_input("Enter song title")
    if query:
        cursor.execute("SELECT * FROM songs WHERE title LIKE %s", (f"%{query}%",))
        st.dataframe(pd.DataFrame(cursor.fetchall()))

elif choice == "View Playlists":
    st.header("🎧 Playlists Overview")
    cursor.execute("""
        SELECT p.playlistId, p.name, p.status, p.tracks, p.total_duration, u.firstName AS owner
        FROM playlists p
        JOIN users u ON p.userId = u.userId
    """)
    st.dataframe(pd.DataFrame(cursor.fetchall()))

elif choice == "User Playlists":
    st.header("🎧 View Playlists Owned by a User")

    # Open a new DB connection
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Step 1: Fetch all users
        cursor.execute("SELECT userId, firstName, lastName FROM users ORDER BY userId")
        users = cursor.fetchall()

        if not users:
            st.warning("⚠️ No users found in the database.")
        else:
            # Step 2: Build dropdown for user selection
            user_dict = {f"{u['userId']} - {u['firstName']} {u['lastName']}": u['userId'] for u in users}
            selected_user = st.selectbox("Select a user", list(user_dict.keys()))

            if selected_user:
                user_id = user_dict[selected_user]

                # Step 3: Fetch playlists for that user
                cursor.execute("""
                    SELECT p.playlistId, p.name, p.status, p.tracks, p.total_duration
                    FROM playlists p
                    WHERE p.userId = %s
                """, (user_id,))
                playlists = cursor.fetchall()

                if playlists:
                    st.success(f"✅ Found {len(playlists)} playlist(s) owned by {selected_user}")
                    st.dataframe(pd.DataFrame(playlists))
                else:
                    st.info(f"ℹ️ No playlists found for {selected_user}")
    except Exception as e:
        st.error(f"❌ Database error: {e}")
    finally:
        cursor.close()
        conn.close()



cursor.close()
conn.close()
