
# Ingest and Visualize YouTube Playlist Data in Port

This guide takes approximately 30 minutes to complete and demonstrates the value of integrating Port with external data sources like YouTube.

## Prerequisites

- Ensure you have a [Port](https://www.getport.io/) account and have completed the [onboarding process](https://docs.getport.io/quickstart).
- Access to a [GitHub](https://github.com/) repository for workflow integration.
- API keys and credentials: Port [Client ID and Client Secret](https://docs.getport.io/build-your-software-catalog/custom-integration/api/#find-your-port-credentials), and [YouTube API Key](https://developers.google.com/youtube/v3/docs#calling-the-api).

## Goal of This Guide

This guide will walk you through:

- Creating and configuring blueprints in Port for YouTube data.
- Setting up a GitHub workflow to automate data ingestion from YouTube.
- Visualizing and analyzing the ingested data in Port.

---

## Step 1: Create Blueprints in Port

### 1.1 Log in to Your Port Account
Access Port's web app and log in with your credentials.

### 1.2 Navigate to the Builder Section
Click on **"Builder"** in the left-hand navigation menu. This is where you create and manage [blueprints](https://docs.getport.io/build-your-software-catalog/customize-integrations/configure-data-model/setup-blueprint/).

### 1.3 Create a Blueprint for YouTube Video
1. Click on **"New Blueprint"** at the top right corner of the Builder page.
2. Configure the blueprint details:
   - **Identifier**: `youtubeVideo`
   - **Title**: `YouTube Video`
   - **Icon**: Choose an icon representing a video (optional).
     
<img width="1440" alt="image" src="https://github.com/user-attachments/assets/38fe0d01-760d-4f2e-8d0d-672b8256124c">

### Define the Schema
Add properties to the YouTube Video blueprint with names, types, and whether they are required:

#### Blueprint for YouTube Video
- **Properties**:
  - `videoId`: string (required)
  - `title`: string (required)
  - `description`: string
  - `thumbnailUrl`: string
  - `duration`: string
  - `viewCount`: number
  - `likeCount`: number
  - `commentCount`: number
- **Relation**: `belongs_to_playlist` to `YouTube Playlist`.

<img width="1437" alt="image" src="https://github.com/user-attachments/assets/109b68a5-c29f-4d43-b79e-9e358945f0d7">

**Example JSON**:
```json
{
  "identifier": "youtubeVideo",
  "description": "This blueprint represents a video in our software catalog",
  "title": "YouTube Video",
  "icon": "Widget",
  "schema": {
    "properties": {
      "videoId": { "type": "string", "title": "Video ID" },
      "title": { "type": "string", "title": "Title" },
      "description": { "type": "string", "title": "Description" },
      "thumbnailUrl": { "type": "string", "title": "Thumbnail URL" },
      "duration": { "type": "string", "title": "Duration" },
      "viewCount": { "type": "number", "title": "View Count" },
      "likeCount": { "type": "number", "title": "Like Count" },
      "commentCount": { "type": "number", "title": "Comment Count" }
    },
    "required": ["videoId", "title"]
  },
  "relations": {
    "belongs_to_playlist": {
      "title": "Belongs to Playlist",
      "target": "youtubePlaylist",
      "required": false,
      "many": false
    }
  }
}
```
<img width="1440" alt="image" src="https://github.com/user-attachments/assets/f5be5730-839a-4238-8016-aedaf24eec49">

### Blueprint for YouTube Playlist
- **Properties**:
  - `playlistId`: string (required)
  - `title`: string (required)
  - `description`: string
  - `videoCount`: number
  - `thumbnailUrl`: string
  - `created_at`: string
- **Relation**: `has_videos` to `YouTube Video`.

<img width="1437" alt="image" src="https://github.com/user-attachments/assets/7807873b-7cd9-469e-b4d7-f57be13808c4">

**Example JSON**:
```json
{
  "identifier": "youtubePlaylist",
  "title": "YouTube Playlist",
  "icon": "Widget",
  "schema": {
    "properties": {
      "playlistId": { "type": "string", "title": "Playlist ID" },
      "title": { "type": "string", "title": "Title" },
      "description": { "type": "string", "title": "Description" },
      "videoCount": { "type": "number", "title": "Video Count" },
      "thumbnailUrl": { "type": "string", "title": "Thumbnail URL" },
      "created_at": { "type": "string", "title": "CreatedAt" }
    },
    "required": ["playlistId", "title"]
  },
  "relations": {
    "has_videos": {
      "title": "Has Videos",
      "target": "youtubeVideo",
      "required": false,
      "many": true
    }
  }
}
```
<img width="1437" alt="image" src="https://github.com/user-attachments/assets/8e707aa2-b041-4e62-a4d9-f1a02e6baac9">

---

## Step 2: Set Up the GitHub Workflow

Create a GitHub workflow file at `.github/workflows/sync_youtube_data.yml`:

```yaml
name: Sync YouTube Data to Port

on:
  schedule:
    - cron: '0 */12 * * *'  # Runs every 12 hours
  workflow_dispatch:  # Manual triggers
  push:
    branches: [ main ]

jobs:
  sync-youtube-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
          
      - name: Install dependencies
        run: |
          pip install google-api-python-client isodate

      - name: Sync YouTube data
        env:
          PORT_CLIENT_ID: ${{ secrets.PORT_CLIENT_ID }}
          PORT_CLIENT_SECRET: ${{ secrets.PORT_CLIENT_SECRET }}
          YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
        run: |
          python .github/scripts/sync_youtube.py
```

### Add Secrets
Add the following secrets to your GitHub repository:

1. Go to **Settings** > **Secrets and Variables** > **Actions**.
2. Create secrets:
   - `PORT_CLIENT_ID`: Your Port Client ID
   - `PORT_CLIENT_SECRET`: Your Port Client Secret
   - `YOUTUBE_API_KEY`: Your YouTube API Key

   <img width="1440" alt="image" src="https://github.com/user-attachments/assets/cecdb05d-f314-47e8-ac84-0091a7a8c0fe">

---

## Step 3: Implement the YouTube Data Sync Script

Create a [script](https://docs.getport.io/build-your-software-catalog/custom-integration/api/#usage) (`.github/scripts/sync_youtube.py`):

```python
import requests
import os
from googleapiclient.discovery import build
import time
import isodate

CLIENT_ID = os.environ.get('PORT_CLIENT_ID')
CLIENT_SECRET = os.environ.get('PORT_CLIENT_SECRET')
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
PLAYLIST_ID = 'PL5ErBr2d3QJH0kbwTQ7HSuzvBb4zIWzhy'

API_URL = 'https://api.getport.io/v1'

def format_duration(youtube_duration):
    duration_obj = isodate.parse_duration(youtube_duration)
    minutes = int(duration_obj.total_seconds() // 60)
    seconds = int(duration_obj.total_seconds() % 60)
    return f"{minutes}:{seconds:02d}"

credentials = {
    'clientId': CLIENT_ID,
    'clientSecret': CLIENT_SECRET
}
token_response = requests.post(f'{API_URL}/auth/access_token', json=credentials)
access_token = token_response.json()['accessToken']

headers = {
    'Authorization': f'Bearer {access_token}'
}

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

playlist_request = youtube.playlists().list(
    part="snippet,contentDetails,status",
    id=PLAYLIST_ID
)
playlist_response = playlist_request.execute()
playlist = playlist_response['items'][0]

playlist_entity = {
    "identifier": PLAYLIST_ID,
    "title": playlist['snippet']['title'],
    "properties": {
        "playlistId": PLAYLIST_ID,
        "title": playlist['snippet']['title'],
        "description": playlist['snippet'].get('description', 'No description available'),
        "videoCount": playlist['contentDetails']['itemCount'],
        "thumbnailUrl": playlist['snippet']['thumbnails']['default']['url'], 
        "createdAt": playlist['snippet']['publishedAt'], 
    },
    "relations": {
        "has_videos": []
    }
}

playlist_response = requests.post(
    f'{API_URL}/blueprints/youtubePlaylist/entities?upsert=true',
    json=playlist_entity,
    headers=headers
)
print(f"Playlist sync status: {playlist_response.status_code}")

video_ids = []
next_page_token = None

while True:
    playlist_items_request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=PLAYLIST_ID,
        maxResults=50,
        pageToken=next_page_token
    )
    playlist_items = playlist_items_request.execute()
    
    err = 0
    for item in playlist_items['items']:
        video_id = item['contentDetails']['videoId']
        video_ids.append(video_id)
        
        video_request = youtube.videos().list(
            part="contentDetails,snippet,statistics",
            id=video_id
        )
        video_response = video_request.execute()
        video_details = video_response['items'][0]
        
        youtube_duration = video_details['contentDetails']['duration']
        duration_str = format_duration(youtube_duration)
        
        video_entity = {
            "identifier": video_id,
            "title": item['snippet']['title'],
            "properties": {
                "title": item['snippet']['title'],
                "videoId": video_id,
                "description": item['snippet'].get('description', 'No description available'),
                "thumbnailUrl": item['snippet']['thumbnails']['default']['url'],
                "duration": duration_str,
                "viewCount": video_details['statistics'].get('viewCount','0'),
                "likeCount": video_details['statistics'].get('likeCount','0'),
                "commentCount": video_details['statistics'].get('commentCount','0')
            },
            "relations": {
                "belongs_to_playlist": [PLAYLIST_ID]
            }
        }
        
        video_response = requests.post(
            f'{API_URL}/blueprints/youtubeVideo/entities?upsert=true',
            json=video_entity,
            headers=headers
        )
        print(f"Video sync status for {video_id}: {video_response.status_code}")
        
        time.sleep(0.1)
    
    next_page_token = playlist_items.get('nextPageToken')
    if not next_page_token:
        break

playlist_entity["relations"]["has_videos"] = video_ids
final_playlist_response = requests.post(
    f'{API_URL}/blueprints/youtubePlaylist/entities?upsert=true',
    json=playlist_entity,
    headers=headers
)
    
```

---

## Step 4: Run and Verify the Workflow

1. **Trigger the Action**: Run the GitHub action manually or wait for the scheduled run.
<img width="1440" alt="image" src="https://github.com/user-attachments/assets/a3b2c496-f5eb-4621-9ab0-d75eb3005f3d">

3. **Check the Logs**: Review the workflow logs for the status of the ingestion process.
   
<img width="1439" alt="image" src="https://github.com/user-attachments/assets/1c46fa56-7370-421b-ba42-b9c5415471e6">

4. **Verify in Port**: Ensure the data appears in your Port account with proper relationships.
   
   <img width="1433" alt="image" src="https://github.com/user-attachments/assets/e1d69c90-fde8-4ede-83ae-e4111fb398d6">

---

## Step 5: Visualize Data in Port

Leverage Port's [visualization](https://docs.getport.io/customize-pages-dashboards-and-plugins/dashboards/) tools for insights:

- **Playlist Metrics**: Display video count and total views.
- **Engagement Analysis**: Use dashboards to monitor likes and comments.

  <img width="1435" alt="image" src="https://github.com/user-attachments/assets/17684b56-3b9d-4b74-9cc4-37c7ee165db8">

---

## Conclusion

By following this guide, you can effectively ingest and visualize YouTube playlist data in Port, enabling data-driven decisions and enhancing your content strategy.

---
