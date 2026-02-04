from mutagen.mp3 import MP3
from time import sleep

import os

def play_sound_file_locally(output_file_name, should_mute_vtuber_during_playback = False):
  if should_mute_vtuber_during_playback:
    # sleep for the duration of the file, to avoid the vtuber speaking over this TTS
    mutagen_audio = MP3(output_file_name)
    mutagen_duration = mutagen_audio.info.length
    sleep(mutagen_duration)

  os.startfile(os.path.abspath(output_file_name))
