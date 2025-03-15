import streamlit as st
import pickle
import pandas as pd
import requests
from requests.exceptions import Timeout, ConnectionError

# OMDb API key
OMDB_API_KEY = "f16580bb"  # Your OMDB API key

def fetch_poster_omdb(title, year=None):
    """Fetch movie poster from OMDb API using movie title and year"""
    try:
        # Build URL with year if available
        if year and year != "N/A" and year != "Unknown":
            url = f"http://www.omdbapi.com/?t={title}&y={year}&apikey={OMDB_API_KEY}"
        else:
            url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
        
        # Add timeout to avoid hanging
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # Check if poster is available and not the default "N/A"
        if 'Poster' in data and data['Poster'] != 'N/A':
            return data['Poster']
        else:
            return None
    except (ConnectionError, Timeout) as e:
        st.warning(f"Could not connect to OMDb API: {e}")
        return None
    except Exception as e:
        st.warning(f"Error fetching poster: {e}")
        return None

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movie_details = []
    for i in movies_list:
        movie_idx = i[0]
        
        # Get only the movie title and similarity score
        movie_title = movies.iloc[movie_idx].title
        similarity_score = i[1]
        
        # Still collect year for poster fetching but don't display it
        try:
            if 'release_date' in movies.columns:
                release_year = movies.iloc[movie_idx].release_date.split('-')[0]
            elif 'release_year' in movies.columns:
                release_year = str(movies.iloc[movie_idx].release_year)
            else:
                release_year = None
        except:
            release_year = None
            
        # Fetch poster using OMDb API
        poster_url = fetch_poster_omdb(movie_title, release_year)
        
        movie_data = {
            'title': movie_title,
            'similarity_score': similarity_score,
            'poster_url': poster_url
        }
        recommended_movie_details.append(movie_data)
    
    return recommended_movie_details

# Load data
movies_dict = pickle.load(open('movies_dict.pkl','rb'))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity.pkl','rb'))

# UI
st.title('Movie Recommender System')

# Add some description
st.markdown("""
This system recommends movies similar to your selection based on content analysis of plot, genres, cast, and keywords.
""")

selected_movie_name = st.selectbox(
    "Select a movie",
    (movies['title'].values)
)

if st.button('Recommend'):
    with st.spinner('Finding similar movies...'):
        recommendations = recommend(selected_movie_name)
        
        st.header(f"Movies similar to '{selected_movie_name}':")
        
        # Create rows of movie cards (2 movies per row)
        for i in range(0, len(recommendations), 2):
            cols = st.columns(2)
            
            # Process up to 2 movies for this row
            for j in range(2):
                if i+j < len(recommendations):
                    movie = recommendations[i+j]
                    with cols[j]:
                        st.markdown(f"### {i+j+1}. {movie['title']}")
                        
                        # Display poster if available
                        if movie['poster_url']:
                            st.image(movie['poster_url'], width=200)
                        else:
                            st.markdown("*Poster not available*")
                        
                        # Show similarity as a progress bar
                        similarity_percentage = round(float(movie['similarity_score']) * 100, 1)
                        st.progress(float(movie['similarity_score']))
                        st.caption(f"Similarity: {similarity_percentage}%")