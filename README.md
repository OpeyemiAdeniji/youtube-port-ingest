# Ingest YouTube Playlist Data into Port
This guide provides a comprehensive walkthrough for creating a self-service action in Port that uses a GitHub workflow to automate the ingestion of YouTube playlist data into Port.

> [!Use cases]  
> **Content Management**: Keep track of video details within your internal software catalog.
>
> **Analytics**: Integrate video data for better insights and decision-making.
>
> **Automation**: Automatically update your Port account with video and playlist metadata.

## Prerequisites

Ensure you have the following before getting started:

- **Port's GitHub Integration**: Install it by clicking [here](https://github.com/apps/getport-io/installations/select_target). This is essential for Port to interact with your GitHub repositories.
- **Port Actions Knowledge**: Understanding how to create and use Port actions. Learn the basics [here](https://docs.getport.io/actions-and-automations/create-self-service-experiences/setup-ui-for-action/).
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

1. **Create the `playlist` blueprints**:
   - Navigate to the [Builder](https://app.getport.io/settings/data-model) page in Port.
   - Click **+ Blueprint** and select **Edit JSON**.
   
  <details>

  Paste the following configuration:

  <summary>Playlist blueprint (click to expand)</summary>

   ```json
{
  "identifier": "playlist",
  "title": "Playlist",
  "icon": "Youtrack",
  "schema": {
    "properties": {
      "description": {
        "type": "string",
        "title": "Description"
      },
      "videoCount": {
        "type": "number",
        "title": "Video Count"
      },
      "thumbnailUrl": {
        "type": "string",
        "title": "Thumbnail URL"
      },
      "created_at": {
        "type": "string",
        "title": "CreatedAt"
      }
    },
    "required": []
  },
  "mirrorProperties": {},
  "calculationProperties": {},
  "aggregationProperties": {},
  "relations": {}
}
```
</details>

2. **Create the `videos` blueprints**:

<details>

  Repeat the same process as in playlist blueprint and paste the following configurations:
  
<summary>Video blueprint (click to expand)</summary>

   ```json
{
  "identifier": "video",
  "description": "This blueprint represents a video in our software catalog",
  "title": "Video",
  "icon": "Youtrack",
  "schema": {
    "properties": {
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
    "required": []
  },
  "mirrorProperties": {},
  "calculationProperties": {},
  "aggregationProperties": {},
  "relations": {
    "playlist": {
      "title": "Playlist",
      "target": "playlist",
      "required": false,
      "many": false
    }
  }
}
```
</details>

## Creating the Port Action

1. Go to the **Self-Service** page in Port.
2. Click **+ New Action** and select **Edit JSON**.

<details>
<summary>Port Action (click to expand)</summary>
   
:::tip Replace placeholders

- `<GITHUB-ORG>` – your GitHub organization or user name.
- `<GITHUB-REPO-NAME>` – your GitHub repository name.

  **Note:** The provided workflow file is named `youtube-ingest.yml`. You can rename it to any name you prefer, as long as it resides in the `.github/workflows/` folder path.

:::

 Paste the following action configuration:
  
   ```json
{
    "identifier": "ingest-youtube-playlist",
    "title": "Ingest Youtube Playlist",
    "icon": "Youtrack",
    "description": "Add a YouTube playlist and create its corresponding playlist entity.",
    "trigger": {
      "type": "self-service",
      "operation": "CREATE",
      "userInputs": {
        "properties": {
          "playlistid": {
            "icon": "DefaultProperty",
            "type": "string",
            "title": "Playlist ID"
          }
        },
        "required": [
          "playlistid"
        ],
        "order": [
          "playlistid"
        ]
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

Create a GitHub workflow file under `.github/workflows/youtube-ingest.yml` to act as the backend for the Port action, using the following content:

<details>
<summary>Github Workflow (click to expand)</summary>
  
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
  prepare_token:
    runs-on: ubuntu-latest
    env:
      PORT_CLIENT_ID: ${{ secrets.PORT_CLIENT_ID }}
      PORT_CLIENT_SECRET: ${{ secrets.PORT_CLIENT_SECRET }}
    steps:
      - name: Create Data Directory
        run: mkdir -p data

      - name: Generate Access Token
        run: |
          set -e
          PORT_CLIENT_ID=$(echo "$PORT_CLIENT_ID" | xargs)
          PORT_CLIENT_SECRET=$(echo "$PORT_CLIENT_SECRET" | xargs)
          
          response=$(curl -s -X POST "https://api.getport.io/v1/auth/access_token" \
            -H "Content-Type: application/json" \
            -d "{\"clientId\": \"$PORT_CLIENT_ID\", \"clientSecret\": \"$PORT_CLIENT_SECRET\"}")
          
          ACCESS_TOKEN=$(echo "$response" | jq -r '.accessToken')
          echo "Bearer $ACCESS_TOKEN" > data/token.txt

      - name: Upload Token Artifact
        uses: actions/upload-artifact@v4
        with:
          name: port-token
          path: data/token.txt
          retention-days: 1

  fetch_playlist_metadata:
    needs: prepare_token
    runs-on: ubuntu-latest
    env:
      YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
      PLAYLIST_ID: ${{ inputs.playlistid }}
    outputs:
      playlist_id: ${{ steps.fetch_metadata.outputs.PLAYLIST_ID }}
      playlist_data: ${{ steps.fetch_metadata.outputs.PLAYLIST_DATA }}
    steps:
      - name: Download Token Artifact
        uses: actions/download-artifact@v4
        with:
          name: port-token
          path: data

      - name: Load Token
        run: |
          TOKEN=$(cat data/token.txt)
          echo "ACCESS_TOKEN=$TOKEN" >> $GITHUB_ENV

      - name: Send Start Logs to Port
        id: start_log
        run: |
          set -e
          PORT_RUN_ID=$(echo '${{ inputs.port_context }}' | jq -r '.runId')
          curl -L "https://api.getport.io/v1/actions/runs/$PORT_RUN_ID/logs" \
            -H "Content-Type: application/json" \
            -H "Authorization: $ACCESS_TOKEN" \
            -d '{
              "message": "Metadata fetch of playlist has commenced PLAYLIST_ID - '$PLAYLIST_ID'",
              "statusLabel": "Fetching Playlist"
            }'

      - name: Fetch YouTube Playlist Metadata
        id: fetch_metadata
        run: |
          playlist_response=$(curl -s "https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails,status&id=${PLAYLIST_ID}&key=${YOUTUBE_API_KEY}")
          playlist_id=$(echo $playlist_response | jq -r '.items[0].id')
          
          if [ -z "$playlist_id" ]; then
            echo "Failed to fetch playlist details. Exiting."
            exit 1
          fi
          playlist_data=$(echo $playlist_response | jq -c '.items[0] | {
            identifier: .id,
            title: .snippet.title,
            properties: {
              description: .snippet.description,
              thumbnailUrl: .snippet.thumbnails.default.url,
              videoCount: .contentDetails.itemCount,
              created_at: .snippet.publishedAt
            }
          }')
          echo "PLAYLIST_ID=$playlist_id" >> $GITHUB_OUTPUT
          echo "PLAYLIST_DATA=$playlist_data" >> $GITHUB_OUTPUT

      - name: Send Completion Logs to Port
        if: success()
        run: |
          PORT_RUN_ID=$(echo '${{ inputs.port_context }}' | jq -r '.runId')
          curl -L "https://api.getport.io/v1/actions/runs/$PORT_RUN_ID/logs" \
            -H "Content-Type: application/json" \
            -H "Authorization: $ACCESS_TOKEN" \
            -d '{
              "message": "Successfully fetched playlist metadata PLAYLIST_ID - '$PLAYLIST_ID'",
              "statusLabel": "Playlist Fetched"
            }'

  push_playlist_to_port:
    needs: fetch_playlist_metadata
    runs-on: ubuntu-latest
    env:
      PLAYLIST_ID: ${{ inputs.playlistid }}
    steps:
      - name: Download Token Artifact
        uses: actions/download-artifact@v4
        with:
          name: port-token
          path: data

      - name: Load Token
        run: |
          TOKEN=$(cat data/token.txt)
          echo "ACCESS_TOKEN=$TOKEN" >> $GITHUB_ENV

      - name: Send Start Logs to Port
        run: |
          PORT_RUN_ID=$(echo '${{ inputs.port_context }}' | jq -r '.runId')
          curl -L "https://api.getport.io/v1/actions/runs/$PORT_RUN_ID/logs" \
            -H "Content-Type: application/json" \
            -H "Authorization: $ACCESS_TOKEN" \
            -d '{
              "message": "ingesting playlist data to Port has commenced PLAYLIST_ID - '$PLAYLIST_ID'",
              "statusLabel": "ingesting Playlist to Port"
            }'

      - name: Push Playlist Data to Port
        run: |
          playlist_entity='${{ needs.fetch_playlist_metadata.outputs.playlist_data }}'
          
          response=$(curl -s -w "%{http_code}" -X POST "https://api.getport.io/v1/blueprints/playlist/entities?upsert=true" \
            -H "Authorization: $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$playlist_entity")
          
          if [[ "${response: -3}" != "200" && "${response: -3}" != "201" ]]; then
            echo "Failed to push playlist to Port. Response: $response"
            exit 1
          fi

      - name: Send Completion Logs to Port
        if: success()
        run: |
          PORT_RUN_ID=$(echo '${{ inputs.port_context }}' | jq -r '.runId')
          curl -L "https://api.getport.io/v1/actions/runs/$PORT_RUN_ID/logs" \
            -H "Content-Type: application/json" \
            -H "Authorization: $ACCESS_TOKEN" \
            -d '{
              "message": "Successfully ingested playlist data to Port PLAYLIST_ID - '$PLAYLIST_ID'",
              "statusLabel": "Playlist ingested"
            }'

  fetch_and_ingest_videos:
    needs: push_playlist_to_port
    runs-on: ubuntu-latest
    env:
      YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
      PLAYLIST_ID: ${{ inputs.playlistid }}
    steps:
      - name: Download Token Artifact
        uses: actions/download-artifact@v4
        with:
          name: port-token
          path: data

      - name: Load Token
        run: |
          TOKEN=$(cat data/token.txt)
          echo "ACCESS_TOKEN=$TOKEN" >> $GITHUB_ENV

      - name: Send Start Logs to Port
        run: |
          PORT_RUN_ID=$(echo '${{ inputs.port_context }}' | jq -r '.runId')
          curl -L "https://api.getport.io/v1/actions/runs/$PORT_RUN_ID/logs" \
            -H "Content-Type: application/json" \
            -H "Authorization: $ACCESS_TOKEN" \
            -d '{
              "message": "Extraction and ingesting of video data from YouTube has commenced PLAYLIST_ID - '$PLAYLIST_ID'",
              "statusLabel": "Fetching and ingesting Videos"
            }'

      - name: Collect Video Data and Ingest
        id: collect_videos
        run: |
          # Process playlist videos
          next_page_token=""
          while :; do
            echo "Fetching playlist page${next_page_token:+ with token $next_page_token}..."
            
            url="https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=${PLAYLIST_ID}&key=${YOUTUBE_API_KEY}${next_page_token:+&pageToken=$next_page_token}"
            response=$(curl -s "$url")
            
            # Check for API errors
            if [ "$(echo "$response" | jq -r '.error.code // empty')" != "" ]; then
              echo "YouTube API Error: $(echo "$response" | jq -r '.error.message')"
              exit 1
            fi
            
            next_page_token=$(echo "$response" | jq -r '.nextPageToken // empty')
            video_ids=$(echo "$response" | jq -r '.items[].snippet.resourceId.videoId')
            
            for video_id in $video_ids; do
              echo "Processing video ID: $video_id"
              
              video_details=$(curl -s "https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=$video_id&key=${YOUTUBE_API_KEY}")
              
              # Extract video details
              video_title=$(echo "$video_details" | jq -r '.items[0].snippet.title')
              video_description=$(echo "$video_details" | jq -r '.items[0].snippet.description')
              video_thumbnail=$(echo "$video_details" | jq -r '.items[0].snippet.thumbnails.default.url')
              video_duration=$(echo "$video_details" | jq -r '.items[0].contentDetails.duration')
              video_view_count=$(echo "$video_details" | jq -r '.items[0].statistics.viewCount // "0"')
              video_like_count=$(echo "$video_details" | jq -r '.items[0].statistics.likeCount // "0"')
              video_comment_count=$(echo "$video_details" | jq -r '.items[0].statistics.commentCount // "0"')
              
              # Create video entity in Port
              video_entity=$(jq -n \
                --arg id "$video_id" \
                --arg title "$video_title" \
                --arg description "$video_description" \
                --arg thumbnailUrl "$video_thumbnail" \
                --arg duration "$video_duration" \
                --arg viewCount "$video_view_count" \
                --arg likeCount "$video_like_count" \
                --arg commentCount "$video_comment_count" \
                --arg playlist_id "$PLAYLIST_ID" \
                '{
                  identifier: $id,
                  title: $title,
                  properties: {       
                    description: $description,
                    thumbnailUrl: $thumbnailUrl,
                    duration: $duration,
                    viewCount: ($viewCount | tonumber),
                    likeCount: ($likeCount | tonumber),
                    commentCount: ($commentCount | tonumber)
                  },
                  relations: {
                    playlist: $playlist_id
                  }
                }')
              
              response=$(curl --http1.1 -s -w "\n%{http_code}" -X POST "https://api.getport.io/v1/blueprints/video/entities?upsert=true" \
                -H "Authorization: $ACCESS_TOKEN" \
                -H "Content-Type: application/json" \
                -d "$video_entity")
              
              http_code=$(echo "$response" | tail -n1)
              body=$(echo "$response" | sed '$d')
              
              if [[ ! "$http_code" =~ ^2[0-9][0-9]$ ]]; then
                echo "Failed to push video to Port. HTTP code: $http_code"
                echo "Response Body: $body"
                continue
              fi
              
              echo "Successfully processed video: $video_id"
            done
            
            if [ -z "$next_page_token" ]; then
              echo "No more pages to process"
              break
            fi
          done

      - name: Send Completion Logs to Port
        if: success()
        run: |
          PORT_RUN_ID=$(echo '${{ inputs.port_context }}' | jq -r '.runId')
          curl -L "https://api.getport.io/v1/actions/runs/$PORT_RUN_ID/logs" \
            -H "Content-Type: application/json" \
            -H "Authorization: $ACCESS_TOKEN" \
            -d '{
              "message": "Successfully fetched and ingested all videos PLAYLIST_ID - '$PLAYLIST_ID'",
              "statusLabel": "Videos Fetched and ingested"
            }'

      - name: Handle Job Completion
        if: always()
        run: |
          PORT_RUN_ID=$(echo '${{ inputs.port_context }}' | jq -r '.runId')
          if [[ "$?" == "0" ]]; then
            STATUS_LABEL="Success"
            MESSAGE="Successfully ingested Youtube data to Port!"
          else
            STATUS_LABEL="Failed"
            MESSAGE="Failed to complete video processing"
          fi
          
          curl -L "https://api.getport.io/v1/actions/runs/$PORT_RUN_ID/logs" \
            -H "Content-Type: application/json" \
            -H "Authorization: $ACCESS_TOKEN" \
            -d "{
              \"message\": \"$MESSAGE\",
              \"statusLabel\": \"$STATUS_LABEL\"
            }"
```
</details>


## Testing the Action

1. On the [self-service](https://app.getport.io/self-serve) page, select the Ingest Youtube Playlist action
2. Fill in the required properties (YouTube Playlist ID).
3. Click **Execute** to trigger the GitHub workflow.
4. Verify that the video and playlist entities have been ingested by checking your Port [catalog](https://app.getport.io/playlists)


## Visualization

By leveraging Port's Dashboards, you can create custom dashboards to track the metrics and monitor your team's performance over time.

### Dashboard Setup

1. Go to your [software catalog](https://app.getport.io/organization/catalog).
2. Click on the `+ New` button in the left sidebar.
3. Select **New dashboard**.
4. Name the dashboard (e.g., Playlist Metrics), choose an icon if desired, and click Create.
   
This will create a new empty dashboard. Let's get ready to add widgets.


### Adding widgets

We will create 5 widgets inside the dashboard to display the key metrics we are interested in.

<details>
 <summary>Setup number of views widget</summary>
   
   1. `Click +` Widget and select Number Chart.

   2. Title: Enter **Views** in the input box

   3. Add an optional icon if you prefer.

   4. Select **Aggregrate by property** option under the **Chart type** and choose **Video** as the blueprint.

   5. Select `View Count` as Property and `Sum` as the Function

   <img width="629" alt="image" src="https://github.com/user-attachments/assets/f87fc98e-5f43-49ed-8efa-c966ce03d80a">

   6. Click Save.

</details>


<details>
 <summary>Setup Video likes widget</summary>
   
   1. `Click +` Widget and select Number Chart.

   2. Title: Enter **Likes** in the input box.

   3. Add an optional icon if you prefer.

   4. Select **Aggregrate by property** option under the **Chart type** and choose **Video** as the blueprint.

   5. Select Like Count as Property and Sum as the Function

   <img width="625" alt="image" src="https://github.com/user-attachments/assets/aa432bd5-1549-42e8-a7c1-e1f1e94c1184">

   6. Click Save.

</details>


<details>
 <summary>Setup video/playlist comments widget</summary>
   
   1. `Click +`Widget and select Number Chart.

   2. Title: Enter **Comments** in the input box.

   3. Add an optional icon if you prefer.

   4. Select **Aggregrate by property** option under the **Chart type** and choose **Video** as the blueprint.

   5. Select Comment Count as Property and Sum as the Function

   <img width="622" alt="image" src="https://github.com/user-attachments/assets/e3525ade-748d-4783-9878-2862aa097647">

   6. Click Save.

</details>


<details>
 <summary>Setup Video Lists widget</summary>
   
   1. `Click +` Widget and select Table.

   2. Title: Enter **Video Lists** in the input box.

   3. Add an optional icon if you prefer.

   4. Choose **Video** as the blueprint.

   5. Add Description and ThumbnailURL as excluded property.

   <img width="623" alt="image" src="https://github.com/user-attachments/assets/7311854f-a905-4967-9c48-b12e4dd03f09">

   6. Click Save.

</details>


<details>
 <summary>Setup View Count widget</summary>
   
   1. `Click +` Widget and select Pie Chart.

   2. Title: Enter **View Count** in the input box.

   3. Add an optional icon if you prefer.

   4. Choose **Video** as the blueprint.

   5. Select Breakdown Property as View Count

   <img width="625" alt="image" src="https://github.com/user-attachments/assets/42e9b9e0-c7f0-4112-877e-16cd54720254">

   6. Click Save.

</details>

<details>
 <summary>Overall Dashboard View</summary>

 <img width="1201" alt="image" src="https://github.com/user-attachments/assets/a7bed816-8835-47db-ac27-e4d9805118c3">

</details>

## Conclusion
By following this guide, you have successfully ingested your YouTube playlist and video contents into Port.
