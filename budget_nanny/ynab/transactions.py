from dataclasses import dataclass


@dataclass
class YnabTransaction:
    account_id: str
    date: str
    amount: int
    payee_id: str
    payee_name: str
    memo: str
    import_id: str = None
    category_id: str = None


def ynab_transactions_encoder(obj):
    if isinstance(obj, YnabTransaction):
         return obj.__dict__
    raise TypeError(repr(obj) + ' is not JSON Serializable')
