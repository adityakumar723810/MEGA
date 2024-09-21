from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import os
import uuid
import time

# Maximum file size for Telegram upload (2GB in bytes)
TELEGRAM_MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024

# Function to download video with retry mechanism and progress tracking
def download_video(video_url, filename, retries=3, timeout=120):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(video_url, stream=True, timeout=timeout)
            if response.status_code == 200:
                total_length = response.headers.get('content-length')
                if total_length is None:  # No content length header
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                else:
                    total_length = int(total_length)
                    dl = 0
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=10240):  # 10KB chunk size
                            dl += len(chunk)
                            f.write(chunk)
                            # Optional: Send progress update here
                            done = int(50 * dl / total_length)
                            print(f"Progress: [{'#' * done}{'.' * (50 - done)}] {done * 2}%")
                return filename
            else:
                print(f"Failed to download video, status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error downloading video: {e}")
            attempt += 1
            time.sleep(2)  # Delay between retries
    return None

# Function to get download links
def get_download_links(video_url):
    api_endpoint = f'https://ashlynn.serv00.net/Ashlynnterabox.php/?url={video_url}'
    
    try:
        response = requests.get(api_endpoint)
        if response.status_code == 200:
            json_response = response.json()
            if 'response' in json_response:
                fast_download_link = json_response['response'][0]['resolutions']['Fast Download']
                return fast_download_link
    except requests.RequestException as e:
        print(f"Error getting download links: {e}")
    return None

# Command to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Welcome to TeraBox Downloader Bot! Send me the URL of the file you want to download.')

# Function to handle messages and check file size
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    video_url = update.message.text
    fast_download_link = get_download_links(video_url)
    
    if fast_download_link:
        filename = f'video_{uuid.uuid4()}.mp4'  # Unique filename
        await update.message.reply_text("Please wait .... downloading started!")
        downloaded_file = download_video(fast_download_link, filename)
        
        if downloaded_file:
            file_size = os.path.getsize(downloaded_file)
            
            if file_size > TELEGRAM_MAX_FILE_SIZE:
                await update.message.reply_text(f"The video is too large to upload on Telegram (Size: {file_size / (1024 * 1024)} MB).")
                os.remove(downloaded_file)  # Clean up large file
            else:
                await update.message.reply_video(video=open(downloaded_file, 'rb'))
                os.remove(downloaded_file)  # Clean up the downloaded file
        else:
            await update.message.reply_text("Failed to download the video.")
    else:
        await update.message.reply_text("No valid link found.")

def main():
    app = ApplicationBuilder().token("8128737803:AAG4mXx7mvdvZXESouv8DtIrQYmxZTpHIto).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()