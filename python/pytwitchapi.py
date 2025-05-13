from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator, UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatCommand
from twitchAPI.helper import first
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.object.eventsub import ChannelSubscribeEvent, ChannelSubscriptionGiftData, ChannelSubscriptionMessageEvent, ChannelCheerEvent, ChannelPointsCustomRewardRedemptionAddEvent
import asyncio
from uuid import UUID
import os
from enums import AZURE_SPEAKING_STYLE, VTS_EXPRESSIONS, PRIORITY_QUEUE_PRIORITIES, TWITCH_EVENTS, TWITCH_EVENT_TYPE
from vts_set_expression import vts_set_expression
from dotenv import load_dotenv; load_dotenv()
from utils import does_one_word_start_with_at
from pytwitchapi_helpers import is_valid_scrabble_tile, send_ban_user_via_username_event_to_priority_queue, is_twitch_message_bot_spam
import json
from remind_me import convert_time_hms_string_to_ms
from datetime import datetime, timedelta
from db import db_event_insert_one
from constants import booba_emotes
from InstanceContainer import InstanceContainer
from State import State
import random
from find_banned_words import find_banned_words

APP_ID = os.environ['TWITCH_APP_ID']
APP_SECRET = os.environ['TWITCH_APP_SECRET']
# APP_ID = os.environ['TWITCH_APP_ID_LUNA']
# APP_SECRET = os.environ['TWITCH_APP_SECRET_LUNA']
USER_SCOPE = [
  # twitch
  AuthScope.MODERATOR_MANAGE_BANNED_USERS,
  # chat
  AuthScope.CHAT_READ,
  AuthScope.CHAT_EDIT,
]
EVENTSUB_SCOPES = [
  AuthScope.CHANNEL_READ_REDEMPTIONS,
  AuthScope.BITS_READ,
  AuthScope.CHANNEL_READ_SUBSCRIPTIONS
]
TARGET_CHANNEL = 'smokie_777'

WHISPER_PREFIX_TEXT = '[respond to this message as if you were whispering. give a longer response than usual.]'
RANT_PREFIX_TEXT = '[please go on a really long and angry rant about the following topic.]'

### START CHAT API ###

async def chat_on_ready(ready_event: EventData):
  print('[PYTWITCHAPI] chat module connected')
  await ready_event.chat.join_room(TARGET_CHANNEL)

async def chat_on_message(msg: ChatMessage):
  # print(msg.__dict__)

  if (
    msg._parsed['tags']['first-msg'] == '1'
    and is_twitch_message_bot_spam(msg.text)
  ):
    print(f'[PYTWITCHAPI] {msg.user.name} was detected as a spam bot, is about to be banned! Their message: {msg.text}')
    send_ban_user_via_username_event_to_priority_queue(
      msg.user.name,
      None,
      'being a spam bot'
    )
    return
  
  banned_words_in_message = find_banned_words(msg.text)
  if len(banned_words_in_message):
    print(f'[PYTWITCHAPI] {msg.user.name} said a banned word, is about to be timed out! Their message: {msg.text}')
    send_ban_user_via_username_event_to_priority_queue(
      msg.user.name,
      10,
      f'saying a banned word in chat: {banned_words_in_message[0]} (mention the banned word in your response!)'
    )
    return

  # bits are handled in eventsub, so we ignore bit messages here
  if (
    msg.bits
    or WHISPER_PREFIX_TEXT in msg.text # channel point redemption will send a normal message too
    or RANT_PREFIX_TEXT in msg.text # channel point redemption will send a normal message too
  ):
    return

  InstanceContainer.ws.send(json.dumps({
    'twitch_event': {
      'event': TWITCH_EVENTS['MESSAGE'],
      'username': msg.user.name,
      'value': msg.text
    }
  }))


  prompt = f'{msg.user.name}: {msg.text}'
  is_at_luna = '@luna' in msg.text.lower() or '@hellfire' in msg.text.lower()

  if (
    State.is_twitch_chat_react_on
    and msg.text[0] != '!'
    and msg.user.name != 'Streamlabs'
    and (
      (State.is_quiet_mode_on and is_at_luna)
      or (not State.is_quiet_mode_on and (
        is_at_luna or not does_one_word_start_with_at(msg.text.lower().split(' '))
      ))
    )
  ):
    if '@luna !remindme ' in msg.text.lower():
      args = msg.text.lower().replace('@luna !remindme ', '').split(' ')
      reminder_action = " ".join(args[1:])
      acknowledgement_prompt = (
        f'say, "I will remind {msg.user.name} to "{reminder_action}" in {args[0]}."'
      )
      reminder_prompt = f'say to {msg.user.name} that this is their reminder to "{reminder_action}".'
      State.remind_me_prompts_and_datetime_queue.append((
        reminder_prompt,
        datetime.now() + timedelta(milliseconds=convert_time_hms_string_to_ms(args[0]))
      ))
      with InstanceContainer.app.app_context():
        db_event_insert_one(
          type=TWITCH_EVENT_TYPE['CHAT_COMMAND'],
          event='!remindme',
          body=reminder_action
        )
      InstanceContainer.priority_queue.enqueue(
        prompt=acknowledgement_prompt,
        priority=PRIORITY_QUEUE_PRIORITIES['PRIORITY_REMIND_ME']
      )
    else:
      is_speaking_fast = random.random() > 0.75
      InstanceContainer.priority_queue.enqueue(
        prompt=prompt,
        priority=PRIORITY_QUEUE_PRIORITIES['PRIORITY_TWITCH_CHAT_QUEUE'],
        is_speaking_fast=is_speaking_fast
      )

