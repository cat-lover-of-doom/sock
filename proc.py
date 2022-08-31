from types import NoneType


class message_processor:
    def __init__(self) -> None:
        self._message: dict = {}
        self.flags: dict = {}
        self.flags['target'] = 'master'
        self.flags['type'] = 'BASH'

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, message):
        if isinstance(message, (bytes, str)):
            self._message = self.format_message(message)
        elif isinstance(message, dict):
            self._message = message
        elif isinstance(message, NoneType):
            self._message = '\n'
        else:
            raise TypeError(
                f'message must be string or dict, yet {type(message)} was received')

    def format_message(self, msg_to_send: (str | bytes)):
        return {'flags': self.flags, 'msg': msg_to_send}


class client_processor(message_processor):
    def __init__(self) -> None:
        super().__init__()
        self.message_to_send: bool = False
        self.tt_called = False
        self.listen = False

    def process_msg(self):
        self.message_to_send = self._process_flags()

    def _process_flags(self):

        if '$TARGET' in self.message['msg']:
            # makes the flag = the message content after the keyword
            self.flags['target'] = self.message['msg'].split(' ')[1]
            return False

        if '$TYPE' in self.message['msg']:
            self.flags['type'] = self.message['msg'].split(' ')[1]
            return False

        if '$TIMEOUT' in self.message['msg']:
            self.tt_called = int(self.message['msg'].split(' ')[1])
            return False

        if '$LISTEN' in self.message['msg']:
            self.listen = True

        return True
