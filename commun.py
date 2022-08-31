import socket
import pickle
import logging

PATH = '\\'.join(__file__.split('\\')[:-1])

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formater = logging.Formatter(
    '%(asctime)s - %(message)s')

file_handler = logging.FileHandler(f'server_logs.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formater)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formater)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class usergen:
    def __init__(self) -> None:
        self.current = 0
        self.free = []

    def yied_user(self):
        if not self.free:
            self.current += 1
            return str(self.current)
        else:
            return self.free.pop(0)


class communicator:
    def __init__(self, header_lenght) -> None:
        self.header_length: int = header_lenght
        self.socket: socket.socket = None
        self.timeout = None

    def receive_message(self, target_socket: socket.socket):
        try:
            message_header = target_socket.recv(self.header_length)

            if not message_header:
                return
            message_length = int(message_header.decode('utf-8').strip())
            message = pickle.loads(target_socket.recv(message_length))

            return message

        except ConnectionResetError:
            return None
        except TimeoutError:
            return None
        except ValueError:
            return None
        except pickle.PickleError:
            print('data was interrupted, try again')
            return None

    def send_message(self, msg_to_send: str, target_socket: socket.socket):
        msg_to_send = pickle.dumps(msg_to_send)
        message_header = f"{len(msg_to_send):<{self.header_length}}".encode(
            'utf-8')

        target_socket.send(message_header + msg_to_send)


class client(communicator):
    def __init__(self, username, ip_in: str, port: int, timeout: bool = False) -> None:
        super().__init__(10)
        self.ip_address: str = ip_in
        self.port: int = port
        self.username = username
        self.timeout = timeout
        self.establish_connection()

    def establish_connection(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip_address, self.port))

        if self.timeout:
            self.socket.settimeout(1)

        print(f'online at ({self.ip_address}, {self.port})')

        self.send_message(self.username, self.socket)


class server(communicator):
    def __init__(self, addres: str, port: int) -> None:
        super().__init__(10)
        self.socket = None
        self.ip_address = addres
        self.port = port
        self.boot_up()
        self.sockets_list = [self.server_socket]
        self.clients = {}
        self.user_generator = usergen()

    def boot_up(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip_address, self.port))
        print(f'server online at ({self.ip_address},{self.port})')
        self.server_socket.listen()

    def handle_new(self):
        client_socket, client_addr = self.server_socket.accept()
        username = self.receive_message(client_socket)

        if not username:
            return

        if username != 'master':
            username = self.user_generator.yied_user()
        self.sockets_list.append(client_socket)
        self.clients[client_socket] = username
        # unused pylint: disable=logging-fstring-interpolation
        logger.log(logging.INFO,
                   f'Accepted new connection from {client_addr[0]}:{client_addr[1]}, username: {username}')

    def handle_traffic(self, notified_socket):
        message = self.receive_message(notified_socket)

        username = self.clients[notified_socket]
        if not message:
            # unused pylint: disable=logging-fstring-interpolation
            logger.log(logging.INFO,
                       f'Closed connection from: {username}')

            self.sockets_list.remove(notified_socket)
            self.user_generator.free.append(username)
            self.user_generator.free.sort()
            del username
            return
        if message['msg'] == '\n':
            return

        if message['flags']['type'] == 'LOGS':
            with open('server_logs.log', 'r') as file:
                lines_of_log = file.read()

            self.send_message({'msg':lines_of_log}, notified_socket)
            return

        # unused pylint: disable=logging-fstring-interpolation
        logger.log(
            logging.INFO, f'Received message from {username}: {message}')

        for client_socket in self.sockets_list:
            msg_target = message['flags']['target']

            if msg_target == 'ALL':
                if client_socket not in (notified_socket, self.server_socket):
                    self.send_message(message, client_socket)
                    
            else:
                if client_socket not in (notified_socket, self.server_socket) and msg_target == self.clients[client_socket]:
                    self.send_message(message, client_socket)
