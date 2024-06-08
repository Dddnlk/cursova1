from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

load_dotenv()

client_id = "9a835c1426bd48728073298af319eff2"
client_secret = "aca9a5b8ccf74212b237827bac357242"
bot = Bot(token='6912321348:AAGnWl_2zRkyQCon07VKq3UPwTlZXSklwb8')
dp = Dispatcher()
print(client_id, client_secret)

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"
    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    if len(json_result) == 0:
        print("No artist with this name exists...")
        return None
    return json_result[0]

def search_for_track(token, track_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={track_name}&type=track&limit=1"
    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["tracks"]["items"]
    if len(json_result) == 0:
        print("No tracks with this name exists...")
        return None
    return json_result[0]

def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def get_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    artist_info = {
        "popularity": json_result["popularity"],
        "uri": json_result["uri"],
        "images": json_result["images"]
    }
    return artist_info

def get_genres(token):
    url = "https://api.spotify.com/v1/recommendations/available-genre-seeds"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result["genres"]

def get_track(token, track_id):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    track_info = {
        "name": json_result["name"],
        "album": json_result["album"]["name"],
        "release_date": json_result["album"]["release_date"],
        "artists": [artist["name"] for artist in json_result["artists"]],
        "images": json_result["album"]["images"]
    }
    return track_info

def create_playlist(token, user_id, playlist_name, public=True):
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers = get_auth_header(token)
    data = {
        "name": playlist_name,
        "public": public
    }
    response = post(url, headers=headers, json=data)

    return response.json().get("id")

def get_playlists(token, user_id):
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет!')
    await message.reply('Как дела?')

@dp.message(Command('artisttop'))
async def artist_top(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Пожалуйста, укажите имя артиста после команды /artisttop")
        return

    artist_name = args[1]
    token = get_token()
    result = search_for_artist(token, artist_name)

    if result is None:
        await message.reply(f"Артист с именем '{artist_name}' не найден.")
        return

    artist_id = result["id"]
    songs = get_songs_by_artist(token, artist_id)

    if not songs:
        await message.reply(f"Не удалось получить топ треки для артиста '{artist_name}'.")
        return

    response = f"Топ треки для '{artist_name}':\n"
    for idx, song in enumerate(songs):
        response += f"{idx + 1}. {song['name']}\n"

    await message.reply(response)

@dp.message(Command('artist'))
async def artist_info(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Пожалуйста, укажите имя артиста после команды /artist")
        return

    artist_name = args[1]
    token = get_token()
    result = search_for_artist(token, artist_name)

    if result is None:
        await message.reply(f"Артист с именем '{artist_name}' не найден.")
        return

    artist_id = result["id"]
    artist_info = get_artist(token, artist_id)

    response = f"Информация об артисте '{artist_name}':\n"
    response += f"Популярность: {artist_info['popularity']}\n"
    response += f"Ссылка: {artist_info['uri']}\n"
    response += "Изображения:\n"
    for img in artist_info["images"]:
        response += f"{img['url']} (размер: {img['width']}x{img['height']})\n"

    await message.reply(response)

@dp.message(Command('available_genres'))
async def available_genres(message: Message):
    token = get_token()
    genres = get_genres(token)

    response = "Доступные жанры:\n"
    for idx, genre in enumerate(genres):
        response += f"{idx + 1}. {genre}\n"

    await message.reply(response)

@dp.message(Command('track'))
async def track_info(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Пожалуйста, укажите название трека после команды /track")
        return

    track_name = args[1]
    token = get_token()
    result = search_for_track(token, track_name)

    if result is None:
        await message.reply(f"Трек с названием '{track_name}' не найден.")
        return

    track_id = result["id"]
    track_info = get_track(token, track_id)

    response = f"Информация о треке '{track_name}':\n"
    response += f"Название альбома: {track_info['album']}\n"
    response += f"Дата выхода: {track_info['release_date']}\n"
    response += "Исполнители:\n"
    for artist in track_info["artists"]:
        response += f"- {artist}\n"
    response += "Изображения:\n"
    for img in track_info["images"]:
        response += f"{img['url']} (размер: {img['width']}x{img['height']})\n"

    await message.reply(response)

@dp.message(Command('create_playlist'))
async def create_playlist_command(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Пожалуйста, укажите название плейлиста после команды /create_playlist")
        return

    playlist_name = args[1]
    token = get_token()
    user_id = "31aduwgjxffwegrrupuozy3by3ty"
    playlist_id = create_playlist(token, user_id, playlist_name)

    if playlist_id:
        await message.reply(f"ID плейлиста: {playlist_id}")
    else:
        await message.reply(
            f"Плейлист '{playlist_name}'успешно создан. ")

@dp.message(Command('playlists'))
async def playlists_info(message: Message):
    token = get_token()
    user_id = "31aduwgjxffwegrrupuozy3by3ty"
    playlists = get_playlists(token, user_id)

    total_playlists = playlists['total']
    items = playlists['items']

    response = f"Всего плейлистов: {total_playlists}\n\n"
    response += "Плейлисты:\n"
    for idx, item in enumerate(items):
        response += f"{idx + 1}. {item['name']}\n"

    await message.reply(response)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
