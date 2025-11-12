import streamlit as st
import pandas as pd
import os
from db_connection import get_connection

st.set_page_config(page_title="🎵 Music DBMS Frontend", layout="wide")
st.title("🎶 Music Database Management System")

menu = [
    "View Tables",
    "Add Song",
    "Edit Song",
    "Search Songs",
    "View Playlists",
    "User Playlists",
    "View Songs in Playlist",
    "View Triggers & Procedures",
    "Manage Songs in Playlists",
    "Add Trigger",  # <-- existing
    "Add User"      # new menu item for adding users
]

choice = st.sidebar.radio("📋 Menu", menu)

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
    st.header("➕ Add a New Song")

    sid = st.text_input("Song ID")
    title = st.text_input("Title")
    release = st.date_input("Release Date")
    duration = st.text_input("Duration (HH:MM:SS)")
    link = st.text_input("Song Link")

    if st.button("Add Song"):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO songs (songId, title, releaseDate, duration, song_link) VALUES (%s, %s, %s, %s, %s)",
                (sid, title, release, duration, link)
            )
            conn.commit()
            st.success(f"✅ Song '{title}' added successfully!")
        except Exception as e:
            err_msg = str(e)
            # Detect trigger error message
            if "Song duration cannot be negative" in err_msg:
                st.error("⚠️ Song duration cannot be negative!")
            else:
                st.error(f"❌ Database error: {err_msg}")
        finally:
            cursor.close()
            conn.close()

        st.markdown("---")
        st.subheader("🗑️ Delete a Song")
        try:
            conn_d = get_connection()
            cur_d = conn_d.cursor(dictionary=True)
            cur_d.execute("SELECT songId, title FROM songs ORDER BY songId")
            songs_list = cur_d.fetchall()
            if not songs_list:
                st.info("No songs available to delete.")
            else:
                song_choices = {f"{s['songId']} - {s['title']}": s['songId'] for s in songs_list}
                selected_del = st.selectbox("Select a song to delete", list(song_choices.keys()))
                if st.button("Delete Song"):
                    sid_del = song_choices[selected_del]
                    try:
                        cur_del = conn_d.cursor()
                        cur_del.execute("DELETE FROM songs WHERE songId = %s", (sid_del,))
                        conn_d.commit()
                        st.success(f"✅ Deleted song {selected_del}")
                        # close and refresh
                        cur_del.close()
                        cur_d.close()
                        conn_d.close()
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to delete song: {e}")
        except Exception as e:
            st.error(f"❌ Could not load songs for deletion: {e}")
        finally:
            try:
                cur_d.close()
                conn_d.close()
            except Exception:
                pass


elif choice == "Search Songs":
    st.header("🔍 Search Songs by Title")

    query = st.text_input("Enter song title")

    if query:
        # Fetch matching songs
        cursor.execute("SELECT * FROM songs WHERE title LIKE %s", (f"%{query}%",))
        results = cursor.fetchall()

        if not results:
            st.warning("⚠️ No matching songs found.")
        else:
            df = pd.DataFrame(results)
            st.dataframe(df)

            # Select one of the found songs to play
            song_titles = [r["title"] for r in results]
            selected_song = st.selectbox("🎵 Select a song to play", song_titles)

            if selected_song:
                cursor.execute(
                    "SELECT song_link FROM songs WHERE title = %s", (selected_song,)
                )
                song_data = cursor.fetchone()

                if song_data and song_data["song_link"]:
                    link = song_data["song_link"]

                    st.markdown("---")
                    st.subheader(f"▶️ Now Playing: {selected_song}")

                    # For YouTube links → embed in an iframe
                    if "youtube.com" in link or "youtu.be" in link:
                        youtube_embed = link.replace("watch?v=", "embed/")
                        st.markdown(
                            f"""
                            <iframe width="700" height="394" 
                            src="{youtube_embed}"
                            frameborder="0" allow="autoplay; encrypted-media" allowfullscreen>
                            </iframe>
                            """,
                            unsafe_allow_html=True
                        )

                    # For Spotify links → Spotify embed
                    elif "spotify.com" in link:
                        st.markdown(
                            f"""
                            <iframe style="border-radius:12px" 
                            src="{link.replace('track', 'embed/track')}" 
                            width="700" height="394" frameborder="0" 
                            allow="autoplay; clipboard-write; encrypted-media; picture-in-picture" 
                            loading="lazy"></iframe>
                            """,
                            unsafe_allow_html=True
                        )

                    # Generic fallback (e.g. other links)
                    else:
                        st.info(f"🔗 [Open Song Link]({link})")
                else:
                    st.warning("⚠️ This song has no playable link.")

        

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

