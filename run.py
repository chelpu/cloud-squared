from flask import Flask, request, redirect
import twilio.twiml
from twilio.rest import TwilioRestClient
import os
import soundcloud
import urllib
import ConfigParser

secrets = ConfigParser.ConfigParser()
secrets.read('secrets.ini')

app = Flask(__name__)

def getTrack(query, client, i, nOrC):
	tracks = client.get('/tracks', q=query)
	track = tracks[i]

	if nOrC == "n":
		i = i+1
		while (track.sharing.startswith("pri") or not track.streamable) and i < tracks.count:
			track = tracks[i]
			i = i+1
	return (track, i)

clientTwil = TwilioRestClient(secrets.get("twilio", "account_sid"), 
							  secrets.get("twilio", "auth_token"))
client = soundcloud.Client(client_id=secrets.get("soundcloud", "client_id"))
baseURL = "http://cloud-squared.herokuapp.com"

@app.route("/text", methods=['GET', 'POST'])
def run():
	body = request.values.get('Body', None)
	(track, i) = getTrack(body, client, 0, "n")
	
	stream_url = client.get(track.stream_url, allow_redirects=False)

	titleAndArtist = track.title + ' - ' + track.user["username"]
	songURL = track.permalink_url
	resp = twilio.twiml.Response()
	resp.message(titleAndArtist)
	playURL = stream_url.location

	encodedPlayURL = urllib.quote_plus(playURL)
	encodedBody = urllib.quote_plus(body)
	encodedSongUrl = urllib.quote_plus(songURL)
	cur = urllib.quote_plus(str(i))

	# Make a call to the user who texted in
	call = clientTwil.calls.create(to=request.values.get('From', None),
								   from_="+16162882901",
								   url=baseURL + "/play?query=" + encodedBody + "&sound=" + encodedPlayURL + "&cur=" + cur + "&url=" + encodedSongUrl)
	return str(resp)

@app.route("/call", methods=['GET', 'POST'])
def call():
	resp = twilio.twiml.Response()
	resp.say("Text this number with a search term to hear a song")
	return str(resp)

@app.route("/play", methods=['GET', 'POST'])
def play():
	cur = request.args.get('cur', '')
	sound = request.args.get('sound', '')
	query = request.args.get('query', '')
	songURL = request.args.get('url', '')

	encodedQuery = urllib.quote_plus(query)
	encodedSongUrl = urllib.quote_plus(songURL)
	cur = urllib.quote_plus(cur)
	encodedSound = urllib.quote_plus(sound)
				
	resp = twilio.twiml.Response()
	
	resp.say("Press 1 to skip to a different song")
	resp.say("Press 2 to receive a link to this song")
	with resp.gather(numDigits=1, action="/handle-key?query=" + encodedQuery + "&cur=" + cur + "&url=" + encodedSongUrl + "&sound=" + encodedSound, method="POST") as g:
		g.play(sound)
	return str(resp)

@app.route("/handle-key", methods=['GET', 'POST'])
def handle_key(): 

	resp = twilio.twiml.Response()
	digit_pressed = request.values.get('Digits', None)
	to = request.values.get('To', None)

	cur = request.args.get('cur', '')
	query = request.args.get('query', '')
	songURL = request.args.get('url', '')
	sound = request.args.get('sound', '')
	
	encodedSongUrl = urllib.quote_plus(songURL)
	encoded = urllib.quote_plus(query)
	encodedSound = urllib.quote_plus(sound)

	# Get the digit pressed by the user
	if digit_pressed == "1":
		(track, i) = getTrack(query, client, int(cur), "n")
		
		titleAndArtist = track.title + ' - ' + track.user["username"]
		message = clientTwil.messages.create(to=to, from_="+16162882901",
                                     		 body=titleAndArtist)
		cur = urllib.quote_plus(str(i))

		songURL = track.permalink_url
		encodedSongUrl = urllib.quote_plus(songURL)

		# Get url to send back to play
		stream_url = client.get(track.stream_url, allow_redirects=False)
		playURL = stream_url.location
		encodedURL = urllib.quote_plus(playURL)
		cur = urllib.quote_plus(cur)

		songURL = stream_url

		with resp.gather(numDigits=1, action="/handle-key?query=" + encoded + "&cur=" + cur + "&url=" + encodedSongUrl + "&sound=" + encodedURL, method="POST") as g:
			g.play(playURL)

		return str(resp)

	elif digit_pressed == "2":
		(track, i) = getTrack(query, client, int(cur), "c")
		
		if track.permalink_url != "":
			message = clientTwil.messages.create(to=to, from_="+16162882901",
                                     			 body=songURL)
		else:
			message = clientTwil.messages.create(to=to, from_="+16162882901",
                                     			 body="Sorry, link unavailable")

		cur = urllib.quote_plus(cur)
		with resp.gather(numDigits=1, action="/handle-key?query=" + encoded + "&cur=" + cur + "&url=" + encodedSongUrl + "&sound=" + sound, method="POST") as g:
			g.play(sound)
		return str(resp)
 
	# If the caller pressed anything but 1, redirect them to the homepage.
	else:
		cur = urllib.quote_plus(cur)
		return redirect("/play?query=" + encoded + "&sound=" + encodedSound + "&cur=" + cur + "&url=" + encodedSongUrl)

if __name__ == "__main__":
	app.run(debug=True)

