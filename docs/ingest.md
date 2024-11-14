# Ingest YouTube Playlist Data into Port
This guide provides a comprehensive walkthrough for creating a self-service action in Port that uses a GitHub workflow to automate the ingestion of YouTube playlist data into Port.

> 💡 **USE-CASES**  
> Ingest YouTube playlist data into Port for streamlined management and integration.
> 
>  **Content Management**: Keep track of video details within your internal software catalog.
>
>  **Analytics**: Integrate video data for better insights and decision-making.
>
>  **Automation**: Automatically update your Port account with video and playlist metadata.

## Prerequisites

Ensure you have the following before getting started:

- **Port's GitHub Integration**: Install it by clicking [here](https://github.com/apps/getport-io/installations/select_target). This is essential for Port to interact with your GitHub repositories.
- **Port Actions Knowledge**: Understanding how to create and use Port actions.Learn the basics [here](https://docs.getport.io/actions-and-automations/create-self-service-experiences/setup-ui-for-action/).
- **GitHub Repository**: A repository to store your GitHub workflow file.
- This guide assumes the presence of a blueprint. If you haven't done so yet, initiate the setup of your data model by referring to this [guide](https://docs.getport.io/build-your-software-catalog/customize-integrations/configure-data-model/) first.

## GitHub Secrets

To execute this workflow, add the following secrets to your GitHub repository:

1. **GitHub Action Secrets**:
   - Navigate to your repository's **Settings > Secrets and Variables > Actions**.
   - Add these secrets:
     - **PORT_CLIENT_ID**: Your Port Client ID [learn more](https://docs.getport.io/build-your-software-catalog/custom-integration/api/#find-your-port-credentials).
     - **PORT_CLIENT_SECRET**: Your Port Client Secret [learn more](https://docs.getport.io/build-your-software-catalog/custom-integration/api/#find-your-port-credentials)..
     - **YOUTUBE_API_KEY**: Your Youtube API Key [learn more](https://developers.google.com/youtube/v3/docs#calling-the-api).

## Port Configuration

### Import Youtube Resources

1. **Create the `playlist` and `video` blueprints**:
   - Navigate to the [Builder](https://app.getport.io/settings/data-model) page in Port.
   - Click **+ Blueprint** and select **Edit JSON**.
   - Paste the following configuration:

  <details>
  <summary>Click to copy Playlist and Video Blueprint JSON</summary>

   ```json
{
     "identifier": "playlist",
     "description": "This blueprint represents a YouTube playlist",
     "title": "playlist",
     "icon": "Widget",
     "schema": {
       "properties": {
         "playlistId": {
           "type": "string",
           "title": "Playlist ID"
         },
         "title": {
           "type": "string",
           "title": "Title"
         },
         "description": {
           "type": "string",
           "title": "Description"
         },
         "thumbnailUrl": {
           "type": "string",
           "title": "Thumbnail URL"
         },
         "videoCount": {
           "type": "number",
           "title": "Number of Videos"
         },
         "created_at": {
           "type": "string",
           "title": "Published At"
         }
       },
       "required": ["playlistId", "title"]
     }
}
```



   ```json
{
    "identifier": "video",
    "description": "This blueprint represents a video in our software catalog",
    "title": "video",
    "icon": "Widget",
    "schema": {
      "properties": {
        "videoId": {
          "type": "string",
          "title": "Video ID"
        },
        "title": {
          "type": "string",
          "title": "Title"
        },
        "description": {
          "type": "string",
          "title": "Description"
        },
        "thumbnailUrl": {
          "type": "string",
          "title": "Thumbnail URL"
        },
        "duration": {
          "type": "string",
          "title": "Duration"
        },
        "viewCount": {
          "type": "number",
          "title": "View Count"
        },
        "likeCount": {
          "type": "number",
          "title": "Like Count"
        },
        "commentCount": {
          "type": "number",
          "title": "Comment Count"
        }
      },
      "required": ["videoId", "title"]
    },
    "relations": {
      "belongs_to_playlist": {
        "title": "Belongs to Playlist",
        "target": "playlist",
        "required": false,
        "many": false
      }
    }
```
</details>

## Creating the Port Action

1. Go to the **Self-Service** page in Port.
2. Click **+ New Action** and select **Edit JSON**.
3. Paste the following action configuration:

<details>
<summary>Click to copy Port Action JSON</summary>
   
:::💡Tip

- `<GITHUB-ORG>` – your GitHub organization or user name.
- `<GITHUB-REPO-NAME>` – your GitHub repository name.

:::
  
   ```json
   {
      "identifier": "ingest-youtube-playlist",
      "title": "Ingest Youtube Playlist",
      "icon": "Youtrack",
      "trigger": {
        "type": "self-service",
        "operation": "CREATE",
        "userInputs": {
          "properties": {
            "playlistid": {
              "type": "string",
              "title": "playlistid"
            }
          },
          "required": [
            "playlistid"
          ],
          "order": []
        },
        "blueprintIdentifier": "playlist"
      },
      "invocationMethod": {
        "type": "GITHUB",
        "org": "<GITHUB-ORG>",
        "repo": "<GITHUB-REPO-NAME>",
        "workflow": "youtube-ingest.yml",
        "workflowInputs": {
          "{{ spreadValue() }}": "{{ .inputs }}",
          "port_context": {
            "runId": "{{ .run.id }}",
            "blueprint": "{{ .action.blueprint }}"
          }
        },
        "reportWorkflowStatus": true
      },
      "requiredApproval": false
    }
   
   ```
 </details>

## GitHub Workflow

Create a workflow file under `.github/workflows/youtube-ingest.yml` with the following content:

<details>
<summary>Github Workflow Script</summary>
  
```yaml
name: Update Port with YouTube Playlist Data
on:
  workflow_dispatch:
    inputs:
      playlistid:
        description: 'ID of the YouTube playlist'
        required: true
      port_context:
        description: 'Port context payload'
        required: true

jobs:
  update_port:
    runs-on: ubuntu-latest
    env:
      PORT_CLIENT_ID: ${{ secrets.PORT_CLIENT_ID }}
      PORT_CLIENT_SECRET: ${{ secrets.PORT_CLIENT_SECRET }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      PORT_RUN_ID: ${{ fromJson(inputs.port_context).runId }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install jq for JSON processing
        run: sudo apt-get install jq

      - name: Fetch and Process YouTube Data using Bash
        id: fetch_data
        env:
          YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
          PLAYLIST_ID: ${{ inputs.playlistid }}
          PORT_CLIENT_ID: ${{ secrets.PORT_CLIENT_ID }}
          PORT_CLIENT_SECRET: ${{ secrets.PORT_CLIENT_SECRET }}
        run: |
          set -e  # Exit immediately if any command returns a non-zero status

          # Ensure environment variables are trimmed of whitespace
          PORT_CLIENT_ID=$(echo "$PORT_CLIENT_ID" | xargs)
          PORT_CLIENT_SECRET=$(echo "$PORT_CLIENT_SECRET" | xargs)

          # Function to get Port access token
          get_port_access_token() {
            response=$(curl -s -X POST "https://api.getport.io/v1/auth/access_token" \
              -H "Content-Type: application/json" \
              -d '{
                "clientId": "'"$PORT_CLIENT_ID"'",
                "clientSecret": "'"$PORT_CLIENT_SECRET"'"
              }')

            # Check if the response contains an error
            if echo "$response" | grep -q '"ok":false'; then
              echo "Error obtaining access token: $(echo "$response" | jq -r '.error' )"
              return 1
            fi

            # Extract the access token from the response
            access_token=$(echo "$response" | jq -r '.accessToken // empty')
            if [ -z "$access_token" ]; then
              echo "Failed to retrieve access token. Response: $response"
              return 1
            fi

            echo "$access_token"
          }

          # Retrieve and sanitize the access token
          ACCESS_TOKEN=$(get_port_access_token)
          if [ -z "$ACCESS_TOKEN" ]; then
            echo "Failed to obtain access token. Exiting."
            exit 1
          fi

          echo "Access token obtained: ${ACCESS_TOKEN:0:50}..."

          # Validate the JWT format
          if ! [[ "$ACCESS_TOKEN" =~ ^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+$ ]]; then
            echo "Invalid JWT format detected. Please check the token generation."
            exit 1
          fi

          # Fetch playlist details
          playlist_response=$(curl -s "https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails,status&id=${PLAYLIST_ID}&key=${YOUTUBE_API_KEY}")
          playlist_id=$(echo $playlist_response | jq -r '.items[0].id')
          playlist_title=$(echo $playlist_response | jq -r '.items[0].snippet.title')
          playlist_description=$(echo $playlist_response | jq -r '.items[0].snippet.description')
          playlist_thumbnail=$(echo $playlist_response | jq -r '.items[0].snippet.thumbnails.default.url')
          playlist_video_count=$(echo $playlist_response | jq -r '.items[0].contentDetails.itemCount')
          playlist_published_at=$(echo $playlist_response | jq -r '.items[0].snippet.publishedAt')

          # Create playlist entity payload
          playlist_entity=$(jq -n --arg id "$playlist_id" --arg title "$playlist_title" \
            --arg description "$playlist_description" --arg thumbnailUrl "$playlist_thumbnail" \
            --arg videoCount "$playlist_video_count" --arg created_at "$playlist_published_at" \
            '{
              identifier: $id,
              title: $title,
              properties: {
                playlistId: $id,
                title: $title,
                description: $description,
                thumbnailUrl: $thumbnailUrl,
                videoCount: ($videoCount | tonumber),
                created_at: $created_at
              }
            }')

          # Print JSON payload for validation
          echo "Payload: $playlist_entity"
          echo "$playlist_entity" | jq .

          # Use HTTP/1.1 to avoid HTTP/2 protocol issues and capture response
          response=$(curl --http1.1 -s -w "%{http_code}\n" -o /tmp/playlist_response.json -X POST "https://api.getport.io/v1/blueprints/playlist/entities?upsert=true" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$playlist_entity")

          http_code=$(echo "$response" | head -c 1)
          body=$(cat /tmp/playlist_response.json)

          echo "HTTP Response Code: $http_code"
          echo "Response Body: $body"

          if [[ "$http_code" != "2" ]]; then
            echo "Failed to push playlist to Port. HTTP code: $http_code"
            echo "Response Body: $body"
            exit 1
          fi

          # Fetch and process videos in the playlist
          next_page_token=""
          while :; do
            url="https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=${PLAYLIST_ID}&key=${YOUTUBE_API_KEY}${next_page_token:+&pageToken=$next_page_token}"
            response=$(curl -s "$url")
            next_page_token=$(echo $response | jq -r '.nextPageToken // empty')

            video_ids=$(echo $response | jq -r '.items[].snippet.resourceId.videoId')
            for video_id in $video_ids; do
              video_details=$(curl -s "https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=$video_id&key=${YOUTUBE_API_KEY}")
              video_title=$(echo $video_details | jq -r '.items[0].snippet.title')
              video_description=$(echo $video_details | jq -r '.items[0].snippet.description')
              video_thumbnail=$(echo $video_details | jq -r '.items[0].snippet.thumbnails.default.url')
              video_duration=$(echo $video_details | jq -r '.items[0].contentDetails.duration')
              video_view_count=$(echo $video_details | jq -r '.items[0].statistics.viewCount // 0')
              video_like_count=$(echo $video_details | jq -r '.items[0].statistics.likeCount // 0')
              video_comment_count=$(echo $video_details | jq -r '.items[0].statistics.commentCount // 0')

              # Create video entity payload
              video_entity=$(jq -n --arg id "$video_id" --arg title "$video_title" \
                --arg description "$video_description" --arg thumbnailUrl "$video_thumbnail" \
                --arg duration "$video_duration" --argjson viewCount "$video_view_count" \
                --argjson likeCount "$video_like_count" --argjson commentCount "$video_comment_count" \
                --arg playlistId "$playlist_id" \
                '{
                  identifier: $id,
                  title: $title,
                  properties: {
                    videoId: $id,
                    title: $title,
                    description: $description,
                    thumbnailUrl: $thumbnailUrl,
                    duration: $duration,
                    viewCount: $viewCount,
                    likeCount: $likeCount,
                    commentCount: $commentCount
                  },
                  relations: {
                    belongs_to_playlist: $playlistId
                  }
                }')

              # Print video payload for validation
              echo "Video Payload: $video_entity"
              echo "$video_entity" | jq .

              # Use HTTP/1.1 to avoid HTTP/2 protocol issues and capture response
              response=$(curl --http1.1 -s -w "%{http_code}\n" -o /tmp/video_response.json -X POST "https://api.getport.io/v1/blueprints/video/entities?upsert=true" \
                -H "Authorization: Bearer $ACCESS_TOKEN" \
                -H "Content-Type: application/json" \
                -d "$video_entity")

              http_code=$(echo "$response" | head -c 1)
              body=$(cat /tmp/video_response.json)

              echo "HTTP Response Code: $http_code"
              echo "Response Body: $body"

              if [[ "$http_code" != "2" ]]; then
                echo "Failed to push video to Port. HTTP code: $http_code"
                echo "Response Body: $body"
                exit 1
              fi
            done

            [[ -z "$next_page_token" ]] && break
          done
```
</details>


## Testing the Action

1. On the [self-service](https://app.getport.io/self-serve) page, select the action
2. Fill in the required properties (YouTube Playlist ID).
3. Click **Execute** to trigger the GitHub workflow.


## Visualization

By leveraging Port's Dashboards, you can create custom dashboards to track the metrics and monitor your team's performance over time.

### Dashboard Setup

1. Go to your [software catalog](https://app.getport.io/organization/catalog).
2. Click on the `+ New` button in the left sidebar.
3. Select **New dashboard**.
4. Name the dashboard (e.g., Playlist Metrics), choose an icon if desired, and click Create.
   
This will create a new empty dashboard. Let's get ready-to-add widgets


### Adding widgets
<details>
 <summary>Setup Views widget</summary>
   
   1. `Click +` Widget and select Number Chart.

   2. Title: Views, (add the metric icon).

   3. Select Aggregrate by property and choose video as the Blueprint.

   4. Select View Count as Property and Sum as the Function

   <img width="613" alt="image" src="https://github.com/user-attachments/assets/14fec310-7bf6-42ad-b9b7-5e850c234133">

   5. Click Save.

</details>


<details>
 <summary>Setup Likes widget</summary>
   
   1. `Click +` Widget and select Number Chart.

   2. Title: Likes, (add the star icon).

   3. Select Aggregrate by property and choose video as the Blueprint.

   4. Select Like Count as Property and Sum as the Function

   <img width="610" alt="image" src="https://github.com/user-attachments/assets/3cf8acb0-6645-40bb-b467-a2ffcb4043f5">

   5. Click Save.

</details>


<details>
 <summary>Setup Comments widget</summary>
   
   1. `Click +`Widget and select Number Chart.

   2. Title: Comments, (add the metric icon).

   3. Select Aggregrate by property and choose video as the Blueprint.

   4. Select Comment Count as Property and Sum as the Function

   <img width="610" alt="image" src="https://github.com/user-attachments/assets/9d484f27-aa48-4c81-ade3-bd1b720d9bed">

   5. Click Save.

</details>


<details>
 <summary>Setup Video Lists widget</summary>
   
   1. `Click +` Widget and select Table.

   2. Title: Video Lists, (add the store icon).

   3. Select Video as the Blueprint.

   4. Add Description and ThumbnailURL as excluded property.

   <img width="612" alt="image" src="https://github.com/user-attachments/assets/c947e440-908c-472a-8a58-8dd65c8fbc8e">

   5. Click Save.

</details>


<details>
 <summary>Setup View Count widget</summary>
   
   1. `Click +` Widget and select Pie Chart.

   2. Title: View Count, (add the pie icon).

   3. Choose video as the Blueprint.

   4. Select Breakdown Property as View Count

   <img width="605" alt="image" src="https://github.com/user-attachments/assets/0757af44-b6b3-45bd-9765-d9f5eea199df">

   4. Click Save.

</details>

<details>
 <summary>Overall Dashboard View</summary>

<img width="1104" alt="image" src="https://github.com/user-attachments/assets/8dd333a0-eb42-45fa-9f80-78d96f111238">

</details>
