import xml.etree.ElementTree as ET
import pprint

"""
//Response to create xml
{"create_results" : {  
                "created_accounts": [{"id":"1234"}, {"id": "432"}],
                "created_symbols": [{ "SPY":{"id":"239487"} }, { "SNP500": {"id":"48893"} }],
                "error_accounts": [{"id": "468289", "msg": "Error response 1"}, {"id": "74992", "msg": "Error response 2"}],
                "error_symbols": [{"id": "37772", "sym": "SPY", "msg": "Error response 3"}]
                }
}

This function generates the result xml given the result_create_dictionary
"""
def generate_create_result_xml(result_create_dict):
    root = ET.Element("results")
    result_dict = result_create_dict["create_results"]
    for tag in result_dict:
        if tag == "created_accounts":
            for account in result_dict[tag]:
                ET.SubElement(root, "created", id=account["id"])
        if tag == "error_accounts":
            for account in result_dict[tag]:
                ET.SubElement(root, "error", id=account["id"]).text = account["msg"]
        if tag ==  "created_symbols":
            for symbol in result_dict[tag]:
                actual_sym = list(symbol.keys())[0]
                actual_sym_id = list(symbol.values())[0]["id"]
                ET.SubElement(root, "created", sym=actual_sym, id=actual_sym_id)
        if tag == "error_symbols":
            for symbol in result_dict[tag]:
                ET.SubElement(root, "error", sym=symbol["sym"], id=symbol["id"]).text = symbol["msg"]

    return_str = ET.tostring(root, xml_declaration=True, encoding='utf-8')
    return return_str

"""
This function generates the result xml for a transaction xml received from the client
//Response to transaction xml:
{
    "transaction_results" : {  "opened" : [{"sym": "SPY", "limit": "3888", "amount": "3500", "transaction_id": "26"}],
                            "error" : [{"sym": "MPS", "limit": "6888", "amount": "6500", "msg": "Failed to create order message"}]
                        },
    "status": {
            "transaction_id": "12354",
            "open": {"shares": "100"},
            "canceled" : {"shares": "50", "time": "<time_value>"},
            "executed" : [{"shares": "29", "time": "<time_value>", "price": "<price_val>"}]
            },
    "canceled":[{"transaction_id": "42879",
        "cancelled": {"shares": "50", "time": "<time_value>"},
        "executed" : {"shares": "29", "time": "<time_value>", "price": "<price_val>"}
    }]

}

"""
def generate_transaction_result_xml(result_transaction_dict):
    root = ET.Element("results")
    for tag in result_transaction_dict:
        if tag == "transaction_results":
            for sub_tag in result_transaction_dict[tag]:
                for sub_dict in result_transaction_dict[tag][sub_tag]:
                    if sub_tag == "opened":
                        ET.SubElement(root, sub_tag, sym=sub_dict["sym"], amount=sub_dict["amount"], limit=sub_dict["limit"], id=sub_dict["transaction_id"])
                    else:
                        ET.SubElement(root, sub_tag, sym=sub_dict["sym"], amount=sub_dict["amount"], limit=sub_dict["limit"]).text = sub_dict["msg"]
        if tag == "status":
            for sub_dict in result_transaction_dict[tag]:
                status_id = ET.SubElement(root, "status", id=sub_dict["transaction_id"])
                if "open" in sub_dict:
                    ET.SubElement(status_id, "open", sub_dict["open"])
                elif "canceled" in sub_dict:
                    ET.SubElement(status_id, "canceled", sub_dict["canceled"])
                for sub_sub_dict in sub_dict["executed"]:
                    ET.SubElement(status_id, "executed", sub_sub_dict)
        if tag == "canceled":
            for sub_dict in result_transaction_dict[tag]:
                canceled_id = ET.SubElement(root, "canceled", id=sub_dict["transaction_id"])
                ET.SubElement(canceled_id, "canceled", sub_dict["canceled"])
                for sub_sub_dict in sub_dict["executed"]:
                    ET.SubElement(canceled_id, "executed", sub_sub_dict)
    return_str = ET.tostring(root, xml_declaration=True, encoding='utf-8')
    return return_str

