from traktor_nowplaying import Listener
from ffmpy import FFmpeg
from .config import config
import pathlib
import multiprocessing
import requests
import os

ICECAST_URL = f"http://{config.icecast.server}:{config.icecast.port}"
ICECAST_BASE = f'icecast://{config.icecast.source.user}:{config.icecast.source.password}@{config.icecast.server}:{config.icecast.port}'
TRAKTOR_RECORDING_GLOB = f"*.{config.traktor['recordings-extension']}"

# potential problem with ffmpeg - if the process gets interrupted
# because say the recording is switched over, then even if we
# restart, I think clients need to refresh. One way to avoid this
# would be to manually PUT the data to icecast, which in _theory_
# isn't that hard.
icecast_outputs = {
    f'{ICECAST_BASE}/radio.ogg': [
        '-acodec', 'libvorbis',
        '-b:a', '256k',
        '-ar', '44100',
        '-ac', '2',
        '-content_type', 'application/ogg',
        '-ice_name', config.stream.title,
        '-ice_description', config.stream.description,
        '-ice_genre', config.stream.genre,
        '-ice_url', config.stream.url,
        '-f', 'ogg',
    ],
    f'{ICECAST_BASE}/radio.mp3': [
        '-acodec', 'libmp3lame',
        '-b:a', '320k',
        '-ar', '44100',
        '-ac', '2',
        '-content_type', 'application/mp3',
        '-ice_name', config.stream.title,
        '-ice_description', config.stream.description,
        '-ice_genre', config.stream.genre,
        '-ice_url', config.stream.url,
        '-f', 'mp3',
    ],
    # f'{ICECAST_BASE}/radio.flac': [
    #     '-acodec', 'flac',
    #     '-sample_fmt', 's16',
    #     '-ar', '44100',
    #     '-ac', '2',
    #     '-content_type', 'application/flac'
    #     '-ice_name', STREAM_TITLE,
    #     '-ice_description', STREAM_DESCRIPTION,
    #     '-f', 'flac',
    # ],
}

icecast_mounts = [m.replace(ICECAST_BASE, '') for m in icecast_outputs.keys()]

sesh = requests.Session()
sesh.auth = (config.icecast.admin.user, config.icecast.admin.password)

def update_icemeta(data):
    info = dict(data)
    track_string = f'{info.get("artist", "")} - {info.get("title", "")}'
    if len(track_string) < 4:
        return
    for mount in icecast_mounts:
        sesh.get(f'{ICECAST_URL}/admin/metadata', params={
            'mode': 'updinfo',
            'mount': mount,
            'song': track_string
        })

def get_traktor_meta():
    listener = Listener(port=config.nowplaying.port, quiet=True, custom_callback=update_icemeta)
    listener.start()

def get_newest_recording():
    recordings = config.traktor['recordings-path'].glob(TRAKTOR_RECORDING_GLOB)
    return max(recordings, key=os.path.getctime, default=None)

def stream():
    newest_recording = get_newest_recording()

    ff = FFmpeg(
        executable='./ffmpeg',
        inputs={str(newest_recording): ['-re', '-sseof', '-1']},
        outputs=icecast_outputs
    )

    try:
        # using a process instead of a thread here because I want
        # to be able to terminate it without any extra code.
        process = multiprocessing.Process(target=get_traktor_meta)
        process.start()

        ff.run()
        # update metadata in a separate thread
    except:
        if process:
            process.terminate()