async def chat_on_command_discord(cmd: ChatCommand):
  await cmd.reply('https://discord.gg/cxTHwepMTb')
  with InstanceContainer.app.app_context():
    db_event_insert_one(type=TWITCH_EVENT_TYPE['CHAT_COMMAND'], event='!discord')

async def chat_on_command_profile(cmd: ChatCommand):
  await cmd.reply('https://www.pathofexile.com/account/view-profile/smokie_777/characters')
  with InstanceContainer.app.app_context():
    db_event_insert_one(type=TWITCH_EVENT_TYPE['CHAT_COMMAND'], event='!profile')

async def chat_on_command_filter(cmd: ChatCommand):
  await cmd.reply('https://www.filterblade.xyz/Profile?name=smokie_777&platform=pc')
  # await cmd.reply('https://pastebin.com/XRCCuqhK')
  with InstanceContainer.app.app_context():
    db_event_insert_one(type=TWITCH_EVENT_TYPE['CHAT_COMMAND'], event='!filter')

async def chat_on_command_video(cmd: ChatCommand):
  await cmd.reply('https://www.youtube.com/@smokie_777')
  with InstanceContainer.app.app_context():
    db_event_insert_one(type=TWITCH_EVENT_TYPE['CHAT_COMMAND'], event='!video')

async def chat_on_command_build(cmd: ChatCommand):
  await cmd.reply('https://pobb.in/mNxCKLr5UVYE')
  with InstanceContainer.app.app_context():
    db_event_insert_one(type=TWITCH_EVENT_TYPE['CHAT_COMMAND'], event='!build')

async def chat_on_command_rip(cmd: ChatCommand):
  await cmd.reply('https://clips.twitch.tv/SpotlessImportantTigerNotATK-y8BriY_NBlNwA8a5')
  with InstanceContainer.app.app_context():
    db_event_insert_one(type=TWITCH_EVENT_TYPE['CHAT_COMMAND'], event='!rip')

async def chat_on_command_booba(cmd: ChatCommand):
  await cmd.reply(' '.join(booba_emotes))
  with InstanceContainer.app.app_context():
    db_event_insert_one(type=TWITCH_EVENT_TYPE['CHAT_COMMAND'], event='!booba')

