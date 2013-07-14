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
		print 'message received %s' % message
	def on_close(self):
		self.write_message("Disconnecting.")
		print 'connection closed'
	def on_new_message(self, message):
		self.write_message(message)

class TaskRunner(object):
	def __init__(self, hostname, terminal, command):
		self.hostname = hostname
		self.terminal = terminal
		self.command = command

	def exec_task(self):
		try:
			print "exec_task command = %s" % self.command
			message = subprocess.check_output(shlex.split(self.command))
			print "Command execution output = %s" % message
			global_message_buffer.new_message(self.hostname, self.terminal, message)
			print "Adding message to global_message_buffer."
		except StopIteration:
			print "Unable to add new message for hostname %s, terminal %s, message %s " % (self.hostname, self.terminal, message)

class MessageBuffer(object):
	def __init__(self):
		self.waiters = set()

	def wait_for_messages(self, callback, hostname, terminal):
		print "Waiting for messages: hostname %s, terminal %s" % (hostname, terminal)
		self.waiters.add((callback, hostname, terminal))

	def cancel_wait(self, callback, hostname, terminal):
		self.waiters.remove((callback, hostname, terminal))

	def new_message(self, target_hostname, target_terminal, message):
		logging.info("Sending new message to %r listeners", len(self.waiters))
		for cht_tuple in self.waiters:
			callback, hostname, terminal = cht_tuple
			if hostname == target_hostname and terminal == target_terminal:
				try:
					print "Writing new message for hostname %s, terminal %s: %s" % (hostname, terminal, message)			
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
	application.listen(8888)
	interval_ms = 5 * 1000
	main_ioloop = tornado.ioloop.IOLoop.instance()
	for host_key, host_val in watchers.iteritems():
		for terminal_key, terminal_val in host_val.iteritems():
			for k, v in terminal_val.iteritems():
				if k == "command":
					print "Creating TaskRunner object for host_key %s, terminal_key %s, command %s" % (host_key,terminal_key,v)
					task = TaskRunner(host_key, terminal_key, v)
					print "Creating task_scheduler"				
					task_scheduler = tornado.ioloop.PeriodicCallback(task.exec_task, interval_ms, io_loop=main_ioloop)
					task_scheduler.start()
	main_ioloop.start()
