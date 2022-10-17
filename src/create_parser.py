from venv import create
import xml.etree.ElementTree as ET
import pprint


def parse_create_xml_file(filename):
    return _parse_create_xml(ET.parse(filename))


def parse_create_xml_str(str):
    return _parse_create_xml(ET.ElementTree(ET.fromstring(str)))

#Function to be used by server to decode the xml sent by user
def _parse_create_xml(tree):
    root = tree.getroot()
    top_level_tags = {}
    temp_dict = {}
    top_level_tags["account"] = []
    for i in range(0, len(root)):
        if root[i].tag == "account":
            top_level_tags[root[i].tag].append(root[i].attrib)
        else:
            symbol_list = root[i].attrib
            key = list(symbol_list.values())[0]
            temp_dict[key] = []
            for j in range(0, len(root[i])):
                temp_dict[key].append({list(root[i][j].attrib.keys())[0]:list(root[i][j].attrib.values())[0], "amount":root[i][j].text})
            top_level_tags[root[i].tag] = temp_dict
    return_dict = {root.tag: top_level_tags}
    return return_dict


#This function assumes that the line_elements list is one with string elements
#Deviation from this assumption will cause unexpected effects
def check_id_balance_errors(line_elements):
    account_id = str(line_elements[0].split('=')[1])
    account_balance = str(line_elements[1].split('=')[1][:-1])
    if (not account_id.isalnum()) or (not account_balance.isnumeric()) or (line_elements[0].count('=') != 1) or (line_elements[1].count('=') != 1):
        raise ValueError("Exception: Some values are wrong in the file")


"""
Function to be used by client in order to parse account information 
from text files which returns a dictionary of the relevant information
and thus can be used in creating the xml which will be sent to server
"""
def parse_input_from_file(filename):
    try:
        account_inputfile = open(filename, 'r')
        account_all_lines = account_inputfile.readlines()
        only_one_account_id_given = 0
        result_dict = {}
        result_dict["account"] = []
        for line in account_all_lines:
            line_elements = line.split(', ')
            if line_elements[0].split('=')[0] == "account_id":
                only_one_account_id_given += 1
                account_id = line_elements[0].split('=')[1]
                account_balance = line_elements[1].split('=')[1][:-1]
                check_id_balance_errors(line_elements)
                result_dict["account"].append({"id": account_id, "balance":account_balance})
            else:
                if(len(line_elements) < 3 or line_elements[0].split('=')[0] != "sym" or line_elements[1].split('=')[0] != "account_id" or line_elements[2].split('=')[0] != "no_shares"):
                    raise ValueError("Exception: Invalid format encountered when trying to parse input file")
                symbol = line_elements[0].split('=')[1]
                line_elements = line_elements[1:]
                if(len(line_elements) % 2 != 0):
                    raise ValueError("Exception: Invalid number of tags found in file while parsing symbol information")                
                list_dicts = []
                #Loop to iterate through the different account ids and no_shares that a symbol can have
                for i in range(0, len(line_elements), 2):
                    temp_dict = {}
                    check_id_balance_errors([line_elements[i], line_elements[1]])
                    temp_dict["id"] = line_elements[i].split('=')[1]
                    no_shares = line_elements[i + 1].split('=')[1]
                    if(no_shares[-1] == "\n"):
                        no_shares = no_shares[:-1]
                    temp_dict["no_shares"] = no_shares
                    if(symbol == "account"):
                        raise ValueError("Exception: Symbol's name cannot be account")
                    list_dicts.append(temp_dict)
                result_dict[symbol] = list_dicts
            if(len(line_elements) % 2 != 0):
                    raise ValueError("Exception: Invalid number of tags found in file while parsing symbol information")                
        if(only_one_account_id_given != 1):
            raise ValueError("Exception: Input file has an invalid format")
        # print(result_dict)
        return result_dict
    except Exception as e:
        print(e)

#This function is gonna be used by the client side once parse_input_from_file returns
def create_create_xml(filename, create_dict):
    root = ET.Element("create")
    # for order in order_list:
    tree = ET.ElementTree(root)

    for tag in create_dict:
        if tag != "account":
            symbol_sub = ET.SubElement(root, "symbol", sym=tag)
            for sublist in create_dict[tag]:
                no_shares = sublist["no_shares"]
                ET.SubElement(symbol_sub, "account", id=sublist["id"]).text = no_shares
        else:
            for sub_dict in create_dict[tag]:
                ET.SubElement(root, "account", sub_dict)
    tree.write(filename, xml_declaration=True, encoding='utf-8')