async def chat_on_command_join(cmd: ChatCommand):
  if not cmd.user.name in State.raffle_entries_set:
    State.raffle_entries_set.add(cmd.user.name)
    # await cmd.reply(f'successfully joined the giveaway! ({len(State.raffle_entries_set)} people have joined so far.)')
    InstanceContainer.ws.send(json.dumps({
      'type': 'SET_TOAST',
      'payload': f'{cmd.user.name} joined the giveaway! ({len(State.raffle_entries_set)} joined so far)'
    }))
    with InstanceContainer.app.app_context():
      db_event_insert_one(type=TWITCH_EVENT_TYPE['CHAT_COMMAND'], event='!join')

async def chat_on_command_play(cmd: ChatCommand):
  parameters = cmd.parameter.strip().lower().split(maxsplit=2)
  start_tile = parameters[0].strip() if len(parameters) > 0 else ''
  letters = parameters[1].strip() if len(parameters) > 1 else ''
  print('[SCRABBLE]', parameters, start_tile, letters)
  coordinate_str = start_tile[:-1] if start_tile[-1] in ['h', 'v'] else start_tile
  if (
    not letters.replace('_', '').isalpha()
    or not is_valid_scrabble_tile(coordinate_str)
  ):
    return
  InstanceContainer.ws.send(json.dumps({
    'scrabble_chat_command': {
      'type': 'play',
      'username': cmd.user.name,
      'letters': letters.upper(),
      # "start tile" refers to the leftmost/upmost tile of the primary word created.
      'startTileX': ord(coordinate_str[0]) - ord('a'), # already accounts for 0 index
      'startTileY': 14 - (int(coordinate_str[1:]) - 1), # subtract 1 to account for 0 index. invert for UI
      # default direction to 'horizontal'
      'direction': 'vertical' if start_tile[-1] == 'v' else 'horizontal'
    }
  }))

async def chat_on_command_ban(cmd: ChatCommand):
  if cmd.user.name == 'smokie_777':
    args = cmd.text.replace('!ban ', '').split(' ')
    username_to_ban = args[0].strip()
    reason = ''
    if len(args) > 1:
      reason = args[1].strip()
    if username_to_ban:
      send_ban_user_via_username_event_to_priority_queue(username_to_ban, None, reason)

### END CHAT API ###

### START GENERIC PYTWITCHAPI ###

async def terminate_pytwitchapi():
  InstanceContainer.chat.stop()
  await InstanceContainer.twitch.close()

### END GENERIC PYTWITCHAPI ###

### START EVENTSUB API ###

async def eventsub_send_sub_event_to_ws_and_priority_queue(ws_sub_name, ws_message, prompt):
  InstanceContainer.ws.send(json.dumps({
    'twitch_event': {
      'event': TWITCH_EVENTS['SUB'],
      'username': ws_sub_name,
      'value': ws_message
    }
  }))
  InstanceContainer.priority_queue.enqueue(
    prompt=prompt,
    priority=PRIORITY_QUEUE_PRIORITIES['PRIORITY_EVENTSUB_EVENTS_QUEUE']
  )

# handles first time, non-gifted subs
async def eventsub_handle_listen_channel_subscribe(data: ChannelSubscribeEvent):
  event = data.event
  print('[PYTWITCHAPI]', { 'tier': event.tier, 'user_name': event.user_name, 'is_gift': event.is_gift })
  if not event.is_gift: # gift subs are handled separately in eventsub_handle_listen_channel_subscription_gift()
    tier = f'Tier {int(event.tier) // 1000}'
    ws_sub_name = event.user_name
    ws_message = f'{tier} sub'
    prompt = f'{ws_sub_name} just subscribed at {tier}!'
    await eventsub_send_sub_event_to_ws_and_priority_queue(ws_sub_name, ws_message, prompt)

# handles gifted subs
async def eventsub_handle_listen_channel_subscription_gift(data: ChannelSubscriptionGiftData):
  event = data.event
  print('[PYTWITCHAPI]', { 'tier': event.tier, 'user_name': event.user_name, 'is_gift': event.is_gift })
  tier = f'Tier {int(event.tier) // 1000}'
  ws_sub_name = event.user_name or 'An anonymous gifter'
  ws_message = f'{tier} sub'
  prompt = f'{ws_sub_name} just subscribed at {tier}!'
  await eventsub_send_sub_event_to_ws_and_priority_queue(ws_sub_name, ws_message, prompt)

