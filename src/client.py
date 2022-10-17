import os, socket, argparse
import random
import string

from lxml import etree
import time

''.join(random.choices( string.ascii_uppercase + string.digits, k=5))


def send_xml_in_file(xml_file):
    '''The current iteration of this method assumes that a given xml file contains exactly ONE xml request'''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        with open(xml_file, "rb") as f:
            # print(f"Size - {os.stat(xml_file).st_size}")
            file_size = os.stat(xml_file).st_size
            s.send(f"{file_size}\n".encode('utf-8')) # send the length in bytes of the xml that we are about to send first
            char_buffer = f.read(1024)
            while char_buffer:
                # print(f"Message Contents: \n{char_buffer}")
                s.send(char_buffer)
                char_buffer = f.read(1024)
        response = s.recv(4096)
        response_xml = etree.fromstring(response)
        print("\nHere is the response received:")
        print(etree.tostring(response_xml, pretty_print=True).decode())



if __name__ == "__main__":
    # HOST = "127.0.0.1"
    HOST = "vcm-24729.vm.duke.edu"
    PORT = 12345

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", dest="filename", help="Pass path of xml file")

    parser.add_argument("-host", "--host", dest="hostname", help="Enter the hostname of the running server instance")

    parser.add_argument("-tc", "--test_create", dest="is_test_create", help="Optional Flag to Run Create Test", action='store_true')
    parser.add_argument("-tt", "--test_transactions", dest="is_test_trans", help="Optional Flag to Run Transaction Test", action='store_true')


    args = parser.parse_args()

    input_xml_file = args.filename
    if args.hostname:
        server_host = args.hostname
    else:
        server_host = HOST
    is_test_create = args.is_test_create
    is_trans_create = args.is_test_trans

    if input_xml_file:
        start = time.time()
        send_xml_in_file(input_xml_file)
        end = time.time()
        # print(end - start)
    elif is_test_create:
        send_xml_in_file("../testing/test_files/test_create_processing.xml")
    elif is_trans_create:
        send_xml_in_file("../testing/test_files/test_transaction_source.xml")