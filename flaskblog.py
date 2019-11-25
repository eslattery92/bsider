import config
import spotipy
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from itertools import product
from spotipy.oauth2 import SpotifyClientCredentials
from wtforms import StringField, SubmitField


app = Flask(__name__)


class TopSongs(FlaskForm):
    artist_input = StringField("")
    submit = SubmitField("Submit")


app.config['SECRET_KEY'] = config.secret_key
client_credentials_manager = SpotifyClientCredentials(client_id=config.client_id, client_secret=config.client_secret)


sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


# User enters the name of a musical artist, and program generates a list of the artist's ten most popular songs
# on Spotify
@app.route('/', methods=["GET"])
@app.route('/top_songs', methods=["POST"])
def home():

    if request.method == 'POST':
        artist = request.form['artist']
        artist_search = sp.search(q='artist:' + artist, type='artist')

        global id_of_artist
        id_of_artist = artist_search['artists']['items'][0]['id']

        results = sp.artist_top_tracks(str(id_of_artist))

        popular_songs, urls = [x['name'] for x in results['tracks']], [x['external_urls'] for x in results['tracks']]

        artist_name = artist_search['artists']['items'][0]['name']

        return render_template('topsongs.html', popular_songs=popular_songs,
                               urls=urls, artist_name=artist_name)

    return render_template('/home.html')


@app.route('/submit_songs', methods=['POST'])
def submitsongs():

    # creates list containing user's favorite songs by the artist
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

        liked_songs = one + two + three + four + five + six + seven + eight + nine + ten

        liked_songs[:] = [[song, [str(sp.search(q='track:' + song, type='track')['tracks']['items'][0]['id'])]] for song
                          in liked_songs]

        # information regarding musical elements of each song is added to each song in the list

        for a, b in liked_songs:
            features = sp.audio_features(b[0])
            if None not in features:
                b.append(features[0]['acousticness'])
                b.append(features[0]['danceability'])
                b.append(features[0]['energy'])
                b.append(features[0]['instrumentalness'])
                b.append(features[0]['speechiness'])
                b.append(features[0]['valence'])
                b.append(features[0]['liveness'])

        # a list is created containing all albums by the artist

        results = sp.artist_albums(id_of_artist, album_type='album')
        albums = [album['id'] for album in results['items'] if 'Karaoke' not in album['name']]

        while results['next']:
            results = sp.next(results)
            album_names = results['items']
            for album in album_names:
                if 'Karaoke' not in album['name']:
                    albums.append(album['id'])

        # A dictionary is created containing all songs by the artist

        all_songs = {}
        for album in albums:
            results = sp.album_tracks(str(album))['items']
            for i in results:
                try:
                    if '-' not in i['name'] and i['name'] not in all_songs.keys():
                        all_songs[i['name']] = [[str(i['id']), sp.track(str(i['id']))['popularity']]]
                    else:
                        all_songs[i['name']].append([str(i['id']), sp.track(str(i['id']))['popularity']])
                except KeyError:
                    pass

        # In some cases, a song can be found on multiple albums. The program finds
        # what the highest popularity ranking for each song is, and then creates new list with the
        # less popular songs by the artist.

        most_popular = {k: max(v, key=lambda x: x[1]) for k, v in all_songs.items() if v[0][1] > 0}

        num_of_songs = len(most_popular) - int(round(len(most_popular) * 0.25))

        most_popular_sort = sorted(most_popular.items(), key=lambda x: x[1][1])[:num_of_songs]

        for a, b in most_popular_sort:
            features = sp.audio_features(b[0])
            if None not in features:
                b.append(features[0]['acousticness'])
                b.append(features[0]['danceability'])
                b.append(features[0]['energy'])
                b.append(features[0]['instrumentalness'])
                b.append(features[0]['speechiness'])
                b.append(features[0]['valence'])
                b.append(features[0]['liveness'])
                del b[1]

        # compares musical features of user's favorite songs with the artist's least favorite songs to find the most
        # similiar ones
        match_songs = []
        for (a, b), (c, d) in product(most_popular_sort, liked_songs):
            total = abs(b[1] - d[1]) + abs(b[2] - d[2]) + abs(b[3] - d[3]) + abs(b[4] - d[4]) + abs(
                b[5] - d[5]) + abs(
                b[6] - d[6]) + abs(b[7] - d[7])
            if total < 0.50:
                match_songs.append([c, a, total, b[0]])

        match_dict = {}
        for item in sorted(match_songs, key=lambda x: x[2]):
            if item[1] not in match_dict.keys() and len(match_dict) < 7:
                match_dict[item[1]] = [item[0], item[3]]

        return render_template('submitsongs.html', match_dict=match_dict)


if __name__ == "__main__":
    app.run(debug=False)
