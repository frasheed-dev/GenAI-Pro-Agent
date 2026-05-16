import requests
import os

image_path = "drafts/test_branding.png"
if os.path.exists(image_path):
    print("Uploading to catbox...")
    try:
        with open(image_path, "rb") as f:
            catbox_res = requests.post(
                "https://catbox.moe/user/api.php", 
                data={"reqtype": "fileupload"}, 
                files={"fileToUpload": f}
            )
            print("Status Code:", catbox_res.status_code)
            print("Response text:", catbox_res.text)
    except Exception as e:
        print("Error:", e)
else:
    print("File not found")
