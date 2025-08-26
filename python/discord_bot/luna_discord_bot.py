# NOTE: RUN THIS PROGRAM USING ABSOLUTE PATHS: python -m discord_bot.luna_discord_bot

from InstanceContainer import InstanceContainer
import discord
import os
import random
import asyncio
import datetime
from dotenv import load_dotenv; load_dotenv()
from log_error import log_error
from llm_openai import gen_llm_response
from find_banned_words import find_banned_words
from discord_bot.utils import gen_timeout_timedelta, get_current_minute, get_current_hour

InstanceContainer.llm_short_term_memory.set_context('Right now, you are hanging out in your discord server.')

# state
current_minute = get_current_minute()
current_hour = get_current_hour()
messages_per_minute_counter = 0
messages_per_hour_counter = 0
is_luna_busy = False
vc = None
client = discord.Client(intents=discord.Intents.all())

# constants
MAX_MESSAGES_PER_MINUTE = 10
MAX_MESSAGES_PER_HOUR = 50
MAX_MESSAGES_PER_SESSION = 100
GUILD_ID = 1139810741642330152
GENERAL_CHANNEL_ID = 1139810743471063052
TRANSCRIPTION_CHANNEL_ID = 1157165876064296980
LUNA_AND_SMOKIE_ONLY_CHANNEL_ID = 1141547964960079984
VOICE_TEXT_CHANNEL_ID = 1141966787404124221
LIVE_ANNOUNCEMENTS_CHANNEL_ID = 1139812500032987166
SELF_PROMO_CHANNEL_ID = 1142501340459839488
SCHEDULE_CHANNEL_ID = 1168991964201484338
POLL_CHANNEL_ID = 1263352851133104253


@client.event
async def delayed_message(channel, message):
  await asyncio.sleep(12 * 60 * 60)  # 12 hours in seconds
  await channel.send(message)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_member_join(member):
  # (_, _, edited) = gen_llm_response(f'{member.display_name} just joined the discord server! Welcome them with a spicy welcome message!')
  channel = client.get_channel(GENERAL_CHANNEL_ID)
  async with channel.typing():
    await asyncio.sleep(random.uniform(2, 4))
  # await channel.send(f'{member.mention} :erm:')
  # await channel.send('<:erm:1181683256438046741>')
  await channel.send('<:lunaErm:1256725746668404827>')

