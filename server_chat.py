import select
from commun import server

sv = server('localhost', 8888)


def main() -> None:
    """main function that runs the code"""

    while True:

        read_sockets, _, _ = select.select(
            sv.sockets_list, [], sv.sockets_list)

        for notified_socket in read_sockets:

            if notified_socket == sv.server_socket:
                try:
                    sv.handle_new()
                except UnicodeDecodeError:
                    continue
            else:
                sv.handle_traffic(notified_socket)


main()
