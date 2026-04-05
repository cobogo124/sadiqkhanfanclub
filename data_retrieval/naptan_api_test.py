import requests
import pandas as pd

def get_naptan_london():

    #490 is ATCO code for london, foreign key used by TfL called naptanID relates to this
    #should allow us to query both sources


    URL = "https://naptan.api.dft.gov.uk/v1/access-nodes"
    
    params = {
        "atcoAreaCodes": "490",
        "dataFormat": "csv" 
    }
    
    response = requests.get(URL, params=params)
    response.raise_for_status()
    

    with open("downloads/naptan_london.csv", "wb") as f:
        f.write(response.content)
    
    print("saved naptan_london.csv")

if __name__ == "__main__":
    get_naptan_london()