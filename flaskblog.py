from flask import Flask, render_template, redirect, url_for, request, session
from forms import TopSongs
import spotipy
import spotipy.util as util
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import operator
from itertools import product
import numpy
import jinja2
import itertools
from spotipy.oauth2 import SpotifyClientCredentials
from difflib import SequenceMatcher


app = Flask(__name__)


class TopSongs(FlaskForm):
    artist_input = StringField("")
    submit = SubmitField("Submit")


app.config['SECRET_KEY'] = 'RETRACTED'

# scope = 'user-library-read'
# spotify_client_id = 'f0c917761fd84635a832a99e0457334f'
# spotify_client_secret = '8a2ce521da2e43398eec9b199bb646b2'
# spotify_redirect_uri = 'http://127.0.0.1:5000/'
# username = 'laladoodle'
#
# token = util.prompt_for_user_token(username, scope, spotify_client_id, spotify_client_secret, spotify_redirect_uri)
# sp = spotipy.Spotify(auth=token)


client_credentials_manager = SpotifyClientCredentials(client_id='RETRACTED', client_secret='RETRACTED')

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)



@app.route('/', methods=["GET", "POST"])
@app.route('/top_songs', methods=["GET", "POST"])
def home():

    if request.method == 'POST':
        artist = request.form['artist']

        artist_search = sp.search(q='artist:' + artist, type='artist')
        items = artist_search['artists']['items']
        artist = items[0]
        global id_of_artist
        id_of_artist = artist['id']
        image_url = artist['images']

        image = image_url[0].values()[0]

        # Finds the top 10 popular songs by artist

        popular_songs = []
        urls = []
        results = sp.artist_top_tracks(str(id_of_artist))
        for track in results['tracks'][:10]:
            name = track['name']
            url = track['external_urls']
            popular_songs.append(name)
            urls.append(url)

        artist_name = artist.values()[1]


        return render_template('topsongs.html', artist=artist, popular_songs=popular_songs, image=image, itertools=itertools, urls=urls, artist_name=artist_name)

    return render_template('/home.html')




@app.route('/submit_songs', methods=['POST'])
def submitsongs():
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

        liked_songs_and_ids = {}
        for song in all_songs:
            find_song_id = sp.search(q='track:' + song, type='track')
            items = find_song_id['tracks']['items']
            track = items[0]
            id_of_song = track['id']
            liked_songs_and_ids[song] = [str(id_of_song)]

        for k, v in liked_songs_and_ids.items():
            features = sp.audio_features(v)
            acoustic = features[0]['acousticness']
            dance = features[0]['danceability']
            energy = features[0]['energy']
            instrument = features[0]['instrumentalness']
            speech = features[0]['speechiness']
            valence = features[0]['valence']
            live = features[0]['liveness']
            liked_songs_and_ids[k].append(acoustic)
            liked_songs_and_ids[k].append(dance)
            liked_songs_and_ids[k].append(energy)
            liked_songs_and_ids[k].append(instrument)
            liked_songs_and_ids[k].append(speech)
            liked_songs_and_ids[k].append(valence)
            liked_songs_and_ids[k].append(live)

        albums_and_ids = {}
        results = sp.artist_albums(id_of_artist, album_type='album')
        album_names = results['items']
        for album in album_names:
            if 'Karaoke' not in album['name']:
                albums_and_ids[album['name']] = album['id']

        while results['next']:
            results = sp.next(results)
            album_names = results['items']
            for album in album_names:
                if 'Karaoke' not in album['name']:
                    albums_and_ids[album['name']] = album['id']



        ids_and_songs = {}
        for k, v in albums_and_ids.items():
            results = sp.album_tracks(str(v))
            track_names = results['items']
            for i in track_names:

                if '-' not in i['name']:
                    ids_and_songs[i['id']] = i['name']

        songs_popularity = {}
        for k, v in ids_and_songs.items():
            results = sp.track(str(k))
            songs_popularity[k] = v, results['popularity']

        sort_popularity = sorted(songs_popularity.items(), key=operator.itemgetter(1), reverse=True)

        keep_songs = {}
        for i in sort_popularity:
            if i[1][0] not in keep_songs.keys():
                keep_songs[i[1][0]] = i[1][1], i[0]

        all_songs = sorted(keep_songs.items(), key=operator.itemgetter(1))

        num_of_songs = len(all_songs) / 2
        if num_of_songs >= 50:
            num_of_songs = 50


        less_popular = {}
        for i, j in all_songs[:num_of_songs]:
            less_popular[i] = [j]

        for k, v in less_popular.items():
            features = sp.audio_features([v[0][1]])

            acoustic = features[0]['acousticness']
            dance = features[0]['danceability']
            energy = features[0]['energy']
            instrument = features[0]['instrumentalness']
            speech = features[0]['speechiness']
            valence = features[0]['valence']
            live = features[0]['liveness']
            less_popular[k].append(acoustic)
            less_popular[k].append(dance)
            less_popular[k].append(energy)
            less_popular[k].append(instrument)
            less_popular[k].append(speech)
            less_popular[k].append(valence)
            less_popular[k].append(live)

        match_songs = []
        for (k, v), (k2, v2) in product(liked_songs_and_ids.items(), less_popular.items()):
            total = abs(v[1] - v2[1]) + abs(v[2] - v2[2]) + abs(v[3] - v2[3]) + abs(v[4] - v2[4]) + abs(
                v[5] - v2[5]) + abs(
                v[6] - v2[6]) + abs(v[7] - v2[7])
            match_songs.append((k, k2, total, v2[0][1]))

        present_list = []
        for k in match_songs:
            if k[2] < 0.50:
                present_list.append((k[0], k[1], k[2], k[3]))

        ordered_songs = sorted(present_list, key=operator.itemgetter(2))

        recommend_songs = []
        for i in ordered_songs[:15]:
            recommend_songs.append((i[0], i[1], i[2], i[3]))

        new_songs = []
        for i in recommend_songs:
            if i[1] not in [x[0] for x in new_songs]:
                new_songs.append((i[1], i[3], i[0]))


            else:
                pass

        return render_template('submitsongs.html', new_songs=new_songs, recommend_songs=recommend_songs)


if __name__ == "__main__":
    app.run(debug=True)