elif choice == "View Triggers":
    st.header("🧩 Database Triggers")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch triggers for the current database
        cursor.execute("""
            SELECT 
                TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE, ACTION_TIMING, ACTION_STATEMENT
            FROM information_schema.triggers
            WHERE trigger_schema = %s
            ORDER BY EVENT_OBJECT_TABLE;
        """, (os.getenv("DB_NAME"),))
        triggers = cursor.fetchall()

        if not triggers:
            st.info("ℹ️ No triggers found in the database.")
        else:
            st.success(f"✅ Found {len(triggers)} trigger(s) in database `project`")

            for trig in triggers:
                with st.expander(f"⚙️ {trig['TRIGGER_NAME']} ({trig['EVENT_MANIPULATION']} ON {trig['EVENT_OBJECT_TABLE']})"):
                    st.markdown(f"**Timing:** {trig['ACTION_TIMING']}")
                    st.markdown("**Definition:**")
                    st.code(trig['ACTION_STATEMENT'], language="sql")
    except Exception as e:
        st.error(f"❌ Error fetching triggers: {e}")
    finally:
        cursor.close()
        conn.close()

elif choice == "View Triggers & Procedures":
    st.header("🧠 Database Triggers & Stored Procedures")

    # Open new connection for safety
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    tab1, tab2 = st.tabs(["⚙️ Triggers", "📜 Stored Procedures"])

    # ==============================
    # TAB 1: TRIGGERS
    # ==============================
    with tab1:
        try:
            cursor.execute("""
                SELECT 
                    TRIGGER_NAME,
                    EVENT_MANIPULATION,
                    EVENT_OBJECT_TABLE,
                    ACTION_TIMING,
                    ACTION_STATEMENT,
                    DEFINER
                FROM information_schema.triggers
                WHERE trigger_schema = %s
                ORDER BY EVENT_OBJECT_TABLE;
            """, (os.getenv("DB_NAME"),))
            triggers = cursor.fetchall()

            if not triggers:
                st.info("ℹ️ No triggers found in this database.")
            else:
                st.success(f"✅ Found {len(triggers)} trigger(s)")
                for trig in triggers:
                    with st.expander(f"{trig['TRIGGER_NAME']} → {trig['EVENT_MANIPULATION']} ON {trig['EVENT_OBJECT_TABLE']}"):
                        st.markdown(f"**Timing:** {trig['ACTION_TIMING']}")
                        st.markdown(f"**Defined by:** `{trig['DEFINER']}`")
                        st.code(trig['ACTION_STATEMENT'], language="sql")
        except Exception as e:
            st.error(f"❌ Error fetching triggers: {e}")

    # ==============================
    # TAB 2: STORED PROCEDURES
    # ==============================
    with tab2:
        try:
            cursor.execute("""
                SELECT 
                    ROUTINE_NAME,
                    ROUTINE_TYPE,
                    CREATED,
                    LAST_ALTERED,
                    DEFINER,
                    ROUTINE_DEFINITION
                FROM information_schema.routines
                WHERE ROUTINE_SCHEMA = %s
                ORDER BY ROUTINE_TYPE, ROUTINE_NAME;
            """, (os.getenv("DB_NAME"),))
            procs = cursor.fetchall()

            if not procs:
                st.info("ℹ️ No stored procedures or functions found.")
            else:
                st.success(f"✅ Found {len(procs)} procedure(s)/function(s)")
                for proc in procs:
                    with st.expander(f"{proc['ROUTINE_TYPE']}: {proc['ROUTINE_NAME']}"):
                        st.markdown(f"**Created:** {proc['CREATED']}")
                        st.markdown(f"**Last Altered:** {proc['LAST_ALTERED']}")
                        st.markdown(f"**Defined by:** `{proc['DEFINER']}`")
                        st.code(proc['ROUTINE_DEFINITION'], language="sql")
        except Exception as e:
            st.error(f"❌ Error fetching stored procedures: {e}")

    cursor.close()
    conn.close()

