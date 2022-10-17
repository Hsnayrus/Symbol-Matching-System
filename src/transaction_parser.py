import xml.etree.ElementTree as ET

#Function to be used by client side to change the orders from txt file
#into a dictionary which is used to create the xml request that is gonna
#sent to server
def parse_orders_from_inputfile(filename):
    input_file = open(filename)
    file_all_lines = input_file.readlines()
    all_transactions = {}
    all_transactions["order"] = []
    all_transactions["query"] = []
    all_transactions["cancel"] = []
    for line in file_all_lines:
        line_elements = line.split(' ')
        line_elements[-1] = line_elements[-1][1:-1]
        if "Buy" in line_elements or "Sell" in line_elements:
            line_elements.remove('@')
            if line_elements[0].lower() == "sell":
                line_elements[1] = "-" + line_elements[1]
            all_transactions["order"].append(line_elements)
        elif "Query" in line_elements:
            all_transactions["query"].append(line_elements)
        else:
            all_transactions["cancel"].append(line_elements)
    return all_transactions

"""
Filename is the name of the output transactions file
account_id is a dictionary of the format {"account": id_number}
order_list is the list of orders which are the result of the 
parse_order_from_inputfile function
This function assumes order_list is in the format:
    
    [[order_type, no_shares, share_symbol, limit_price]]
"""
def create_transaction_xml(filename, account_id, order_list)    :
    root = ET.Element("transactions", account_id)
    # for order in order_list:
    tree = ET.ElementTree(root)
    
    for order_type in order_list:
        for order_sublist in order_list[order_type]:
            if(order_type == "order"):
                ET.SubElement(root, order_type, sym=order_sublist[2], amount=order_sublist[1], limit=order_sublist[3])
            else:
                ET.SubElement(root, order_type, id=order_sublist[1])
    
    tree.write(filename, xml_declaration=True, encoding='utf-8')


def parse_transaction_xml_file(filename):
    return _parse_transaction_xml(ET.parse(filename))


def parse_transaction_xml_str(str):
    return _parse_transaction_xml(ET.ElementTree(ET.fromstring(str)))


#This function is to be used by server for parsing the received transaction xml
def _parse_transaction_xml(tree):
    # tree = ET.parse(filename)
    root = tree.getroot()
    result_dict = {}
    result_dict["id"] = root.attrib["id"]
    result_dict["children"] = {"order":[], "query":[], "cancel":[]}
    for i in range(0, len(root)):
        result_dict["children"][root[i].tag].append(root[i].attrib)
    return_dict = {root.tag: result_dict}
    return return_dict

"""
<results>
<created id="ACCOUNT_ID"/> #For account create
<created sym="SYM" id="ACCOUNT_ID"/> #For symbol create
<error id="ACCOUNT_ID">Msg</error> #For account create error
<error sym="SYM" id="ACCOUNT_ID">Msg</error> #For symbol create
error
</results>



//Response to create xml
{"results" : {"accounts": [{"id":"1234", "status":"Cancelled/Not cancelled"}], " symbols": [{"SPY":{"id":"239487"}, {"SNP500": {"id":"48893"}}}], }} 

Results
    For each accoutn id we received, we need to check if there is an error or not 
//Response to transaction xml

"""