# handles resubs only.
async def eventsub_handle_listen_channel_subscription_message(data: ChannelSubscriptionMessageEvent):
  event = data.event
  print('[PYTWITCHAPI]', { 'tier': event.tier, 'user_name': event.user_name, 'cumulative_months': event.cumulative_months, 'message.text': event.message.text })
  tier = f'Tier {int(event.tier) // 1000}'
  months = f' for {event.cumulative_months} months' if event.cumulative_months else ''
  sub_message = f' Their sub message: {event.message.text}' if event.message.text else ''
  ws_sub_name = event.user_name or 'An anonymous gifter'
  ws_message = f'{tier} sub'
  prompt = f'{ws_sub_name} just resubscribed at {tier}{months}!{sub_message}'
  await eventsub_send_sub_event_to_ws_and_priority_queue(ws_sub_name, ws_message, prompt)

# handles bits.
async def eventsub_handle_listen_channel_cheer(data: ChannelCheerEvent):
  event = data.event
  print('[PYTWITCHAPI]', { 'bits': event.bits, 'user_name': event.user_name, 'message': event.message })
  user_name = event.user_name or 'An anonymous donator'
  bits = event.bits
  message = f' Their message: {event.message}'
  prompt = f'{user_name} just cheered {bits} bits!{message}'
  InstanceContainer.ws.send(json.dumps({
    'twitch_event': {
      'event': TWITCH_EVENTS['BITS'],
      'username': user_name,
      'value': str(bits)
    }
  }))
  InstanceContainer.priority_queue.enqueue(
    prompt=prompt, 
    priority=PRIORITY_QUEUE_PRIORITIES['PRIORITY_EVENTSUB_EVENTS_QUEUE']
  )

async def eventsub_handle_listen_channel_points_custom_reward_redemption_add(data: ChannelPointsCustomRewardRedemptionAddEvent):
  event = data.event
  title = event.reward.title
  display_name = event.user_name
  user_input = event.user_input
  print('[PYTWITCHAPI]', { 'reward.title': title, 'user_name': display_name, 'user_input': user_input })

  if title == 'luna whisper' and State.is_twitch_chat_react_on:
    vts_set_expression(VTS_EXPRESSIONS['FLUSHED'])
    prompt = f'{WHISPER_PREFIX_TEXT} {display_name}: {user_input}'
    with InstanceContainer.app.app_context():
      db_event_insert_one(
        type=TWITCH_EVENT_TYPE['CHANNEL_POINT_REDEMPTION'],
        event='luna whisper',
        body=user_input
      )
    InstanceContainer.priority_queue.enqueue(
      prompt=prompt,
      priority=PRIORITY_QUEUE_PRIORITIES['PRIORITY_EVENTSUB_EVENTS_QUEUE'],
      azure_speaking_style=AZURE_SPEAKING_STYLE['WHISPERING']
    )
  elif title == 'luna rant' and State.is_twitch_chat_react_on:
    vts_set_expression(VTS_EXPRESSIONS['ANGRY'])
    prompt = f'{RANT_PREFIX_TEXT} {user_input}!'
    with InstanceContainer.app.app_context():
      db_event_insert_one(
        type=TWITCH_EVENT_TYPE['CHANNEL_POINT_REDEMPTION'],
        event='luna rant',
        body=user_input
      )
    InstanceContainer.priority_queue.enqueue(
      prompt=prompt,
      priority=PRIORITY_QUEUE_PRIORITIES['PRIORITY_EVENTSUB_EVENTS_QUEUE']
    )
  elif title == 'Luna brown hair':
    with InstanceContainer.app.app_context():
      db_event_insert_one(
        type=TWITCH_EVENT_TYPE['CHANNEL_POINT_REDEMPTION'],
        event='Luna brown hair'
      )
    vts_set_expression(VTS_EXPRESSIONS['BROWN_HAIR'])
  elif title == 'smokie tts' and not State.is_singing:
    with InstanceContainer.app.app_context():
      db_event_insert_one(
        type=TWITCH_EVENT_TYPE['CHANNEL_POINT_REDEMPTION'],
        event='smokie tts',
        body=user_input
      )
    InstanceContainer.priority_queue.enqueue(
      prompt=user_input,
      priority=PRIORITY_QUEUE_PRIORITIES['PRIORITY_EVENTSUB_EVENTS_QUEUE'],
      is_eleven_labs=True
    )
  elif title == 'unlock 7tv emote':
    prompt = f'{display_name} just requested adding the {user_input} 7tv emote!'
    with InstanceContainer.app.app_context():
      db_event_insert_one(
        type=TWITCH_EVENT_TYPE['CHANNEL_POINT_REDEMPTION'],
        event='unlock 7tv emote',
        body=user_input
      )
    InstanceContainer.priority_queue.enqueue(
      prompt=prompt,
      priority=PRIORITY_QUEUE_PRIORITIES['PRIORITY_EVENTSUB_EVENTS_QUEUE']
    )
  elif title == 'luna wheel' and user_input.count(',') > 0:
    State.luna_wheel_queue.append(user_input)
    InstanceContainer.ws.send(json.dumps({
      'type': 'LUNA_WHEEL',
      'payload': user_input
    }))