elif choice == "Manage Songs in Playlists":
    st.header("🎵 Manage Song–Playlist Relationships")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Step 1: Search for a song
        search_term = st.text_input("🔍 Search for a song by title")

        if search_term:
            cursor.execute("""
                SELECT songId, title, releaseDate, duration 
                FROM songs 
                WHERE title LIKE %s
            """, (f"%{search_term}%",))
            results = cursor.fetchall()

            if not results:
                st.warning("⚠️ No songs found matching that title.")
            else:
                song_dict = {f"{s['songId']} - {s['title']}": s['songId'] for s in results}
                selected_song = st.selectbox("Select a song", list(song_dict.keys()))

                if selected_song:
                    song_id = song_dict[selected_song]

                    # Step 2: Display playlists containing this song
                    st.subheader("📂 Playlists containing this song:")
                    cursor.execute("""
                        SELECT p.playlistId, p.name, p.status, u.firstName AS owner
                        FROM playlistsongs ps
                        JOIN playlists p ON ps.playlistId = p.playlistId
                        JOIN users u ON p.userId = u.userId
                        WHERE ps.songId = %s
                    """, (song_id,))
                    containing_playlists = cursor.fetchall()

                    if containing_playlists:
                        st.dataframe(pd.DataFrame(containing_playlists))
                    else:
                        st.info("ℹ️ This song is not currently in any playlist.")

                    st.markdown("---")

                    # Step 3: Add this song to another playlist
                    st.subheader("➕ Add this song to another playlist")

                    cursor.execute("SELECT playlistId, name FROM playlists ORDER BY name")
                    playlists = cursor.fetchall()

                    playlist_dict = {f"{p['playlistId']} - {p['name']}": p['playlistId'] for p in playlists}
                    target_playlist = st.selectbox("Select a playlist to add into", list(playlist_dict.keys()))

                    if st.button("Add Song to Playlist"):
                        playlist_id = playlist_dict[target_playlist]
                        try:
                            cursor.execute("""
                                INSERT INTO playlistsongs (playlistId, songId)
                                VALUES (%s, %s)
                            """, (playlist_id, song_id))
                            conn.commit()
                            st.success(f"✅ Added song '{selected_song}' to playlist '{target_playlist}' successfully!")
                            st.rerun()
                        except Exception as e:
                            err_msg = str(e)
                            if "Duplicate entry" in err_msg:
                                st.error("⚠️ This song is already in that playlist.")
                            else:
                                st.error(f"❌ Database error: {err_msg}")
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

