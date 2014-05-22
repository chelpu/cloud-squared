from flask import Flask, request, redirect
import twilio.twiml
import os
import soundcloud

app = Flask(__name__)



@app.route("/", methods=['GET', 'POST'])
def run():
	body = request.values.get('Body', None)

	client = soundcloud.Client(client_id='2a48aabb635303b6544ac9482529822a')
	tracks = client.get('/tracks', q=body)
	track = tracks[0]
	stream_url = client.get(track.stream_url, allow_redirects=False)

	titleAndArtist = track.title + ' - ' + track.user["username"]
	print titleAndArtist
	print stream_url.location

	resp = twilio.twiml.Response()
	resp.message(titleAndArtist)
	resp.play(stream_url.location)
	#resp.message(body)
	return str(resp)

if __name__=="__main__":
	app.run(debug=True)

