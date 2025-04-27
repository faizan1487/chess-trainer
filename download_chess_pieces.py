import os
import requests
import shutil

# Define the base URL for chess pieces - updated with correct path
base_url = "https://raw.githubusercontent.com/oakmac/chessboardjs/master/website/img/chesspieces/wikipedia/"

# Define the local directory
local_dir = "./chess_app/static/chess_app/img/chesspieces/wikipedia/"

# Create the directory if it doesn't exist
os.makedirs(local_dir, exist_ok=True)

# Define all chess piece files
pieces = [
    "wP.png", "wR.png", "wN.png", "wB.png", "wQ.png", "wK.png",
    "bP.png", "bR.png", "bN.png", "bB.png", "bQ.png", "bK.png"
]

# Download each piece
for piece in pieces:
    url = base_url + piece
    local_path = os.path.join(local_dir, piece)
    
    print(f"Downloading {url} to {local_path}")
    
    # Download the file
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        # Write the file
        with open(local_path, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
        print(f"  Successfully downloaded {piece}")
    else:
        print(f"  Failed to download {piece}: {response.status_code}")

print("Download completed.") 