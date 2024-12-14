import pickle
import streamlit as st
import requests
import time

# Default placeholder poster URL
DEFAULT_POSTER_URL = "https://via.placeholder.com/500x750?text=No+Poster+Available"

# Function to fetch movie poster
def fetch_poster(movie_id, retries=3):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8aaac00e4a437009ed6aa16b518cad05&language=en-US"
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get('poster_path')
            return f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else DEFAULT_POSTER_URL
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                st.error(f"Error fetching poster for movie ID {movie_id}: {e}")
                return DEFAULT_POSTER_URL

# Function to fetch movie trailer
def fetch_trailer(movie_id, retries=3):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key=8aaac00e4a437009ed6aa16b518cad05&language=en-US"
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            for video in data['results']:
                if video['type'] == "Trailer" and video['site'] == "YouTube":
                    return f"https://www.youtube.com/embed/{video['key']}?autoplay=1&mute=0"
            return None
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                st.error(f"Error fetching trailer for movie ID {movie_id}: {e}")
                return None

# Function to fetch movie backdrop
def fetch_backdrop(movie_id, retries=3):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8aaac00e4a437009ed6aa16b518cad05&language=en-US"
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            backdrop_path = data.get('backdrop_path')
            if backdrop_path:
                return f"https://image.tmdb.org/t/p/original/{backdrop_path}"
            else:
                return "https://via.placeholder.com/1920x1080?text=No+Backdrop+Available"
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                st.error(f"Error fetching backdrop for movie ID {movie_id}: {e}")
                return "https://via.placeholder.com/1920x1080?text=No+Backdrop+Available"

# Function to recommend movies
def recommend(movie):
    try:
        index = movies[movies['title'] == movie].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        recommended_movies = []
        for i in distances[1:7]:  # Top 6 recommendations
            movie_id = movies.iloc[i[0]].movie_id
            recommended_movies.append({
                "title": movies.iloc[i[0]].title,
                "id": movie_id,
                "poster": fetch_poster(movie_id)
            })
        return recommended_movies
    except IndexError:
        st.error("Could not find the selected movie in the database.")
        return []

# Function to fetch trending movies
def fetch_trending_movies(timeframe='week', retries=3):
    url = f"https://api.themoviedb.org/3/trending/movie/{timeframe}?api_key=8aaac00e4a437009ed6aa16b518cad05"
    trending_movies = []
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            for movie in data['results'][:6]:  # Get top 6 trending movies
                trending_movies.append({
                    "title": movie['title'],
                    "id": movie['id'],
                    "poster": fetch_poster(movie['id']),
                    "rating": movie['vote_average']  # Displaying rating on poster
                })
            return trending_movies
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                st.error(f"Error fetching trending movies: {e}")
                return []

# Load movie data and similarity matrix
try:
    movies = pickle.load(open('model/movie_list.pkl', 'rb'))
    similarity = pickle.load(open('model/similarity.pkl', 'rb'))
except FileNotFoundError as e:
    st.error(f"Error loading required files: {e}")
    st.stop()

# App layout
st.title("🎬 Movie Recommender System")

# Movie selection dropdown
selected_movie = st.selectbox(
    "Search for a movie:",
    [""] + list(movies['title'].values),
    help="Start typing the name of a movie to select."
)

# Store the state of the button press for recommendations
show_recommendations = False

# If a movie is selected, play the trailer and show recommendations
if selected_movie:
    selected_movie_id = movies[movies['title'] == selected_movie].iloc[0]['movie_id']

    # Fetch and display the backdrop image as the background
    backdrop_url = fetch_backdrop(selected_movie_id)
    if backdrop_url:
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url('{backdrop_url}');
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

    # Fetch and display the trailer
    trailer_url = fetch_trailer(selected_movie_id)
    if trailer_url:
        st.markdown(
            f"""
            <iframe width="100%" height="400" src="{trailer_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error("Trailer not available for this movie.")

    # Button for showing recommendations
    show_recommendations = st.button("Show Recommendations")

    # Display the recommended movies if the button is clicked
    if show_recommendations:
        recommended_movies = recommend(selected_movie)
        if recommended_movies:
            st.subheader("🎯 Recommended Movies")
            cols = st.columns(3)
            for idx, movie in enumerate(recommended_movies):
                with cols[idx % 3]:
                    st.image(movie['poster'], use_container_width=True)
                    st.markdown(f"[{movie['title']}] (https://www.themoviedb.org/movie/{movie['id']})")
        else:
            st.error("No recommendations available for the selected movie.")

# Fetch and display trending movies when the button is clicked
if st.button("Show Trending Movies This Week"):
    trending_movies = fetch_trending_movies(timeframe='week')
    if trending_movies:
        st.subheader("🔥 Trending Movies This Week")
        cols = st.columns(3)
        for idx, movie in enumerate(trending_movies):
            with cols[idx % 3]:
                st.image(movie['poster'], use_container_width=True)
                st.markdown(f"[{movie['title']}] (https://www.themoviedb.org/movie/{movie['id']})")
                st.markdown(f"Rating: {movie['rating']}")

# Fetch and display trending movies for today when the button is clicked
if st.button("Show Trending Movies Today"):
    trending_movies = fetch_trending_movies(timeframe='day')
    if trending_movies:
        st.subheader("🔥 Trending Movies Today")
        cols = st.columns(3)
        for idx, movie in enumerate(trending_movies):
            with cols[idx % 3]:
                st.image(movie['poster'], use_container_width=True)
                st.markdown(f"[{movie['title']}] (https://www.themoviedb.org/movie/{movie['id']})")
                st.markdown(f"Rating: {movie['rating']}")

