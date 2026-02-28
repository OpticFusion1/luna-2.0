import requests
import time

BASE_URL = "https://www.pathofexile.com/forum/view-thread/{}"
thread_number = 3913392

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PoE-Thread-Checker/1.0)"
}

while True:
    url = BASE_URL.format(thread_number)
    print(f"Checking thread {thread_number}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        html = response.text

        if "Content Update" in html:
            print("content update found! " + url)
            payload = {
                "prompt": "smokie: announce to everyone that poe 3.28 patch notes are live!",
                "priority": "PRIORITY_MIC_INPUT"
            }
            response = requests.post(
                "http://localhost:5001/receive_prompt",
                json=payload  # automatically sets Content-Type: application/json
            )
            break

        elif "Resource Not Found" in html:
            # Do nothing, continue checking same thread
            print("passed")
            pass

        else:
            print('bumped')
            thread_number += 1

    except requests.RequestException as e:
        print(f"Request failed: {e}")

    time.sleep(5)
