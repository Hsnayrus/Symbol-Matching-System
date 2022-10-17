import os, django
import pprint
import sys
import re

from django.db import transaction
from django.db.models import Sum
from django.db.models import Q

sys.path.append('..')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from data.models import Symbol, Account, Position, Order, ExecutedOrder, CanceledOrder


create_test_default = {'create' :
                           {'account':
                                {'id': "123456",'balance': "1000"},
                            'symbol': {'SPY':
                                           [
                                               {'id': "123456", 'amount': "100000"}
                                           ]
                                       }
                            },
                       'transactions':
                           {'id': "123456",
                            'children':
                               [
                                   {'order':
                                        {'sym': "SPY", 'amount': "500", 'limit': "550.67"}
                                    },
                                   {'query':
                                        {'id': "1"}
                                    },
                                   # {'cancel':
                                   #      {'id': "2"}
                                   #  }
                               ]
                            }
                       }


def set_sym_position_for_account(sym, new_position_amount, account):
    print(f"Setting sym position for the following account --->\nSYM - {sym} | AMOUNT - {new_position_amount} | ACCOUNT - {account}")
    # print("State of database BEFORE deleting position objects:")
    # print_database_objs()
    # remove existing positions
    Position.objects.all().filter(sym=sym, account=account).delete()
    # print("State of database AFTER deleting position objects:")
    # print_database_objs()
    print("New_Position_Amount = {}".format(new_position_amount))
    create_position(sym.sym, account.id, new_position_amount)

def get_num_shares_in_acct(sym, account):
    # sum all of the Position amounts associated with the given sym and account
    return Position.objects.all().filter(sym=sym, account=account).aggregate(Sum('amount'))['amount__sum']


def execute_orders(sell_order, buy_order, sale_price):

    buyer_account = buy_order.account
    seller_account = sell_order.account
    print("START OF EXECUTE ORDERS: This is the buy_order {}".format(buy_order))
    print("START OF EXECUTE ORDERS: This is the sell_order {}".format(sell_order))
    completed_orders = [] # <-- this line is not necessary anymore
    if abs(sell_order.amount) > buy_order.amount:
        num_shares = abs(buy_order.amount)
        completed_orders.append(buy_order)
    elif buy_order.amount > abs(sell_order.amount):
        num_shares = abs(sell_order.amount)
        completed_orders.append(sell_order)
    else:
        # if the order amounts match exactly, then lets complete (remove) both
        # orders and specify num_shares to be equal to either buy_order.amount or
        # sell_order.amount as they are equivalent
        num_shares = abs(buy_order.amount)
        completed_orders.append(buy_order)
        completed_orders.append(sell_order)

    total_order_cost = abs(sale_price * num_shares)
    seller_shares = seller_account.get_num_owned_shares_of(sell_order.sym)
    buyer_shares = buyer_account.get_num_owned_shares_of(buy_order.sym)

    print("SELLER_SHARES -- {}".format(seller_shares))
    print("BUYER_SHARES -- {}".format(buyer_shares))

    # seller_shares = get_num_shares_in_acct(sell_order.sym, seller_account)
    # buyer_shares = get_num_shares_in_acct(buy_order.sym, buyer_account)
    # withdraw and deposit the funds associated with our transaction
    seller_account.deposit(total_order_cost)
    buyer_account.withdraw(total_order_cost)

    sell_order.sell_n_shares(num_shares)
    buy_order.buy_n_shares(num_shares)

    new_sell_executed_order = ExecutedOrder(order=sell_order, shares= -1 * num_shares, sale_price=sale_price)
    new_sell_executed_order.save()

    new_buy_executed_order = ExecutedOrder(order=buy_order, shares=num_shares, sale_price=sale_price)
    new_buy_executed_order.save()

    set_sym_position_for_account(sell_order.sym, seller_shares - num_shares, seller_account)
    set_sym_position_for_account(buy_order.sym, buyer_shares + num_shares, buyer_account)


