#!/usr/bin/env python
from app import app


if __name__ == "__main__":
	import webbrowser, threading
	url = "http://127.0.0.1:5000"

	threading.Timer(1.25, lambda:webbrowser.open_new(url)).start()
	app.run(debug=True)