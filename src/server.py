import socket
import pprint
from multiprocessing import Process
from create_parser import parse_create_xml_str
from transaction_parser import parse_transaction_xml_str
from process_requests import process_requests, print_database_objs
from generate_response import generate_create_result_xml, generate_transaction_result_xml
from lxml import etree


TRANSACTION_TAG = "</transactions>"
CREATE_TAG = "</create>"


def receive_msg_of_length(socket, msg_length):
    message = b''
    while (len(message) < msg_length):
        num_bytes_to_read = msg_length - len(message)
        incoming_data = socket.recv(num_bytes_to_read)
        if not incoming_data:
            break
        else:
            message += incoming_data
    return message


def read_next_byte_as_str(socket):
    return socket.recv(1).decode('utf-8')


def receive_one_line(socket):
    line_str = ''
    curr_char = read_next_byte_as_str(socket)
    while (curr_char != '\n'):
        line_str += curr_char
        curr_char = read_next_byte_as_str(socket)
    return line_str


def process_incoming_xml_requests():
    msg_length = int(receive_one_line(conn))
    msg = receive_msg_of_length(conn, msg_length).decode('utf-8')
    print("Recevied the following message:\n{}".format(msg))
    # we expect msg to be an xml string with either a transaction or create tag
    if CREATE_TAG in msg:
        print("processing a create message!")
        msg_as_dict = parse_create_xml_str(msg)
        print("Here is the create dict produced:")
        pprint.pprint(msg_as_dict)
        print("")
    elif TRANSACTION_TAG in msg:
        print("processing a transaction message!")
        msg_as_dict = parse_transaction_xml_str(msg)
        print("Here is the transaction dict produced:")
        pprint.pprint(msg_as_dict)
        print("")
    else:
        raise RuntimeError("Invalid Request Tag: Given tag was not either CREATE or TRANSACTION")

    # consume XML
    response_dicts = process_requests(msg_as_dict)
    print("This is what the response_dicts look like:\n")
    pprint.pprint(response_dicts)

    responses = [] # list of string responses to return
    for response_dict in response_dicts:
        if "create_results" in response_dict.keys():
            print("found create_results")
            return_msg = generate_create_result_xml(response_dict)
            responses.append(return_msg)
        elif "transaction_results" in response_dict.keys() or "status" in response_dict.keys() or "canceled" in response_dict.keys():
            print("found transaction_results")
            return_msg = generate_transaction_result_xml(response_dict)
            responses.append(return_msg)
        else:
            raise ValueError(f"Invalid Response Dict: Given response did not contain required 'create_results' or 'transaction_results' top-level keys\n {response_dict.keys()}")

    print("\nHere are the responses:")
    for response in responses:
        response_xml = etree.fromstring(response)
        print(etree.tostring(response_xml, pretty_print=True).decode())
        # pprint.pprint(response.decode('utf-8'))

    for response in responses:
      conn.send(response)
    print("\n")
    print_database_objs()



if __name__ == "__main__":
    HOST = socket.gethostname()
    PORT = 12345
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, client_addr = s.accept()
            with conn:
                print(f"Connected by {client_addr}")
                p = Process(target=process_incoming_xml_requests())
                p.start()
                p.join()