@transaction.atomic()
def find_matching_order(order):
    # when your server matches orders, it MUST (a) give the best price match, and (b) break ties giving priority
    # to orders that arrived earlier
    sym = order.sym
    account = order.account
    amount = order.amount
    limit = order.limit
    buyers_share_price = limit * amount
    # seller's limit price <= execution price <= buyer's limit price
    if amount < 0:
        # order is a SELL; look for matching BUY orders
        # first see how many shares the user trying to sell actually owns
        owned_shares = get_num_shares_in_acct(sym, account)
        if owned_shares < amount:
            raise AttributeError(
                f"Insufficient Stock: "
                f"Account that placed order does not have {amount} shares of {sym} to sell (only has {owned_shares})")
        # Criteria for matched buy order:
        # Find all BUY orders (Order amount greater than 0) for the given symbol
        # where the buyer is willing to purchase the stock for AT LEAST as much as I am willing to sell it (limit gte to my limit)
        buy_orders = Order.objects.filter(~Q(order_id=order.order_id), sym=sym, amount__gt=0, limit__gte=limit, status='open').order_by('limit', 'creation_time').select_for_update()
        shares_to_sell = amount
        for buy_order in buy_orders:
            # loop through the buy orders and start matching them up until
            # we either run out of shares to sell OR we reach the end of the list
            shares_being_bought = buy_order.amount
            if shares_being_bought >= shares_to_sell:
                # complete the sale of the shares to the buying account at their requested limit price
                print(f"Executing a Buy Order of {buy_order}")
                execute_orders(order, buy_order, sale_price=buy_order.limit)
                return
            else:
                print(f"Executing a Buy Order of {buy_order}")
                shares_to_sell -= shares_being_bought
                execute_orders(order, buy_order)
    else:
        # order is a BUY; look for matching SELL orders
        # make sure that the user account has enough of a balance to complete the purchase
        if account.balance < buyers_share_price:
            raise AttributeError(f"Insufficient Balance: Account that placed order does not have enough money to purchase {amount} shares of {sym} at {limit} each")
        sell_orders = Order.objects.filter(~Q(order_id=order.order_id), sym=sym, amount__lt=0, limit__lte=limit, status='open').order_by('-limit', 'creation_time').select_for_update()
        shares_to_buy = amount
        for sell_order in sell_orders:
            shares_being_sold = sell_order.amount
            if shares_being_sold >= shares_to_buy:
                print(f"Executing a Sell Order of {sell_order}")
                execute_orders(sell_order, order, sale_price=sell_order.limit)
                return
            else:
                print(f"Executing a Sell Order of {sell_order}")
                shares_to_buy -= shares_being_sold
                execute_orders(sell_order, order, sale_price=sell_order.limit)



def generate_order(sym, acct_id, amount, limit):
    # by default make the order status 'open'
    order_sym = Symbol.objects.get(sym__exact=sym)
    order_acct = Account.objects.get(id__exact=acct_id)
    shares_owned = order_acct.get_num_owned_shares_of(order_sym)
    if amount < 0 and shares_owned < abs(amount):
        # if we are trying to create a sell order but the account does not have enough stock, then throw an error
        raise ValueError(f"Invalid Order: Account {acct_id} does not have enough stock to sell (requested {amount} ; owned {shares_owned})")
    new_order = Order(sym=order_sym, account=order_acct, amount=amount, limit=limit, status='open')
    new_order.save()
    return new_order


def generate_open_order_resp(open_order):
    return {"sym": open_order.sym.sym, "limit": str(open_order.limit), "amount": str(open_order.amount), "transaction_id": str(open_order.order_id)}


def cancel_order(order_id):
    try:
        queried_transaction = Order.objects.get(order_id=order_id)
        queried_transaction.cancel()
        cancel_response_entry = {"transaction_id": str(queried_transaction.order_id)}
        executed_orders = ExecutedOrder.objects.filter(~Q(shares=0), order=queried_transaction)
        cancel_response_entry["executed"] = []
        for executed_order in executed_orders:
            cancel_response_entry["executed"].append(
                {"shares": str(executed_order.shares),
                 "time": str(executed_order.time.timestamp()),
                 "price": str(executed_order.sale_price)})
        canceled_order = CanceledOrder.objects.filter(order=queried_transaction).first()
        cancel_response_entry["canceled"] = {}
        if canceled_order:
            cancel_response_entry["canceled"]["shares"] = str(canceled_order.shares)
            cancel_response_entry["canceled"]["time"] = str(canceled_order.time.timestamp())

        print(f"Successfully deleted order with id {order_id}")
        return cancel_response_entry
    except:
        raise ValueError(f"Invalid CANCEL: No order found with given id '{order_id}'")