elif choice == "View Songs in Playlist":
    st.header("🎧 View Songs in a Playlist")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Step 1: Fetch all playlists
        cursor.execute("""
            SELECT p.playlistId, p.name, p.status, u.firstName AS owner
            FROM playlists p
            JOIN users u ON p.userId = u.userId
            ORDER BY p.name
        """)
        playlists = cursor.fetchall()

        if not playlists:
            st.warning("⚠️ No playlists found in the database.")
        else:
            # Step 2: Build dropdown
            playlist_dict = {f"{p['playlistId']} - {p['name']} (by {p['owner']})": p['playlistId'] for p in playlists}
            selected_playlist = st.selectbox("Select a playlist", list(playlist_dict.keys()))

            if selected_playlist:
                playlist_id = playlist_dict[selected_playlist]

                # Step 3: Fetch all songs in that playlist
                cursor.execute("""
                    SELECT s.songId, s.title, s.duration, s.releaseDate, s.song_link, a.name AS artist
                    FROM playlistsongs ps
                    JOIN songs s ON ps.songId = s.songId
                    LEFT JOIN artistsong ars ON s.songId = ars.songId
                    LEFT JOIN artists a ON ars.artistId = a.artistId
                    WHERE ps.playlistId = %s
                    ORDER BY s.title;
                """, (playlist_id,))
                songs = cursor.fetchall()

                if songs:
                    st.success(f"✅ Found {len(songs)} song(s) in '{selected_playlist}'")
                    df = pd.DataFrame(songs)
                    st.dataframe(df)

                    # Optional: Show total duration
                    cursor.execute("""
                        SELECT total_duration 
                        FROM playlists 
                        WHERE playlistId = %s
                    """, (playlist_id,))
                    total = cursor.fetchone()
                    if total and total['total_duration']:
                        minutes = total['total_duration'] // 60
                        seconds = total['total_duration'] % 60
                        st.info(f"⏱️ Total Duration: {minutes} min {seconds} sec")
                else:
                    st.info("ℹ️ No songs found in this playlist.")
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

elif choice == "Edit Song":
    st.header("✏️ Edit Existing Song")

    # Establish a new connection for this page
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Step 1: Fetch all songs
        cursor.execute("SELECT songId, title FROM songs ORDER BY songId")
        songs = cursor.fetchall()

        if not songs:
            st.warning("⚠️ No songs found in the database.")
        else:
            # Step 2: Dropdown to select a song
            song_dict = {f"{s['songId']} - {s['title']}": s['songId'] for s in songs}
            selected_song = st.selectbox("Select a song to edit", list(song_dict.keys()))

            if selected_song:
                song_id = song_dict[selected_song]

                # Step 3: Fetch that song’s full details
                cursor.execute("SELECT * FROM songs WHERE songId = %s", (song_id,))
                song = cursor.fetchone()

                if song:
                    st.subheader(f"Editing: {song['title']}")

                    # Step 4: Editable fields (pre-filled)
                    new_title = st.text_input("Title", song['title'])
                    new_release = st.date_input("Release Date", song['releaseDate'])
                    new_duration = st.text_input("Duration (HH:MM:SS)", song['duration'])
                    new_link = st.text_input("Song Link", song['song_link'])

                    # Step 5: Update button
                    if st.button("💾 Update Song"):
                        try:
                            cursor.execute("""
                                UPDATE songs 
                                SET title = %s, releaseDate = %s, duration = %s, song_link = %s
                                WHERE songId = %s
                            """, (new_title, new_release, new_duration, new_link, song_id))
                            conn.commit()
                            st.success(f"✅ Song '{new_title}' updated successfully!")
                            st.rerun()  # Refresh page to show updated data
                        except Exception as e:
                            err_msg = str(e)
                            if "duration cannot be negative" in err_msg.lower():
                                st.error("🚫 Song duration cannot be negative!")
                            else:
                                st.error(f"❌ Database error: {err_msg}")

    except Exception as e:
        st.error(f"❌ Error loading songs: {e}")

    finally:
        cursor.close()
        conn.close()

