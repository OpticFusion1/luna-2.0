from pynput.keyboard import Key, Listener

def r_ctrl_stt_run(container):
  def pynput_on_press(key):
    if key == Key.ctrl_r:
      container.azure.is_listening = True
      container.azure.recognize_from_microphone(container)

  def pynput_on_release(key):
    if key == Key.pause:
      return False

  # Collect events until released
  with Listener(on_press=pynput_on_press, on_release=pynput_on_release) as listener:
    listener.join()