def query_order_with_id(order_id):
    queried_transaction = Order.objects.get(order_id=order_id)
    query_response_entry = {"transaction_id": str(queried_transaction.order_id)}
    order_status = queried_transaction.status
    # print("Here is the order_status - {}".format(order_status))
    # query_response_entry["open"] = {}
    if order_status == "open":
        if not "open" in query_response_entry:
            query_response_entry["open"] = {}
        query_response_entry["open"] = {"shares": str(queried_transaction.amount)}
    executed_orders = ExecutedOrder.objects.filter(~Q(shares=0), order=queried_transaction)
    query_response_entry["executed"] = []
    for executed_order in executed_orders:
        query_response_entry["executed"].append(
            {"shares": str(executed_order.shares),
             "time": str(executed_order.time.timestamp()),
             "price": str(executed_order.sale_price)})
    canceled_order = CanceledOrder.objects.filter(order=queried_transaction).first()
    query_response_entry["canceled"] = {}
    if canceled_order:
        query_response_entry["canceled"]["shares"] = str(canceled_order.shares)
        query_response_entry["canceled"]["time"] = str(canceled_order.time.timestamp())
    print(f"TRANSACTION STATUS: {order_status}")
    return query_response_entry


def create_position(sym, acct_id, amount):
    position_sym = Symbol.objects.get(sym__exact=sym)
    position_acct = Account.objects.get(id__exact=acct_id)
    with transaction.atomic():
        new_position = Position(account=position_acct, sym=position_sym, amount=amount)
        new_position.save()


def create_account(id, balance):
    account_created_dict = {}
    if not Account.objects.filter(id = id).exists():
        new_account = Account(id=id, balance=balance)
        # attempting to create an account that already exists should return an error
        new_account.save()
        account_created_dict["created_accounts"] = {"id" : str(id)}
    else:
        account_created_dict["error_accounts"] = {"id": str(id), "msg": "Account already exists"}
    
    return account_created_dict


def create_symbol(sym, positions):
    symbol_created_dict = {}# <--- fill this with our info
    symbol = Symbol.objects.get_or_create(sym=sym)
    # print("Here is the symbol that was found: {}".format(symbol))

    if re.match(r"^[a-zA-Z0-9]+$", sym):
        symbol_created_dict["created_symbols"] = []
        tag = "created_symbols"
        symbol_created_dict["error_symbols"] = []
        for position in positions:
            acct_id = int(position['id'])
            amt = int(position['amount'])
            if not Account.objects.filter(id=acct_id).exists():
                tag = "error_symbols"
                symbol_created_dict[tag].append({"id": str(acct_id), "sym":sym, "msg":"Invalid account number provided"})
                tag = "created_symbols"
            elif amt <= 0:
                tag = "error_symbols"
                symbol_created_dict[tag].append({"id": str(acct_id), "sym":sym, "msg":"Shorting sales are not permitted"})
                tag = "created_symbols"
            else:
                create_position(sym, acct_id, amt)
                symbol_created_dict[tag].append({sym: {"id": str(acct_id)}})
    else:
        symbol_created_dict["error_symbols"]= []
        tag = "error_symbols"
        for position in positions:
            symbol_created_dict[tag].append({"id": position["id"], "sym":sym, "msg":"Invalid symbol format"})
    return symbol_created_dict