elif choice == "Add User":
    st.header("➕ Add a New User")

    user_id = st.text_input("User ID")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email (optional)")

    if st.button("Add User"):
        # Basic validation
        if not user_id.strip() or not first_name.strip() or not last_name.strip():
            st.error("Please provide User ID, First Name and Last Name.")
        else:
            conn_u = get_connection()
            cur_u = conn_u.cursor()
            try:
                cur_u.execute(
                    "INSERT INTO users (userId, firstName, lastName, email) VALUES (%s, %s, %s, %s)",
                    (user_id.strip(), first_name.strip(), last_name.strip(), email.strip() or None)
                )
                conn_u.commit()
                st.success(f"✅ User '{first_name} {last_name}' added successfully!")
            except Exception as e:
                msg = str(e)
                if "Duplicate entry" in msg:
                    st.error("⚠️ A user with that ID already exists.")
                else:
                    st.error(f"❌ Database error: {msg}")
            finally:
                try:
                    cur_u.close()
                    conn_u.close()
                except Exception:
                    pass

        st.markdown("---")
        st.subheader("🗑️ Delete a User")
        try:
            conn_ud = get_connection()
            cur_ud = conn_ud.cursor(dictionary=True)
            cur_ud.execute("SELECT userId, firstName, lastName FROM users ORDER BY userId")
            users_list = cur_ud.fetchall()
            if not users_list:
                st.info("No users available to delete.")
            else:
                user_choices = {f"{u['userId']} - {u['firstName']} {u['lastName']}": u['userId'] for u in users_list}
                sel_user = st.selectbox("Select a user to delete", list(user_choices.keys()))
                if st.button("Delete User"):
                    uid_del = user_choices[sel_user]
                    try:
                        cur_delu = conn_ud.cursor()
                        cur_delu.execute("DELETE FROM users WHERE userId = %s", (uid_del,))
                        conn_ud.commit()
                        st.success(f"✅ Deleted user {sel_user}")
                        cur_delu.close()
                        cur_ud.close()
                        conn_ud.close()
                        st.experimental_rerun()
                    except Exception as e:
                        # Likely FK constraint if user owns playlists etc.
                        st.error(f"❌ Failed to delete user: {e}")
        except Exception as e:
            st.error(f"❌ Could not load users for deletion: {e}")
        finally:
            try:
                cur_ud.close()
                conn_ud.close()
            except Exception:
                pass

