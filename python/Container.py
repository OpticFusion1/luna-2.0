from PriorityQueue import PriorityQueue
from LLMShortTermMemory import LLMShortTermMemory
from websocket import create_connection
from Azure import Azure
import threading

class Container:
  def __init__(self):
    # the vtuber can't perform any actions while is_busy is True.
    self.is_busy = False
    # llm fuzzy token limit
    self.llm_fuzzy_token_limit = 750
    # seconds of delay bewteen ai responses
    self.ai_response_delay = 2.5
    # is the vtuber responding to twitch chat?
    self.is_twitch_chat_react_on = True
    # is the vtuber responding to twitch chat, but only if @ mentioned?
    self.is_quiet_mode_on = True
    # is singing in action
    self.is_singing = False
    # id/name of last banned user
    self.last_banned_user_id = None
    self.last_banned_user_name = 'nabbebabbe_'
    # stores tuples like ('remind foo to bar!', datetime)
    self.remind_me_prompts_and_datetime_queue = []
    self.remind_lock = threading.Lock()
    # stores raffle entries
    self.raffle_entries_set = set()
    # stores comma-separated strings
    self.luna_wheel_queue = []
    # storage for the vtuber's queued up actions
    self.priority_queue = PriorityQueue()
    # azure tts/stt instance
    self.azure = Azure()
    # flask server
    self.app = None
    # llm short term memory
    self.llm_short_term_memory = LLMShortTermMemory()
    # websocket connection instance
    self.ws = create_connection('ws://localhost:4000')
    # pytwitchapi instances
    self.twitch = None
    self.chat = None
    self.eventsub = None
    
    print('[CONFIG] Initialized Container.')