"""
Input dictionary will look something like this for create:
{'create': {'account': [{'balance': '1000', 'id': '123456'}],
            'symbol': {'SPY': [{'amount': '100000', 'id': '123456'}] } 
            }
}
"""
def process_requests(requests_dict=None):
    # this is a default value used for testing
    if requests_dict is None:
        requests_dict = create_test_default
    response_dicts = []
    for top_level_node in requests_dict:
        if top_level_node == "create":
            create_request_dict = requests_dict[top_level_node]
            response_dicts.append(process_create_requests(create_request_dict))
        elif top_level_node == "transactions":
            trans_request_dict = requests_dict[top_level_node]
            trans_acct_id = trans_request_dict['id']
            results = {}
            for transaction_type, transactions_of_type in trans_request_dict['children'].items():
                if transaction_type == "order":
                    results["transaction_results"] =  {}
                    transaction_results = results["transaction_results"]
                    for order_transaction in transactions_of_type:
                        sym = order_transaction['sym']
                        amount = int(order_transaction['amount'])
                        limit = float(order_transaction['limit'])
                        print(f"Generating an order with: SYM - {sym} | trans_acct_id - {trans_acct_id} | amount - {amount} | limit - {limit}")
                        try:
                            new_order = generate_order(sym, trans_acct_id, amount, limit)
                            open_order_resp = generate_open_order_resp(new_order)
                            if "opened" not in transaction_results:
                                transaction_results["opened"] = []
                            transaction_results["opened"].append(open_order_resp)
                            with transaction.atomic():
                                find_matching_order(new_order)
                        except Exception as e:
                            if not "error" in transaction_results:
                                transaction_results["error"] = []
                            transaction_results["error"].append({"sym": sym, "limit": str(limit), "amount": str(amount), "msg": str(e)})
                elif transaction_type == "query":
                    results["status"] = []
                    for query_transaction in transactions_of_type:
                        order_id = int(query_transaction['id'])
                        order_status_resp = query_order_with_id(order_id)
                        results["status"].append(order_status_resp)
                elif transaction_type == "cancel":
                    results["canceled"] = []
                    for cancel_transaction in transactions_of_type:
                        order_id = int(cancel_transaction['id'])
                        cancel_resp = cancel_order(order_id)
                        results["canceled"].append(cancel_resp)
                else:
                    raise ValueError(
                        f"Invalid Transaction: Transaction nodes must be specified with 1 or more 'order', 'cancel', or 'query' child nodes; given '{transaction_type}'")
            response_dicts.append(results)

    return response_dicts


def process_create_requests(create_request_dict):
    response_dict = {}
    if "account" in create_request_dict:
        response_dict["created_accounts"] = []
        response_dict["error_accounts"] = []
    if "symbol" in create_request_dict:
        response_dict["created_symbols"] = []
        response_dict["error_symbols"] = []
    for child_key, child_values in create_request_dict.items():
        if child_key == "account":
            for account_entry in child_values:
                account_id = int(account_entry['id'])
                balance = int(account_entry['balance'])
                account_creation_resp = create_account(account_id, balance)
                for sub_dict_key in account_creation_resp:
                    response_dict[sub_dict_key].append(account_creation_resp[sub_dict_key])
        elif child_key == "symbol":
            symbols_to_create_dict = create_request_dict[child_key]
            # if there is not at least one position in this request, then that is an error
            for sym_name, positions in symbols_to_create_dict.items():
                print("Building symbol with sym_name = {} | positions = {}".format(sym_name, positions))
                symbol_creation_resp = create_symbol(sym_name, positions)
                for key in symbol_creation_resp:
                    for sublist in symbol_creation_resp[key]:
                        response_dict[key].append(sublist)
                # temp_list = []
                # response_dict.append(symbol_creation_resp)
        else:
            raise ValueError(
                f"Invalid CREATE: Create order nodes must be specified with 0 or more 'account' or 'symbol' child nodes; given '{child_key}'")
    return_dict = {"create_results": response_dict}
    return return_dict

def print_database_objs():
    accounts = Account.objects.all()
    symbols = Symbol.objects.all()
    positions = Position.objects.all()
    orders = Order.objects.all()
    executed_orders = ExecutedOrder.objects.filter(~Q(shares=0))
    canceled_orders = CanceledOrder.objects.all()
    if symbols:
        print("Here are all the existing symbols:")
        for s in symbols:
            print(f"    {s}")
    if accounts:
        print("\n\nHere are the existing accounts:")
        for a in accounts:
            print(f"    {a}")
    if positions:
        print("\n\nHere are the existing positions:")
        for p in positions:
            print(f"    {p}")
    if orders:
        print("\n\nHere are the existing orders:")
        for o in orders:
            print(f"    {o}")
    if executed_orders:
        print("\n\nHere are the orders that have been executed:")
        for e in executed_orders:
            print(f"    {e}")
    if canceled_orders:
        print("\n\nHere are the orders that have been canceled:")
        for c in canceled_orders:
            print(f"    {c}")


if __name__ == "__main__":
    try:
        process_requests()
    except (django.db.utils.OperationalError):
        # if there is a db issue, then run syncdb and try again
        os.system('python3 manage.py migrate --run-syncdb')
        process_requests()

    # print out the contents of our tables
    print_database_objs()