# -------------------------
# Minimal Add Trigger branch
# -------------------------
elif choice == "Add Trigger":
    st.header("🛠️ Add Trigger (minimal)")

    # Load tables from information_schema safely (accept different key casings)
    try:
        conn_t = get_connection()
        cursor_t = conn_t.cursor(dictionary=True)
        cursor_t.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name;
        """, ("project",))
        rows = cursor_t.fetchall()
        tables = []
        for r in rows:
            tbl = r.get("table_name") or r.get("TABLE_NAME")
            if tbl:
                tables.append(tbl)
    except Exception as e:
        st.error(f"❌ Could not load table list: {e}")
        tables = []
    finally:
        try:
            cursor_t.close()
            conn_t.close()
        except Exception:
            pass

    if not tables:
        st.info("No tables available (or failed to read schema). Check DB privileges or schema name.")
    else:
        trig_name = st.text_input("Trigger name (alphanumeric & underscores only)")
        col1, col2 = st.columns(2)
        with col1:
            timing = st.selectbox("Timing", ["BEFORE", "AFTER"])
        with col2:
            event = st.selectbox("Event", ["INSERT", "UPDATE", "DELETE"])

        table_name = st.selectbox("Table", tables)

        st.markdown("### Trigger body (SQL statements inside `BEGIN ... END`)")
        st.markdown("Write only the statements that will execute inside the trigger body. **Do not** include the `CREATE TRIGGER` wrapper or `DELIMITER` lines.")
        default_template = "-- Example:\n-- UPDATE playlists SET tracks = (SELECT COUNT(*) FROM playlistsongs WHERE playlistId = NEW.playlistId) WHERE playlistId = NEW.playlistId;"
        body_sql = st.text_area("Trigger body", value=default_template, height=220)

        def assemble_preview(name, timing, event, table, body):
            name_safe = name.strip() or f"{timing.lower()}_{table}_{event.lower()}_trigger"
            preview = (
                f"CREATE TRIGGER `{name_safe}`\n"
                f"{timing} {event} ON `{table}`\n"
                f"FOR EACH ROW\n"
                f"BEGIN\n{body}\nEND;"
            )
            return preview, name_safe

        preview_sql, safe_name = assemble_preview(trig_name, timing, event, table_name, body_sql)
        st.subheader("Preview")
        st.code(preview_sql, language="sql")

        if st.button("Create Trigger"):
            import re
            if not re.fullmatch(r"[A-Za-z0-9_]+", safe_name):
                st.error("Trigger name invalid. Use only letters, numbers and underscores, no spaces.")
            elif table_name not in tables:
                st.error("Selected table is not present in schema (aborting).")
            elif not body_sql.strip():
                st.error("Trigger body is empty.")
            else:
                # Execute with a fresh connection (multi=True to support ; inside body)
                try:
                    conn_ct = get_connection()
                    cur_ct = conn_ct.cursor()
                    # Some MySQL python drivers (e.g. mysql-connector) accept multi=True to run
                    # multiple statements in one call. Others (e.g. MySQLdb/C extensions) do not
                    # accept the `multi` keyword. Try the multi form first, fall back to plain execute.
                    try:
                        for _ in cur_ct.execute(preview_sql, multi=True):
                            pass
                    except TypeError:
                        # Driver doesn't accept 'multi' kwarg — execute as a single statement
                        cur_ct.execute(preview_sql)

                    conn_ct.commit()
                    st.success(f"✅ Trigger `{safe_name}` created on `{table_name}`.")
                except Exception as e:
                    st.error(f"❌ Failed to create trigger: {e}")
                finally:
                    try:
                        cur_ct.close()
                        conn_ct.close()
                    except Exception:
                        pass

        st.markdown("---")
        st.subheader("🗑️ Drop a Trigger")
        try:
            conn_td = get_connection()
            cur_td = conn_td.cursor(dictionary=True)
            cur_td.execute("SELECT TRIGGER_NAME, EVENT_OBJECT_TABLE FROM information_schema.triggers WHERE trigger_schema = %s ORDER BY TRIGGER_NAME;", (os.getenv("DB_NAME"),))
            existing_trigs = cur_td.fetchall()
            if not existing_trigs:
                st.info("No triggers found to drop.")
            else:
                trig_choices = {f"{t['TRIGGER_NAME']} (on {t['EVENT_OBJECT_TABLE']})": t['TRIGGER_NAME'] for t in existing_trigs}
                sel_trig = st.selectbox("Select a trigger to drop", list(trig_choices.keys()))
                if st.button("Drop Trigger"):
                    tname = trig_choices[sel_trig]
                    try:
                        cur_drop = conn_td.cursor()
                        cur_drop.execute(f"DROP TRIGGER `{tname}`")
                        conn_td.commit()
                        st.success(f"✅ Dropped trigger {tname}")
                        cur_drop.close()
                        cur_td.close()
                        conn_td.close()
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to drop trigger: {e}")
        except Exception as e:
            st.error(f"❌ Could not load triggers for dropping: {e}")
        finally:
            try:
                cur_td.close()
                conn_td.close()
            except Exception:
                pass

        st.markdown("---")
        # List existing triggers (simple)
        try:
            conn_list = get_connection()
            cur_list = conn_list.cursor(dictionary=True)
            cur_list.execute("""
                SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE, ACTION_TIMING
                FROM information_schema.triggers
                WHERE trigger_schema = %s
                ORDER BY EVENT_OBJECT_TABLE, TRIGGER_NAME;
            """, (os.getenv("DB_NAME"),))
            trig_list = cur_list.fetchall()
            if not trig_list:
                st.info("No triggers found in this schema.")
            else:
                for t in trig_list:
                    st.write(f"- `{t['TRIGGER_NAME']}` → {t['ACTION_TIMING']} {t['EVENT_MANIPULATION']} ON `{t['EVENT_OBJECT_TABLE']}`")
        except Exception as e:
            st.error(f"Could not fetch triggers: {e}")
        finally:
            try:
                cur_list.close()
                conn_list.close()
            except Exception:
                pass

# -------------------------
# end Add Trigger branch
# -------------------------

cursor.close()
conn.close()