### END EVENTSUB API ###

async def run_pytwitchapi():
  # chat api
  InstanceContainer.twitch = await Twitch(APP_ID, APP_SECRET)
  auth = UserAuthenticator(InstanceContainer.twitch, USER_SCOPE, force_verify=False)
  token, refresh_token = await auth.authenticate()
  await InstanceContainer.twitch.set_user_authentication(token, USER_SCOPE, refresh_token)

  InstanceContainer.chat = await Chat(InstanceContainer.twitch)
  InstanceContainer.chat.register_event(ChatEvent.READY, chat_on_ready)
  InstanceContainer.chat.register_event(ChatEvent.MESSAGE, chat_on_message)
  InstanceContainer.chat.register_command('discord', chat_on_command_discord)
  InstanceContainer.chat.register_command('profile', chat_on_command_profile)
  InstanceContainer.chat.register_command('filter', chat_on_command_filter)
  InstanceContainer.chat.register_command('video', chat_on_command_video)
  InstanceContainer.chat.register_command('play', chat_on_command_play)
  InstanceContainer.chat.register_command('ban', chat_on_command_ban)
  InstanceContainer.chat.register_command('rip', chat_on_command_rip)
  InstanceContainer.chat.register_command('build', chat_on_command_build)
  InstanceContainer.chat.register_command('pob', chat_on_command_build)
  InstanceContainer.chat.register_command('booba', chat_on_command_booba)
  # InstanceContainer.chat.register_command('join', chat_on_command_join)

  InstanceContainer.chat.start()
  
  # eventsub api
  eventsub_helper = UserAuthenticationStorageHelper(InstanceContainer.twitch, EVENTSUB_SCOPES)
  await eventsub_helper.bind()
  eventsub_user = await first(InstanceContainer.twitch.get_users())
  InstanceContainer.eventsub = EventSubWebsocket(InstanceContainer.twitch)
  InstanceContainer.eventsub.start()  

  await InstanceContainer.eventsub.listen_channel_subscribe(eventsub_user.id, eventsub_handle_listen_channel_subscribe)
  await InstanceContainer.eventsub.listen_channel_subscription_gift(eventsub_user.id, eventsub_handle_listen_channel_subscription_gift)
  await InstanceContainer.eventsub.listen_channel_subscription_message(eventsub_user.id, eventsub_handle_listen_channel_subscription_message)
  await InstanceContainer.eventsub.listen_channel_cheer(eventsub_user.id, eventsub_handle_listen_channel_cheer)
  await InstanceContainer.eventsub.listen_channel_points_custom_reward_redemption_add(eventsub_user.id, eventsub_handle_listen_channel_points_custom_reward_redemption_add)

  user = await first(InstanceContainer.twitch.get_users(logins='smokie_777'))
  # print the ID of your user or do whatever else you want with it
  print('[PYTWITCHAPI]', user.id)
