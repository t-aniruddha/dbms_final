# 🎵 Music Database Management System

A database-driven application for managing songs, artists, albums, and playlists — built with **MySQL** as the backend and a lightweight **Streamlit** frontend for interaction.

---

## 🧩 Overview

This project demonstrates a **complete database management system** for a music platform.  
The core of the project lies in the **MySQL schema**, which handles:
- Users, playlists, and songs
- Relationships between artists, albums, and tracks
- Automatic updates using **SQL triggers**
- Data integrity through **foreign keys** and **constraints**

The **Streamlit** interface acts as a visual front-end for:
- Viewing and editing database records
- Managing playlists
- Searching and adding songs
- Inspecting and adding triggers dynamically

---

## 🗄️ Database Design

### 🧱 Core Tables

| Table | Purpose |
|--------|----------|
| **users** | Stores user info (userId, firstName, lastName, etc.) |
| **songs** | Contains all songs with songId, title, duration, releaseDate, song_link |
| **artists** | Stores artist details |
| **albums** | Stores album info |
| **playlists** | User-owned collections of songs with `tracks` and `total_duration` |
| **playlistsongs** | Junction table linking songs ↔ playlists |
| **artistsong**, **albumsong** | Junction tables linking artists ↔ songs and albums ↔ songs |
| **genres**, **genresong** | Classify songs by genre |
| **paymentplan**, **userphone** | Example auxiliary tables for extended features |

Each table uses proper **primary and foreign key constraints** to maintain relational consistency.

---

## 🔗 Relationships Summary

- **1:N (One-to-Many)**  
  - `users → playlists`  
  - `albums → songs`

- **M:N (Many-to-Many)**  
  - `songs ↔ playlists` (via `playlistsongs`)  
  - `songs ↔ artists` (via `artistsong`)  
  - `songs ↔ genres` (via `genresong`)

- **Referential Integrity**  
  Enforced through `ON DELETE CASCADE` and `ON UPDATE CASCADE` constraints for dependent records.

---

## ⚙️ SQL Triggers & Stored Logic

Triggers automate updates and maintain consistency.  
Notable triggers include:

| Trigger | Description |
|----------|--------------|
| **after_playlistsongs_insert** | Recalculates playlist `tracks` and `total_duration` whenever a song is added |
| **after_playlistsongs_delete** | Updates playlist totals when a song is removed |
| **before_songs_insert** | Prevents adding songs with negative or invalid duration |
| **after_playlist_empty** *(custom)* | Marks playlists as `Private` when their `tracks` count drops to 0 |

### 🧠 Stored Procedures (Optional)
Procedures can be defined to simplify repetitive operations like:
- Adding songs to multiple playlists
- Aggregating play counts per user

All triggers and procedures are viewable inside the app under  
**"View Triggers & Procedures"**.

---

## 🪄 Database Connection

All database interactions are handled through a reusable utility:
```python
# db_connection.py
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="project"
    )
