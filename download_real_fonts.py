import os
import requests

os.makedirs('assets/fonts', exist_ok=True)

print("Downloading Roboto-Black...")
r1 = requests.get("https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Black.ttf")
if r1.status_code == 200:
    with open('assets/fonts/Roboto-Black.ttf', 'wb') as f:
        f.write(r1.content)
        
print("Downloading FontAwesome...")
r2 = requests.get("https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/webfonts/fa-brands-400.ttf")
if r2.status_code == 200:
    with open('assets/fonts/fa-brands-400.ttf', 'wb') as f:
        f.write(r2.content)

print("Fonts downloaded successfully into assets/fonts/!")
