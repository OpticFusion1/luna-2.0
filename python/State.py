# centralized state

# this class uses the singleton pattern to avoid multiple instantiations
class StateClass:
  _instance = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super(StateClass, cls).__new__(cls, *args, **kwargs)
      cls._instance.__initialize()
      return cls._instance

  def __initialize(self):
    # the vtuber can't perform any actions while is_busy is True.
    self.is_busy = False
    # llm fuzzy token limit
    self.llm_fuzzy_token_limit = 750
    # make this false for a couple seconds to terminate the audio playing loop.
    self.tts_green_light = True
    # seconds of delay bewteen ai responses
    self.ai_response_delay = 2.5
    # is the vtuber responding to twitch chat?
    self.is_twitch_chat_react_on = True
    # is the vtuber responding to twitch chat, but only if @ mentioned?
    self.is_quiet_mode_on = True
    # is singing in action
    self.is_singing = False
    # speaking speed
    self.is_speaking_fast = False
    # id of last banned user
    self.last_banned_user_id = None
    self.last_banned_user_name = 'nabbebabbe_'

    # stores tuples like ('remind foo to bar!', datetime)
    self.remind_me_prompts_and_datetime_queue = []
    # stores raffle entries
    self.raffle_entries_set = set()
    # stores comma-separated strings
    self.luna_wheel_queue = []
    
    # twitch chat message history for moderation
    self.twitch_chat_history = ['babboon1: hey sokie', 'vespa2: you look like a potato', 'kax324: no she doesnt look like a potato lol', 'vespa2: yea she does lol', 'yax77: hey, are you playing in pohx league?']
    # twitch moderation ai action history
    self.twitch_moderation_history = ['banned xdc2 for swearing', 'banned ax22 for being a spam bot', 'unbanned ax22 for being a spam bot', 'banned ravs2 for being spam bot', 'timed out jansen88 for 30s for saying the banned word: hearthstone']
    # this token will be consumed to make the next voice/text message by me an admin message
    self.luna_admin_token = False

    print('[CONFIG] Initialized State.')


State = StateClass()
