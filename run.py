from flask import Flask, request, redirect
import twilio.twiml
import soundcloud

app = Flask(__name__)

#client = soundcloud.Client(client_id='2a48aabb635303b6544ac9482529822a')
#tracks = client.get('/tracks', q='hello')
#track = tracks[0]
#stream_url = client.get(track.stream_url, allow_redirects=False)
#
#print stream_url.location

@app.route("/", methods=['GET', 'POST'])
def disp():
	resp = twilio.twiml.Response()
	resp.message(stream_url.location)
	return str(resp)

if __name__=="__main__":
	app.run(debug=True)

