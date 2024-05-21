I was frustrated with the fact that the public HP API has had no changes in years, so ive made this really basic web scraper to autofill serialnumbers via registry to the HP Website, then grab the warranty end date and save that to the registry. You can then utilise powershell scripts to upload to your RMM, or whatever you need.

TO COMPILE:

You'll need python installed on your machine. Once installed, use:

pyinstaller --onefile --window PATH\TO\YOUR\.PY

to create the .exe


Also, im not a programmer / dev, this was made from heaps of research online, so if theres errors or functionalities that are redundant or useless, please let me know.
