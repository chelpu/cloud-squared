from flask import Flask, request, redirect
import twilio.twiml
from twilio.rest import TwilioRestClient
import os
import soundcloud
import urllib

app = Flask(__name__)

def getTrack(query, client, i, nOrC):
	tracks = client.get('/tracks', q=query)
	track = tracks[i]
	if nOrC == "n":
		while track.sharing.startswith("pri") and track.streamable and i < tracks.count:
			i = i+1
			track = tracks[i]
	return {"track" : track, "i" : i}



	
account_sid = "AC5116d5d4df9f61ceae2f0732e1ea9f1b"
auth_token = "a7628c89db064134c18bec81b380722b"
clientTwil = TwilioRestClient(account_sid, auth_token)
client = soundcloud.Client(client_id='2a48aabb635303b6544ac9482529822a')

@app.route("/text", methods=['GET', 'POST'])
def run():
	body = ""
	option = request.args.get('opt', '')
	if option == "4":
		body = request.values.get('TranscriptionText', None)
	else:
		body = request.values.get('Body', None)
	d = getTrack(body, client, 0, "n")
	track = d["track"]
	i = d["i"]
	stream_url = client.get(track.stream_url, allow_redirects=False)

	titleAndArtist = track.title + ' - ' + track.user["username"]
	print titleAndArtist
	print stream_url.location

	resp = twilio.twiml.Response()
	resp.message(titleAndArtist)
	print stream_url.location + " " + track.sharing
	playURL = stream_url.location

	encoded = urllib.quote_plus(playURL)
	encodedBody = urllib.quote_plus(body)

	cur = urllib.quote_plus(str(i))

	# make a call to the client who texted in
	call = clientTwil.calls.create(to=request.values.get('From', None),
								   from_="+16162882901",
								   url="http://cloud-squared.herokuapp.com/play?query=" + encodedBody + "&sound=" + encoded + "&opt=0&cur=" + cur)
	return str(resp)

@app.route("/call", methods=['GET', 'POST'])
def call():
	resp = twilio.twiml.Response()
	resp.say("What would you like to search for?")
	resp.record(maxLength="10", transcribe="true", finishOnKey="#", transcribeCallback="http://cloud-squared.herokuapp.com/text?option=4")
	return str(resp)

@app.route("/play", methods=['GET', 'POST'])
def play():
	option = request.args.get('opt', '')
	cur = request.args.get('cur', '')
	print "CUR IN PLAY: ", cur
	sound = request.args.get('sound', '')
	query = request.args.get('query', '')
	encoded = urllib.quote_plus(query)
				
	resp = twilio.twiml.Response()
	resp.say("Press 1 to skip to a different song")
	resp.say("Press 2 to receive a download link")
	with resp.gather(numDigits=1, action="/handle-key?query=" + encoded + "&cur=" + cur, method="POST") as g:
		g.play(sound)
	return str(resp)

@app.route("/handle-key", methods=['GET', 'POST'])
def handle_key(): 
	resp = twilio.twiml.Response()
	digit_pressed = request.values.get('Digits', None)

	cur = request.args.get('cur', '')
	query = request.args.get('query', '')
	encoded = urllib.quote_plus(query)

	# Get the digit pressed by the user
	if digit_pressed == "1":
		print "CUR IN HK: ", cur
		d = getTrack(query, client, int(cur), "n")
		track = d["track"]
		i = d["i"]

		# Get url to send back to play
		stream_url = client.get(track.stream_url, allow_redirects=False)
		playURL = stream_url.location
		encodedURL = urllib.quote_plus(playURL)

		with resp.gather(numDigits=1, action="/handle-key?query=" + encoded, method="POST") as g:
			g.play(playURL)

		return str(resp)

	if digit_pressed == "2":
		print "CUR: ", cur
		d = getTrack(query, client, int(cur), "c")
		track = d["track"]
		if track.downloadable:
			resp.message(track.download_url)
		else:
			resp.message("Sorry, download link unavailable")
		return str(resp)
 
	# If the caller pressed anything but 1, redirect them to the homepage.
	else:
		return redirect("/play")

if __name__=="__main__":
	app.run(debug=True)

