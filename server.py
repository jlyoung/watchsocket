import logging
import shlex
import subprocess
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
from watchersdict import watchers

class WSHandler(tornado.websocket.WebSocketHandler):
	def open(self, hostname, terminal):
		self.write_message("Connected %s to %s." % (hostname, terminal))
		global_message_buffer.wait_for_messages(self.on_new_message, hostname, terminal)
	def on_message(self, message):
		logging.info('message received %s' % message)
	def on_close(self):
		self.write_message("Disconnecting.")
		logging.info('connection closed')
	def on_new_message(self, message):
		self.write_message(message)

class TaskRunner(object):
	def __init__(self, hostname, terminal, command):
		self.hostname = hostname
		self.terminal = terminal
		self.command = command

	def exec_task(self):
		try:
			logging.info("exec_task command = %s" % self.command)
			message = subprocess.check_output(shlex.split(self.command))
			logging.debug("Command execution output = %s" % message)
			global_message_buffer.new_message(self.hostname, self.terminal, message)
			logging.info("Adding message to global_message_buffer.")
		except StopIteration:
			logging.error("Unable to add new message for hostname %s, terminal %s, message %s " % (self.hostname, self.terminal, message))

class MessageBuffer(object):
	def __init__(self):
		self.waiters = set()

	def wait_for_messages(self, callback, hostname, terminal):
		logging.info("Waiting for messages: hostname %s, terminal %s" % (hostname, terminal))
		self.waiters.add((callback, hostname, terminal))

	def cancel_wait(self, callback, hostname, terminal):
		self.waiters.remove((callback, hostname, terminal))

	def new_message(self, target_hostname, target_terminal, message):
		logging.info("Sending new message to %r listeners", len(self.waiters))
		for cht_tuple in self.waiters:
			callback, hostname, terminal = cht_tuple
			if hostname == target_hostname and terminal == target_terminal:
				try:
					logging.info("Writing new message for hostname %s, terminal %s." % (hostname, terminal))
					logging.debug(message)
					callback(message)
				except:
					logging.error("Error in waiter callback for hostname %s, terminal %s" % (hostname, terminal), exc_info=True)

global_message_buffer = MessageBuffer()

static_path = './static'
application = tornado.web.Application([
	(r'/static/(.*)', tornado.web.StaticFileHandler, {'path': static_path}),
	(r'/ws/(\w+)/(\w+)', WSHandler),
])

if __name__ == '__main__':
	logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
	application.listen(8888)
	default_interval_ms = 5 * 1000
	main_ioloop = tornado.ioloop.IOLoop.instance()
	for host_key, host_val in watchers.iteritems():
		for terminal_key, terminal_val in host_val.iteritems():
			if 'interval' in terminal_val:
				interval_ms = terminal_val['interval']
			else:
				interval_ms = default_interval_ms
			if 'command' in terminal_val:
				logging.info("Creating TaskRunner object for host_key %s, terminal_key %s, command %s" % (host_key,terminal_key,terminal_val['command']))
				task = TaskRunner(host_key, terminal_key, terminal_val['command'])
				logging.info("Creating task_scheduler")			
				task_scheduler = tornado.ioloop.PeriodicCallback(task.exec_task, interval_ms, io_loop=main_ioloop)
				task_scheduler.start()
			else:
				logging.error('%s : %s does not have a command specified!' % (host_key, terminal_key))
	main_ioloop.start()
