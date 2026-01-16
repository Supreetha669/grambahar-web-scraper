from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
from fastapi.responses import StreamingResponse

app = FastAPI()

# Allow your HTML to talk to the Python backend
app.add_middleware(CORSMiddleware, allow_origins=["*"])


@app.get("/scrape")
def scrape_site(url: str):
    try:
        header = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=header, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Extract Logo
        logo = soup.find('img', {'src': True})['src'] if soup.find('img') else "Not found"

        # 2. Extract Basic Contacts (Simple Example)
        email = "None"
        if "mailto:" in response.text:
            email = response.text.split('mailto:')[1].split('"')[0]

        # 3. Extract Meta Info (Services/Description)
        desc = soup.find("meta", {"name": "description"})
        services = desc["content"] if desc else "No description found"

        # Create Data Structure
        data = [{
            "Website": url,
            "Logo URL": logo,
            "Contact Email": email,
            "Description/Services": services
        }]

        # Convert to CSV in memory
        df = pd.DataFrame(data)
        stream = io.StringIO()
        df.to_csv(stream, index=False)

        return StreamingResponse(
            io.BytesIO(stream.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=extract.csv"}
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))