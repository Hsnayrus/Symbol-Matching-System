import xml.etree.ElementTree as ET
import argparse


def create_xmls(no_xmls, starting_account_number, file_prefix):
    for i in range (0, no_xmls):
        filename = file_prefix + str(i) + ".xml"
        file = open(filename, "w+")
        root = ET.Element("create")
        tree = ET.ElementTree(root)
        account_id = starting_account_number + i
        account_balance = 1000 * (i + 1)
        ET.SubElement(root, "account", id=str(account_id), balance=str(account_balance))
        tree.write(filename, xml_declaration=True, encoding='utf-8')

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", dest="file_prefix", help="Destintation folder of xml file")
    parser.add_argument("-n", "--no_files", dest="no_files", help="Number of files to generate")

    args = parser.parse_args()

    file_prefix = args.file_prefix
    no_files = args.no_files

    create_xmls(int(no_files), 1000, file_prefix)