import requests
import json

def main():
    URL = "https://api.tfl.gov.uk/line/24/stoppoints"   
    response  = requests.get(URL)
    data = response.json()

    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()