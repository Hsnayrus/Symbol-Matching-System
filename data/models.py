from django.db import models, transaction
from django.db.models import Sum


class ConcurrentStockObj(models.Model):
    """An abstract Django model object that defines a method necessary for implementation
    of atomic write to DB operations in our models. This object only needs to be
    inherited from in model objects which have methods that modify their state (i.e,
    Account and Order)"""
    def get_self_as_queryset(self):
        return self.__class__.objects.filter(id=self.id)

    class Meta:
        abstract = True


class Symbol(models.Model):
    sym = models.CharField(primary_key=True, unique=True, max_length=5)

    def __str__(self):
        return f"< Symbol :: SYM - {self.sym} >"

class Account(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    balance = models.IntegerField()

    def get_self_as_queryset(self):
        return self.__class__.objects.filter(id=self.id)

    @transaction.atomic()
    def deposit(self, amount):
        obj = self.get_self_as_queryset().select_for_update().get()
        obj.balance += amount
        obj.save()

    @transaction.atomic()
    def withdraw(self, amount):
        obj = self.get_self_as_queryset().select_for_update().get()
        if amount > obj.balance:
            raise ValueError(f"Invalid Withdrawal: Account {obj.id} does not have specified amount (requested {amount} ; own {obj.balance}")
        obj.balance -= amount
        obj.save()

    def get_num_owned_shares_of(self, symbol_obj):
        num_shares = Position.objects.all().filter(sym=symbol_obj, account=self).aggregate(Sum('amount'))['amount__sum']
        if not num_shares:
            return 0
        else:
            return num_shares


    def __str__(self):
        return f"< Account :: ID - {self.id} | " \
               f"BALANCE - {self.balance} >"


class Position(models.Model):
    position_id = models.AutoField(primary_key=True, unique=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    sym = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    amount = models.IntegerField()

    def __str__(self):
        return f"< Position :: POSITION_ID - {self.position_id} | " \
               f"SYM - {self.sym.sym} | " \
               f"ACCOUNT_ID - {self.account.id} | " \
               f"AMOUNT - {self.amount} >"

ORDER_STATUS = (('open', 'open'), ('cancelled', 'cancelled'), ('executed', 'executed'))


class Order(models.Model):
    order_id = models.AutoField(primary_key=True, unique=True)
    sym = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.IntegerField()
    limit = models.FloatField()
    status = models.CharField(default='open', null=False, max_length=50)
    creation_time = models.DateTimeField(auto_now_add=True)


    def get_self_as_queryset(self):
        return self.__class__.objects.filter(order_id=self.order_id)


    def buy_n_shares(self, n_shares):
        print(f"Buying {n_shares} Shares of {self.sym} with order that requires {self.amount} ")
        if self.amount < 0:
            raise RuntimeError("Invalid stock buy: Order requested to buy, but was previously declared as a SELL order")

        if self.amount < n_shares:
            raise ValueError("Invalid Order Buy Update: Given amount is greater than amount that is being purchased (to_buy - {} ; requested - {})".format(self.amount, n_shares))
        self.amount -= n_shares
        self.save()
        if self.amount == 0:
            self.close()


    def sell_n_shares(self, n_shares):
        if self.amount > 0:
            raise RuntimeError("Invalid stock sell: Order requested to sell, but was previously declared as a BUY order")
        # to be used when adding shares
        if abs(self.amount) < n_shares:
            raise ValueError("Invalid Order Sell Update: Given amount is greater than amount that is being sold (to_sell - {} ; requested - {})".format(self.amount, n_shares))
        self.amount += n_shares
        self.save()
        if self.amount == 0:
            self.close()


    def close(self):
        self.status = 'closed'
        self.save()


    def cancel(self):
        self.status = 'canceled'
        self.save()
        canceled_order = CanceledOrder(order=self, shares=self.amount)
        canceled_order.save()


    def __str__(self):
        return f"< Order :: ORDER_ID - {self.order_id} " \
               f"| SYM - {self.sym.sym} | " \
               f"ACCOUNT_ID - {self.account.id} | " \
               f"AMOUNT - {self.amount} | " \
               f"LIMIT - {self.limit} | " \
               f"STATUS - {self.status} >"


class CanceledOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    shares = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"< CanceledOrder :: ORDER_ID - {self.order.order_id} " \
               f"| SHARES - {self.shares} " \
               f"| TIME - {self.time.timestamp()} >"

class ExecutedOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    shares = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)
    sale_price = models.FloatField()

    def __str__(self):
        return f"< ExecutedOrder :: ORDER_ID - {self.order.order_id} " \
               f"| SHARES - {self.shares} " \
               f"| TIME - {self.time.timestamp()} " \
               f"| SALE_PRICE - {self.sale_price} >"