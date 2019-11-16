import spotipy
import operator
import itertools
from flask_wtf import FlaskForm
from flask import Flask, render_template, request
from wtforms import StringField, SubmitField
from itertools import product
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)


class TopSongs(FlaskForm):
    artist_input = StringField("")
    submit = SubmitField("Submit")


app.config['SECRET_KEY'] = 'RETRACTED'

client_credentials_manager = SpotifyClientCredentials(client_id='RETRACTED', client_secret='RETRACTED')

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


# The application asks the user to enter the name of a musical artist,
# and then generates a list of the artist's ten most popular songs on Spotify
@app.route('/', methods=["GET"])
@app.route('/top_songs', methods=["POST"])
def home():

    if request.method == 'POST':
        artist = request.form['artist']
        artist_search = sp.search(q='artist:' + artist, type='artist')

        global id_of_artist
        id_of_artist = artist_search['artists']['items'][0]['id']

        image = artist_search['artists']['items'][0]['images'][0]['url']
        results = sp.artist_top_tracks(str(id_of_artist))

        popular_songs, urls = [x['name'] for x in results['tracks']], [x['external_urls'] for x in results['tracks']]

        artist_name = artist_search['artists']['items'][0]['name']

        return render_template('topsongs.html', artist=artist, popular_songs=popular_songs, image=image,
                               itertools=itertools, urls=urls, artist_name=artist_name)

    return render_template('/home.html')


@app.route('/submit_songs', methods=['POST'])
def submitsongs():

    # creates dictionary containing user's favorite songs by the artist
    if request.method == 'POST':
        one = request.form.getlist("one")
        two = request.form.getlist("two")
        three = request.form.getlist("three")
        four = request.form.getlist("four")
        five = request.form.getlist("five")
        six = request.form.getlist("six")
        seven = request.form.getlist("seven")
        eight = request.form.getlist("eight")
        nine = request.form.getlist("nine")
        ten = request.form.getlist("ten")
        all_songs = one + two + three + four + five + six + seven + eight + nine + ten

        liked_songs_and_ids = {song: [str(sp.search(q='track:' + song, type='track')['tracks']['items'][0]['id'])] for
                               song in all_songs}

        # information regarding musical elements of each song is added to the dictionary

        for k, v in liked_songs_and_ids.items():
            features = sp.audio_features(v)
            liked_songs_and_ids[k].append(features[0]['acousticness'])
            liked_songs_and_ids[k].append(features[0]['danceability'])
            liked_songs_and_ids[k].append(features[0]['energy'])
            liked_songs_and_ids[k].append(features[0]['instrumentalness'])
            liked_songs_and_ids[k].append(features[0]['speechiness'])
            liked_songs_and_ids[k].append(features[0]['valence'])
            liked_songs_and_ids[k].append(features[0]['liveness'])

        # A dictionary is created containing all albums by the artist; this is to find every song by them

        results = sp.artist_albums(id_of_artist, album_type='album')
        album_names = results['items']
        albums_and_ids = {album['name']: album['id'] for album in album_names if 'Karaoke' not in album['name']}

        while results['next']:
            results = sp.next(results)
            album_names = results['items']
            for album in album_names:
                if 'Karaoke' not in album['name']:
                    albums_and_ids[album['name']] = album['id']

        # A dictionary is created containing all songs by the artist

        ids_and_songs = {}
        for k, v in albums_and_ids.items():
            results = sp.album_tracks(str(v))
            track_names = results['items']
            for i in track_names:

                if '-' not in i['name']:
                    ids_and_songs[i['id']] = i['name']

        # It is common for a song to be on multiple albums. The application finds
        # what the highest popularity ranking for each song is.

        songs_popularity = {k: [v, sp.track(str(k))['popularity']] for k, v in ids_and_songs.items()}
        sort_popularity = sorted(songs_popularity.items(), key=operator.itemgetter(1), reverse=True)

        keep_songs = {}
        for i in sort_popularity:
            if i[1][0] not in keep_songs.keys():
                keep_songs[i[1][0]] = i[1][1], i[0]

        all_songs = sorted(keep_songs.items(), key=operator.itemgetter(1))

        # The application will only recommend songs in the bottom half of popularity,
        # or the bottom 50 of an artist's discography

        num_of_songs = len(all_songs) / 2
        if num_of_songs >= 50:
            num_of_songs = 50

        less_popular = {i: [j] for i, j in all_songs[:num_of_songs]}

        # the musical elements for the least popular songs are added to their dictionary
        for k, v in less_popular.items():
            features = sp.audio_features([v[0][1]])
            less_popular[k].append(features[0]['acousticness'])
            less_popular[k].append(features[0]['danceability'])
            less_popular[k].append(features[0]['energy'])
            less_popular[k].append(features[0]['instrumentalness'])
            less_popular[k].append(features[0]['speechiness'])
            less_popular[k].append(features[0]['valence'])
            less_popular[k].append(features[0]['liveness'])

        # The user's favorite top songs and the artist's less popular tracks are compared
        match_songs = []
        for (k, v), (k2, v2) in product(liked_songs_and_ids.items(), less_popular.items()):
            total = abs(v[1] - v2[1]) + abs(v[2] - v2[2]) + abs(v[3] - v2[3]) + abs(v[4] - v2[4]) + abs(
                v[5] - v2[5]) + abs(
                v[6] - v2[6]) + abs(v[7] - v2[7])
            match_songs.append((k, k2, total, v2[0][1]))

        present_list = [(k[0], k[1], k[2], k[3]) for k in match_songs if k[2] < 0.50]

        ordered_songs = sorted(present_list, key=operator.itemgetter(2))

        # The (up to 15) tracks with the most similarity are displayed

        recommend_songs = [(i[0], i[1], i[2], i[3]) for i in ordered_songs[:15]]

        new_songs = []
        for i in recommend_songs:
            if i[1] not in [x[0] for x in new_songs]:
                new_songs.append((i[1], i[3], i[0]))

        return render_template('submitsongs.html', new_songs=new_songs, recommend_songs=recommend_songs)


if __name__ == "__main__":
    app.run(debug=True)
