from State import State
from InstanceContainer import InstanceContainer
import os
import openai
from dotenv import load_dotenv; load_dotenv()

openai.api_key = os.environ['OPENAI_KEY']

def gen_conversational_llm_response(prompt):
  if not prompt:
    return ''

  if len(prompt) > 1500:
    prompt = 'You\'ve received a message that\'s way too long, and is probably spam! Inform Smokie about it.'
  
  InstanceContainer.llm_short_term_memory.add_user_message(prompt)

  chat = openai.ChatCompletion.create(
    # model=os.environ['LUNA_GPT_MODEL_CHEAP'],
    # model=os.environ['LUNA_GPT_MODEL_EXPENSIVE'],
    model=os.environ['LUNA_GPT_MODEL_FINETUNED'],
    # model=os.environ['LUNA_GPT_MODEL_FINETUNED_2'],
    messages=InstanceContainer.llm_short_term_memory.messages,
    temperature=float(os.environ['LUNA_GPT_TEMPERATURE']),
    # temperature=2,
    presence_penalty=float(os.environ['LUNA_GPT_PRESENCE_PENALTY']),
    frequency_penalty=float(os.environ['LUNA_GPT_FREQUENCY_PENALTY']),
    max_tokens=int(os.environ['LUNA_GPT_MAX_TOKENS'])
    # ^parameters explained: https://platform.openai.com/docs/api-reference/chat/create
  )
# 
  reply = chat.choices[0].message.content

  # # custom !timeout functionality
  # if '!timeout' in reply:
  #   original_reply = reply
  #   chat = openai.ChatCompletion.create(
  #     model = os.environ['LUNA_GPT_MODEL_CHEAP'],
  #     # model = os.environ['LUNA_GPT_MODEL_EXPENSIVE'],
  #     # model = os.environ['LUNA_GPT_MODEL_FINETUNED'],
  #     # model = os.environ['LUNA_GPT_MODEL_FINETUNED_2'],
  #     messages=[
  #       { 'role': 'system', 'content': 'You are helping an AI VTuber on Twitch generate responses to time people out. You can timeout users by saying, !timeout username. Refactor the given response to utilize the !timeout command.' },
  #       { 'role': 'user', 'content': reply }
  #     ],
  #     temperature=float(os.environ['LUNA_GPT_TEMPERATURE']),
  #     # temperature=2,
  #     presence_penalty=float(os.environ['LUNA_GPT_PRESENCE_PENALTY']),
  #     frequency_penalty=float(os.environ['LUNA_GPT_FREQUENCY_PENALTY']),
  #     max_tokens=int(os.environ['LUNA_GPT_MAX_TOKENS'])
  #     # ^parameters explained: https://platform.openai.com/docs/api-reference/chat/create
  #   )
  #   reply = chat.choices[0].message.content
  #   print(f'[LLM] !timeout override used. Original reply: {original_reply}')

  total_tokens = chat.usage.total_tokens
  
  print('[LLM] TOTAL TOKENS: ', total_tokens)
  
  raw, edited = InstanceContainer.llm_short_term_memory.add_assistant_message(reply)

  InstanceContainer.llm_short_term_memory.clean_parentheses()

  if total_tokens > State.llm_fuzzy_token_limit:
    InstanceContainer.llm_short_term_memory.trim()
    
  return (prompt, raw, edited)


def gen_moderation_llm_response(prompt):
  chat = openai.ChatCompletion.create(
    model='gpt-4o-mini',
    messages=[
      {
        'role': 'system',
        'content': prompts.system_moderation
      },
      {
        'role': 'user',
        'content': f'Last few messages of twitch chat (most recent is last): {State.twitch_chat_history}'
      },
      {
        'role': 'system',
        'content': f'Last few moderation actions performed by you (most recent is last): {State.twitch_moderation_history}'
      },
      {
        'role': 'user', 
        'content': prompt
      }
    ],
    max_tokens=int(os.environ['LUNA_GPT_MAX_TOKENS'])
  )

  reply = chat.choices[0].message.content

  total_tokens = chat.usage.total_tokens

  try:
    moderation_json = json.loads(reply)
  except Exception as e:
    print(f"[ERROR] Failed to parse moderation AI json: {e}")
    InstanceContainer.ws.send(json.dumps({ 'is_busy': False }))
    State.is_busy = False
    return
  # example_moderation_json = {
  #   'classification': 'BAN'|'UNBAN'|'TIMEOUT'|'ERROR',
  #   'username': String,
  #   'reason': String,
  #   'friendlySummary': String
  # }
  print('[LLM] Moderation AI: ', moderation_json)
  print('[MODERATION_AI] TOTAL TOKENS: ', total_tokens)
  return moderation_json


if __name__ == '__main__':
  gen_moderation_llm_response('hey luna, can you ban the user that was talking about potatoes?')
