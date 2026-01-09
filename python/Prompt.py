class Prompt:
  def __init__(
    self,
    prompt,
    priority,
    utterance_id = None,
    azure_speaking_style = None,
    is_speaking_fast = False,
    username_to_ban = None,
    username_to_unban = None,
    is_eleven_labs = False,
    should_generate_audio_file_only = False,
    should_use_moderation_ai = False,
    pytwitchapi_args = {}
  ):
    self.prompt = prompt
    self.priority = priority
    self.utterance_id = utterance_id
    self.azure_speaking_style = azure_speaking_style
    self.is_speaking_fast = is_speaking_fast
    self.username_to_ban = username_to_ban
    self.username_to_unban = username_to_unban
    self.is_eleven_labs = is_eleven_labs
    self.should_generate_audio_file_only = should_generate_audio_file_only
    self.should_use_moderation_ai = should_use_moderation_ai
    self.pytwitchapi_args = pytwitchapi_args
    