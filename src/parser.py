import generate_response as result_generator
import create_parser as CP, transaction_parser as TP

def main():
    create_dict = CP.parse_input_from_file("../testing/test_files/createTest.txt")
    # print(create_dict)
    CP.create_create_xml("../testing/test_files/testCreate.xml", create_dict)
    CP.parse_create_xml_file("../testing/test_files/trialXml.xml")
    orders = TP.parse_orders_from_inputfile("../testing/test_files/testInputOrders.txt")
    TP.create_transaction_xml("../testing/test_files/test_transaction_source.xml", {"id": "123456"}, orders)
    TP.parse_transaction_xml_file("../testing/test_files/test_transaction_source.xml")
    result_generator.generate_create_result_xml(
{"create_results" : {  
                "created_accounts": [{"id":"1234"}, {"id": "432"}],
                "created_symbols": [{ "SPY":{"id":"239487"}}, {"SNP500": {"id":"48893"} }],
                "error_accounts": [{"id": "468289", "msg": "Error response 1"}, {"id": "74992", "msg": "Error response 2"}],
                "error_symbols": [{"id": "37772", "sym": "SPY", "msg": "Error response 3"}]
                }
}
)
    print(result_generator.generate_transaction_result_xml(
            {
        "transaction_results" : {"opened" : [{"sym": "SPY", "limit": "3888", "amount": "3500", "transaction_id": "26"}, {"sym": "SPY", "limit": "3888", "amount": "3500", "transaction_id": "26"}],
                                "error" : [{"sym": "MPS", "limit": "6888", "amount": "6500", "msg": "Failed to create order message"}]
                            },
        "status": [{
                "transaction_id": "12354",
                "open": {"shares": "100"},
                "canceled" : {"shares": "50", "time": "12882"},
                "executed" : [{"shares": "29", "time": "183883", "price": "5000"}, {"shares": "29", "time": "123111122", "price": "5000"}]
                }],
        "canceled":[{"transaction_id": "42879",
            "canceled": {"shares": "50", "time": "<time_value>"},
            "executed" : [{"shares": "29", "time": "<time_value>", "price": "<price_val>"}, {"shares": "29", "time": "183883", "price": "5000"}]
                }]
        }
    )
    )

if __name__=='__main__':
    main()