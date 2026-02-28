import asyncio
from threading import Thread
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from Container import Container
import routes
from db import db_message_get_last_five
from pytwitchapi import run_pytwitchapi
from remind_me import remind_me_async_loop_run
from priority_queue import priority_queue_loop_run
from r_ctrl_stt import r_ctrl_stt_run
from server_extensions import db, ma
import db as models # chatgpt said i need to import this "so metadata is registered"

if __name__ == '__main__':
  container = Container();
  container.app = Flask(__name__)
  container.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
  db.init_app(container.app)
  ma.init_app(container.app)
  with container.app.app_context():
    container.llm_short_term_memory.load_initial_messages(
      db_message_get_last_five()
    )
    # optional: set llm context
    context = ''
    if context:
      container.llm_short_term_memory.set_context(context)
      print(container.llm_short_term_memory.messages[1:])
    db.create_all()
    routes.register(container) # route registration should be last in instantiation order

  def flask_run(container):
    container.app.run(debug=False, port=5001);
  def pytwitchapi_run(container):
    asyncio.run(run_pytwitchapi(container))

  microservices = [
    flask_run,
    pytwitchapi_run,
    priority_queue_loop_run,
    remind_me_async_loop_run,
    r_ctrl_stt_run
  ]
  
  threads = [Thread(target=fn, args=(container,)) for fn in microservices]

  for t in threads: t.start()
  for t in threads: t.join()
