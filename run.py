from flask import Flask, request, redirect
import twilio.twiml
from twilio.rest import TwilioRestClient
import os
import soundcloud

app = Flask(__name__)

	
account_sid = "AC5116d5d4df9f61ceae2f0732e1ea9f1b"
auth_token = "a7628c89db064134c18bec81b380722b"
clientTwil = TwilioRestClient(account_sid, auth_token)

playURL = ""

@app.route("/", methods=['GET', 'POST'])
def run():
	body = request.values.get('Body', None)
	client = soundcloud.Client(client_id='2a48aabb635303b6544ac9482529822a')
	tracks = client.get('/tracks', q=body)
	track = tracks[0]
	i = 0
	while track.sharing.startswith("pri") and i < tracks.count:
		track = tracks[++i]

	stream_url = client.get(track.stream_url, allow_redirects=False)

	titleAndArtist = track.title + ' - ' + track.user["username"]
	print titleAndArtist
	print stream_url.location

	resp = twilio.twiml.Response()
	resp.message(titleAndArtist)
	print stream_url.location + " " + track.sharing
	playURL = stream_url.location

	# make a call to the client who texted in
	call = clientTwil.calls.create(to=request.values.get('From', None),
								   from_="+16162882901",
								   url="http://cloud-squared.herokuapp.com/play")
	return str(resp)

@app.route("/play", methods=['GET', 'POST'])
def play():
	resp = twilio.twiml.Response()
	resp.say("Press 1 to skip to a different song")
	print "purl ", playURL
	resp.play("https://ec-media.soundcloud.com/FrbdQpJhNBjf.128.mp3?f10880d39085a94a0418a7ef69b03d522cd6dfee9399eeb9a522019c67f8be3864a14bf70977cd1706f3fa370df75106ab0634f2e7c7d4e26de5cb3208e10633a158c10ebf&AWSAccessKeyId=AKIAJNIGGLK7XA7YZSNQ&Expires=1400800426&Signature=%2F0HlgCDCu4bdg3uDAIJWbIkAqy8%3D")
	return str(resp)

if __name__=="__main__":
	app.run(debug=True)

