# Chatterino - a simple texting app
This app allows users to host chatting servers and other users to join and chat on those servers.

## Getting started
Close repository using:
```
git clone https://github.com/JakubTuta/Chatterino.git
```

Install necessary modules:
```
pip install -r modules.txt
```

Now run the main.py file via code editor or:
```
python main.py
```

You can also run the program with additional parameters:
```
python main.py [mode] [side]
```

where:
```
[mode]: headless, gui
[side]: join, host
```

headless - runs the app in the console
gui - creates a window for the app

join - allows user to join in and type in the server
host - creates and then hosts the server

## Note
You need to host the server first, before users are able to connect