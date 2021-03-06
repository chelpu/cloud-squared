from flask import Flask, request, redirect
import twilio.twiml
from twilio.rest import TwilioRestClient
import os
import soundcloud
import urllib
import ConfigParser

app = Flask(__name__)

client_twil = TwilioRestClient(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
client_sc = soundcloud.Client(client_id=os.environ['SOUNDCLOUD_CLIENT_ID'])
base_url = 'http://cloud-squared.herokuapp.com'
twilio_number = '+16162882901'

def get_track(query, client_sc, i, nOrC):
	tracks = client_sc.get('/tracks', q=query)
	track = tracks[i]

	if nOrC == 'n':
		i = i+1
		while (track.sharing == 'private' or not track.streamable) and i < tracks.count:
			track = tracks[i]
			i = i+1
		if i == tracks.count:
			i = -1
	return (track, i)

@app.route('/text', methods=['GET', 'POST'])
def run():
	body = request.values.get('Body', None)
	(track, i) = get_track(body, client_sc, 0, 'n')
	if i == -1:
		resp.message('No songs found')
		return str(resp)
	
	stream_url = client_sc.get(track.stream_url, allow_redirects=False)

	title_and_artist = track.title + ' - ' + track.user['username']
	song_url = track.permalink_url
	play_url = stream_url.location

	resp = twilio.twiml.Response()
	resp.message(title_and_artist)

	encoded_play_url = urllib.quote_plus(play_url)
	encoded_query = urllib.quote_plus(body)
	encoded_song_url = urllib.quote_plus(song_url)
	cur = urllib.quote_plus(str(i))

	# Make a call to the user who texted in
	call = client_twil.calls.create(to=request.values.get('From', None),
									from_=twilio_number,
									url=base_url + '/play?query=' + encoded_query + '&sound=' + encoded_play_url + '&cur=' + cur + '&url=' + encoded_song_url)
	return str(resp)

@app.route('/call', methods=['GET', 'POST'])
def call():
	resp = twilio.twiml.Response()
	resp.say('Text this number with a search term to hear a song')
	return str(resp)

@app.route('/play', methods=['GET', 'POST'])
def play():
	cur = request.args.get('cur', '')
	sound = request.args.get('sound', '')
	query = request.args.get('query', '')
	song_url = request.args.get('url', '')

	encoded_query = urllib.quote_plus(query)
	encoded_song_url = urllib.quote_plus(song_url)
	encoded_sound = urllib.quote_plus(sound)
	cur = urllib.quote_plus(cur)
				
	resp = twilio.twiml.Response()
	
	resp.say('Press 1 to skip to a different song')
	resp.say('Press 2 to receive a link to this song')
	with resp.gather(numDigits=1, action='/key-press?query=' + encoded_query + '&cur=' + cur + '&url=' + encoded_song_url + '&sound=' + encoded_sound, method='POST') as g:
		g.play(sound)
	return str(resp)

@app.route('/key-press', methods=['GET', 'POST'])
def key_press(): 
	resp = twilio.twiml.Response()
	digit_pressed = request.values.get('Digits', None)
	to = request.values.get('To', None)

	cur = request.args.get('cur', '')
	query = request.args.get('query', '')
	song_url = request.args.get('url', '')
	sound = request.args.get('sound', '')
	
	encoded_song_url = urllib.quote_plus(song_url)
	encoded_query = urllib.quote_plus(query)
	encoded_sound = urllib.quote_plus(sound)

	# Get the digit pressed by the user
	if digit_pressed == '1':
		(track, i) = get_track(query, client_sc, int(cur), 'n')

		if i == -1:
			resp.message('No songs found')
			return str(resp)
		
		title_and_artist = track.title + ' - ' + track.user['username']
		message = client_twil.messages.create(to=to, from_=twilio_number,
                                     		 body=title_and_artist)
		cur = urllib.quote_plus(str(i))

		song_url = track.permalink_url
		encoded_song_url = urllib.quote_plus(song_url)

		# Get url to send back to play
		stream_url = client_sc.get(track.stream_url, allow_redirects=False)
		play_url = stream_url.location

		encoded_url = urllib.quote_plus(play_url)
		cur = urllib.quote_plus(cur)

		with resp.gather(numDigits=1, action='/key-press?query=' + encoded_query + '&cur=' + cur + '&url=' + encoded_song_url + '&sound=' + encoded_url, method='POST') as g:
			g.play(play_url)

		return str(resp)

	elif digit_pressed == '2':
		(track, i) = get_track(query, client_sc, int(cur), 'c')
		
		if track.permalink_url != '':
			message = client_twil.messages.create(to=to, from_=twilio_number,
                                     			 body=song_url)
		else:
			message = client_twil.messages.create(to=to, from_=twilio_number,
                                     			 body='Sorry, link unavailable')

		cur = urllib.quote_plus(cur)
		with resp.gather(numDigits=1, action='/key-press?query=' + encoded_query + '&cur=' + cur + '&url=' + encoded_song_url + '&sound=' + sound, method='POST') as g:
			g.play(sound)
		return str(resp)
 
	# If the caller pressed anything but 1, redirect them to the homepage.
	else:
		cur = urllib.quote_plus(cur)
		return redirect('/play?query=' + encoded_query + '&sound=' + encoded_sound + '&cur=' + cur + '&url=' + encoded_song_url)

if __name__ == '__main__':
	app.run(debug=True)

