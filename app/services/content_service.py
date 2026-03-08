# app/services/content_service.py

import requests

WIKI_SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_MEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/media/"

UNSPLASH_URL = "https://api.unsplash.com/search/photos"
UNSPLASH_ACCESS_KEY = "YOUR_UNSPLASH_ACCESS_KEY"  # Replace with your Unsplash API key
from fastapi import HTTPException


def fetch_content(modality: str, topic: str):
    if modality == "visual":
        return fetch_visual(topic)
    elif modality == "audio":
        return fetch_audio(topic)
    elif modality == "text":
        return fetch_text(topic)
    elif modality == "kinesthetic":
        return fetch_kinesthetic(topic)
    else:
        raise HTTPException(400, "Unknown content modality")


def fetch_visual(topic: str):
    params = {
        "query": topic,
        "client_id": UNSPLASH_ACCESS_KEY,
        "per_page": 3
    }

    res = requests.fetch(UNSPLASH_URL, params=params)

    if res.status_code != 200:
        raise HTTPException(502, "Image service failed")

    data = res.json()
    if not data["results"]:
        raise HTTPException(404, "No images found")

    return {
        "type": "visual",
        "images": [img["urls"]["small"] for img in data["results"]]
    }


def fetch_audio(topic: str):
    return {
        "type": "audio",
        "message": f"Audio content placeholder for {topic}"
    }


def fetch_text(topic: str):
    return {
        "type": "text",
        "content": f"Reading material about {topic}"
    }


def fetch_kinesthetic(topic: str):
    return {
        "type": "kinesthetic",
        "activity": f"Hands-on activity for {topic}"
    }
