from flask import Flask, request, redirect
import twilio.twiml
from twilio.rest import TwilioRestClient
import os
import soundcloud
import urllib

app = Flask(__name__)

def getTrack(query, client):
	tracks = client.get('/tracks', q=query)
	track = tracks[0]
	i = 0
	while track.sharing.startswith("pri") and i < tracks.count:
		track = tracks[++i]
	return track

	
account_sid = "AC5116d5d4df9f61ceae2f0732e1ea9f1b"
auth_token = "a7628c89db064134c18bec81b380722b"
clientTwil = TwilioRestClient(account_sid, auth_token)
client = soundcloud.Client(client_id='2a48aabb635303b6544ac9482529822a')

playURL = ""

@app.route("/", methods=['GET', 'POST'])
def run():
	body = request.values.get('Body', None)
	track = getTrack(body, client)
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

	# make a call to the client who texted in
	call = clientTwil.calls.create(to=request.values.get('From', None),
								   from_="+16162882901",
								   url="http://cloud-squared.herokuapp.com/play?query=" + encodedBody + "&sound=" + encoded + "&opt=0")
	return str(resp)

@app.route("/play", methods=['GET', 'POST'])
def play():
	option = request.args.get('opt', '')
	print "OPT: ", option
	sound = request.args.get('sound', '')
	query = request.args.get('query', '')
	encoded = urllib.quote_plus(query)

	resp = twilio.twiml.Response()
	resp.say("Press 1 to skip to a different song")
	resp.say("Press 2 to receive a download link")
	with resp.gather(numDigits=1, action="/handle-key?query=" + encoded, method="POST") as g:
		g.play(sound)
	return str(resp)

@app.route("/handle-key", methods=['GET', 'POST'])
def handle_key(): 
	resp = twilio.twiml.Response()
	digit_pressed = request.values.get('Digits', None)

	query = request.args.get('query', '')
	encoded = urllib.quote_plus(query)

	# Get the digit pressed by the user
	if digit_pressed == "1":
		#resp.say("one pressed")
		track = getTrack(query, client)
		return str(resp)

	if digit_pressed == "2":
		resp.say("Two pressed")
		return str(resp)
 
	# If the caller pressed anything but 1, redirect them to the homepage.
	else:
		return redirect("/play")

if __name__=="__main__":
	app.run(debug=True)

