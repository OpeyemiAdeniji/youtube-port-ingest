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