@client.event
async def on_message(message):
  global current_minute
  global current_hour
  global messages_per_minute_counter
  global messages_per_hour_counter
  global is_luna_busy
  global vc

  # don't respond to itself, or if currently working through a response.
  if message.author == client.user or is_luna_busy:
    return

  is_luna_busy = True

  if message.guild.id == GUILD_ID:
    # moderation flow: runs on every message in the discord server
    if len(find_banned_words(str(message.clean_content))):
      banned_words_in_message = find_banned_words(str(message.clean_content))
      prompt = f'Announce that you\'ve just timed out {str(message.author.display_name)} for 30 seconds for saying a banned word: {banned_words_in_message[0]} (mention the banned word in your response)'
      try:
        timeout_timedelta = gen_timeout_timedelta('30s')
        await message.author.timeout(timeout_timedelta, reason='timed out by luna')
        (_, _, edited) = gen_llm_response(prompt)
        await message.reply(edited)
      except Exception as e:
        log_error(e, '(discord bot)')
        await message.reply('Someone tell @smokie_777 there is a problem with my AI.')
    # main flow: only respond to messages if BOTH message is in the server AND @Luna was mentioned
    elif int(os.environ['LUNA_DISCORD_BOT_ID']) in [m.id for m in message.mentions]:
      # print('message.activity: ', message.activity)
      # print('message.application: ', message.application)
      # print('message.application_id: ', message.application_id)
      # print('message.attachments: ', message.attachments)
      # print('message.author: ', message.author)
      # print('message.channel: ', message.channel)
      # print('message.channel_mentions: ', message.channel_mentions)
      # print('message.clean_content: ', message.clean_content)
      # print('message.components: ', message.components)
      # print('message.content: ', message.content)
      # print('message.created_at: ', message.created_at)
      # print('message.edited_at: ', message.edited_at)
      # print('message.embeds: ', message.embeds)
      # print('message.flags: ', message.flags)
      # print('message.guild: ', message.guild)
      # print('message.id: ', message.id)
      # print('message.interaction: ', message.interaction) 
      # print('message.jump_url: ', message.jump_url)
      # print('message.mention_everyone: ', message.mention_everyone)
      # print('message.mentions: ', message.mentions)
      # print('message.nonce: ', message.nonce)
      # print('message.pinned: ', message.pinned)
      # print('message.position: ', message.position)
      # print('message.raw_channel_mentions: ', message.raw_channel_mentions)
      # print('message.raw_mentions: ', message.raw_mentions)
      # print('message.raw_role_mentions: ', message.raw_role_mentions)
      # print('message.reactions: ', message.reactions)
      # print('message.reference: ', message.reference)
      # print('message.role_mentions: ', message.role_mentions)
      # print('message.role_subscription: ', message.role_subscription)
      # print('message.stickers: ', message.stickers)
      # print('message.system_content: ', message.system_content)
      # print('message.tts: ', message.tts)
      # print('message.type: ', message.type)
      # print('message.webhook_id: ', message.webhook_id)

      # rate limiting logic (per minute and hour)
      updated_current_minute = get_current_minute()
      updated_current_hour = get_current_hour()
      
      if (current_minute != updated_current_minute):
        messages_per_minute_counter = 0
        current_minute = updated_current_minute
      if (current_hour != updated_current_hour):
        messages_per_hour_counter = 0
        current_hour = updated_current_hour

      if (messages_per_minute_counter < MAX_MESSAGES_PER_MINUTE and messages_per_hour_counter < MAX_MESSAGES_PER_HOUR):
        try:
          prompt = ''
          # send specific message to target channel functionality
          if (str(message.author) == 'smokie_777' and '@Luna !send ' in str(message.clean_content)):
            args = message.clean_content.replace('@Luna !send ', '').split(' ')
            channel_name = args[0]
            message_to_send = ' '.join(args[1:])
            if channel_name and message_to_send:
              channel = discord.utils.get(message.guild.text_channels, name=channel_name)
              async with channel.typing():
                await asyncio.sleep(random.uniform(2, 4))
              await channel.send(message_to_send)
          # luna bot create poll functionality
          elif (str(message.author) == 'smokie_777' and '@Luna !poll' in str(message.clean_content)):
            (_, _, edited) = gen_llm_response('Generate a wild and crazy poll for the discord server, about any topic you choose! Format should be QUESTION: your question here ANSWERS: answer1,answer2,answer3. (The answers should be a comma-separated list, and you must include QUESTION: and ANSWERS: sections) Example: QUESTION: What should Smokie stream next? ANSWERS: her eating,her sleeping,her doing literally nothing,her throwing rocks at seagulls')
            print('!poll attempting to create poll from input: ', edited)
            try:
              _, qa_part = edited.split('QUESTION:', 1)
              question_part, answers_part = qa_part.split('ANSWERS:', 1)
              question = question_part.strip()
              answers = [ans.strip() for ans in answers_part.split(',')]
              p = discord.Poll(question=question, duration=datetime.timedelta(hours=24))
              for i in answers:
                p.add_answer(text=i)
              channel = client.get_channel(LUNA_AND_SMOKIE_ONLY_CHANNEL_ID if '!polltest' in str(message.clean_content) else POLL_CHANNEL_ID)
              await channel.send(poll=p)
            except:
              print('!poll failed to create poll from input: ', edited)
          # live-announcements stream alert notif functionality
          elif (str(message.author) == 'smokie_777' and '@Luna !live' in str(message.clean_content)):
            (_, _, edited) = gen_llm_response('Smokie: Luna, we\'re about to go live on Twitch! Can you come up a spicy discord alert message to let everyone know we\'re about to go live?')
            message_to_send = f'@here {edited} https://www.twitch.tv/smokie_777'
            channel = client.get_channel(LIVE_ANNOUNCEMENTS_CHANNEL_ID)
            await channel.send(message_to_send)
          # send message after delay functionality
          elif (str(message.author) == 'smokie_777' and '@Luna !beep' in str(message.clean_content)):
            message_to_send = f'Beep! This is a test mesage sent by Luna after a 12 hour delay.'
            channel = client.get_channel(SCHEDULE_CHANNEL_ID)
            asyncio.create_task(delayed_message(channel, message_to_send))
          # youtube video promo functionality (experimental)
          elif (str(message.author) == 'smokie_777' and '@Luna !video ' in str(message.clean_content)):
            # example usage: @Luna !video | title | url
            s = str(message.clean_content)
            title = s.split('|')[1].strip()
            url = s.split('|')[2].strip()
            (_, _, edited) = gen_llm_response(f'Smokie: Luna, you just published a new video on your luna_777 youtube channel! Can you promote it to your discord server? The title is: {title}')
            message_to_send = f'{edited} {url}'
            channel = client.get_channel(SELF_PROMO_CHANNEL_ID)
            await channel.send(message_to_send)
          # ban functionality
          elif (str(message.author) == 'smokie_777' and '@Luna !ban ' in str(message.clean_content)):
            await message.mentions[1].ban()
            (_, _, edited) = gen_llm_response('Smokie: luna, announce that you\'ve just banned ' + message.mentions[1].display_name + ' out of your discord server. feel free to include some spice :)')
            async with message.channel.typing():
              await asyncio.sleep(random.uniform(2, 4))
            await message.reply(edited)
          # timeout functionality
          elif (str(message.author) == 'smokie_777' and '@Luna !timeout ' in str(message.clean_content)):
            # example usage: @Luna !timeout @Username | 4m 2s | for this reason
            s = str(message.clean_content)
            time_string = s.split('|')[1].strip()
            reason = s.split('|')[2].strip() if s.count('|') == 2 else None
            try:
              timeout_timedelta = gen_timeout_timedelta(time_string)
              await message.mentions[1].timeout(timeout_timedelta, reason=reason)
              reason_string = f'Reason: {reason}. ' if reason else ''
              (_, _, edited) = gen_llm_response(f'Smokie: luna, announce that you\'ve just timed out {message.mentions[1].display_name} for {time_string}. {reason_string}Feel free to include some spice :)')
              async with message.channel.typing():
                await asyncio.sleep(random.uniform(2, 4))
              await message.reply(edited)
            except Exception as e:
              log_error(e, '(discord bot)')
              await message.reply('Someone tell @smokie_777 there is a problem with my AI.')
          # remote shut down functionality
          elif (str(message.author) == 'smokie_777' and '@Luna !sleep' in str(message.clean_content)):
            await client.close()
          # bot join voice channel
          elif (str(message.author) == 'smokie_777' and '@Luna !vc' in str(message.clean_content)):
            channel = message.author.voice.channel
            # channel = message.guild.get_channel(1139810743471063053)
            if vc is not None:
              await vc.disconnect()
              vc = None
            else:
              vc = await channel.connect()
          elif (str(message.author) == 'smokie_777' and '@Luna !reply ' in str(message.clean_content)):
            message_id = str(message.clean_content).replace('@Luna !reply ', '')
            target_messsage = await message.channel.fetch_message(message_id)
            prompt = str(target_messsage.author.display_name) + ': ' + str(target_messsage.clean_content)
            (_, _, edited) = gen_llm_response(prompt)
            async with target_messsage.channel.typing():
              await asyncio.sleep(random.uniform(2, 4))
            await target_messsage.reply(edited)
          # general message response function
          else:
            if str(message.author) != 'smokie_777':
              messages_per_minute_counter += 1
              messages_per_hour_counter += 1
            prompt = str(message.author.display_name) + ': ' + str(message.clean_content)
            (_, _, edited) = gen_llm_response(prompt)

            if vc is not None and (message.channel.id == VOICE_TEXT_CHANNEL_ID or message.channel.id == LUNA_AND_SMOKIE_ONLY_CHANNEL_ID):
              await message.reply(edited)
              (filename, _) = InstanceContainer.azure.gen_audio_file_and_subtitles(edited, None, True)
              try:
                # todo: in collab mode, do a post request to the flask server
                vc.play(discord.FFmpegPCMAudio(filename))
              except:
                print('skipping')
            else:
              async with message.channel.typing():
                await asyncio.sleep(random.uniform(2, 4))
              await message.reply(edited)

        except Exception as e:
          log_error(e, '(discord bot)')
          await message.reply('Someone tell @smokie_777 there is a problem with my AI.')
      else:
        await message.reply('⌛')
    # luna bot respond to transcription
    elif (
      message.channel.id == TRANSCRIPTION_CHANNEL_ID
      and str(message.author) == 'SeaVoice#8208'
      and vc is not None
      and len(str(message.clean_content).split(':  ')[-1].split()) > 1
      and str(message.clean_content).split(':  ')[0] != '**Luna**'
    ):
      prompt = str(message.clean_content.replace('*', ''))
      (_, _, edited) = gen_llm_response(prompt)
      (filename, _) = InstanceContainer.azure.gen_audio_file_and_subtitles(edited, None, True)
      try:
        vc.play(discord.FFmpegPCMAudio(filename))
      except:
        print('skipping')

  is_luna_busy = False


if __name__ == '__main__':
  client.run(os.environ['LUNA_DISCORD_BOT_TOKEN'])
