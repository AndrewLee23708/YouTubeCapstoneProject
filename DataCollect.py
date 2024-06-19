from googleapiclient.discovery import build
# pip install google-api-python-client pandas
# For documentations, go to https://developers.google.com/youtube/v3/docs

import pandas as pd
import requests
from PIL import Image
from io import BytesIO

# Set up YouTube API
api_key = 'AIzaSyBg_bTSyo-ibJzHTRqkqmkM34DuXrJDiPE'
youtube = build('youtube', 'v3', developerKey=api_key)

# Function to get video details
def get_video_details(video_id):
    video_response = youtube.videos().list(
        part='snippet,contentDetails,statistics,topicDetails',
        id=video_id
    ).execute()

    if video_response['items']:
        video = video_response['items'][0]
        snippet = video['snippet']
        content_details = video['contentDetails']
        statistics = video['statistics']
        topic_details = video.get('topicDetails', {})
        
        # Download thumbnail and get its size
        thumbnail_url = snippet['thumbnails']['high']['url']
        response = requests.get(thumbnail_url)
        img = Image.open(BytesIO(response.content))
        thumbnail_size = img.size

        return {
            'video_id': video_id,
            'title': snippet['title'],
            'published_at': snippet['publishedAt'],
            'channel_id': snippet['channelId'],
            'category_id': snippet['categoryId'],
            'tags': snippet.get('tags', []),
            'view_count': statistics.get('viewCount', 0),
            'like_count': statistics.get('likeCount', 0),
            'comment_count': statistics.get('commentCount', 0),
            'duration': content_details['duration'],
            'definition': content_details['definition'],
            'caption': content_details['caption'],
            'thumbnail_url': thumbnail_url,
            'thumbnail_width': thumbnail_size[0],
            'thumbnail_height': thumbnail_size[1],
            'topic_categories': topic_details.get('topicCategories', []),
        }
    else:
        return None

# Function to get channel details
def get_channel_details(channel_id):
    channel_response = youtube.channels().list(
        part='snippet,contentDetails,statistics,topicDetails,status,brandingSettings',
        id=channel_id
    ).execute()

    if channel_response['items']:
        channel = channel_response['items'][0]
        snippet = channel['snippet']
        statistics = channel['statistics']
        content_details = channel['contentDetails']
        topic_details = channel.get('topicDetails', {})
        status = channel.get('status', {})
        branding_settings = channel.get('brandingSettings', {})

        return {
            'channel_id': channel_id,
            'channel_title': snippet['title'],
            'published_at': snippet['publishedAt'],
            'thumbnails': snippet['thumbnails']['default']['url'],
            'country': snippet.get('country', ''),
            'subscriber_count': statistics.get('subscriberCount', 0),
            'total_views': statistics.get('viewCount', 0),
            'topic_categories': topic_details.get('topicCategories', []),
            'is_linked': status.get('isLinked', False),  # verification status
        }
    else:
        return None

# Function to get channel's videos
def get_channel_videos(channel_id, order='date', max_results=50):
    videos = []
    search_response = youtube.search().list(
        channelId=channel_id,
        part='id,snippet',
        order=order,
        maxResults=max_results
    ).execute()

    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            video_id = search_result['id']['videoId']
            video_details = get_video_details(video_id)
            if video_details:
                videos.append(video_details)
    return videos

# Function to get a list of channel IDs based on channel names
def get_channel_id_by_name(channel_name):
    search_response = youtube.search().list(
        q=channel_name,
        part='id',
        type='channel'
    ).execute()
    
    return search_response['items'][0]['id']['channelId']

# Main function to collect data from multiple channels
def collect_data_from_channels(channel_names, order='date', max_results=50):
    all_videos = []
    all_channels = []
    channel_ids = set()  # To keep track of processed channels

    for channel_name in channel_names:
        try:
            channel_id = get_channel_id_by_name(channel_name)
            if channel_id not in channel_ids:
                channel_details = get_channel_details(channel_id)
                if channel_details:
                    all_channels.append(channel_details)
                    channel_ids.add(channel_id)

            videos = get_channel_videos(channel_id, order, max_results)
            all_videos.extend(videos)
        except Exception as e:
            print(f"Error processing channel {channel_name}: {e}")
    
    return all_videos, all_channels

# List of channel names (replace with your target channels)
channel_names = ['Better Ideas', 'Struthless', 'Cole Hastings']

# Collect data
video_data, channel_data = collect_data_from_channels(channel_names, order='date', max_results=20)

# Convert to DataFrame
df_videos = pd.DataFrame(video_data)
df_channels = pd.DataFrame(channel_data)

# Save to CSV
df_videos.to_csv('youtube_videos.csv', index=False)
df_channels.to_csv('youtube_channels.csv', index=False)

print("Data collection complete. Saved to youtube_videos.csv")
