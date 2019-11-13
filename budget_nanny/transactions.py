import collections
from dataclasses import dataclass


@dataclass
class YNABTransaction:
    account_id: str
    date: str
    amount: int
    payee_id: str
    payee_name: str
    memo: str

    import_id: str = None
    category_id: str = None

    import_counter = collections.Counter()

    def __post_init__(self):
        self._set_import_id()

    def _set_import_id(self):
        """
        Transactions imported through File Based Import or Direct Import (not through the API) are assigned an import_id in
        the format: 'YNAB:[milliunit_amount]:[iso_date]:[occurrence]'. For example, a transaction dated 2015-12-30 in the
        amount of -$294.23 USD would have an import_id of 'YNAB:-294230:2015-12-30:1’. If a second transaction on the same
        account was imported and had the same date and same amount, its import_id would be 'YNAB:-294230:2015-12-30:2’.
        """
        if self.import_id:
            return

        key_for_counter = (
            self.account_id,
            self.date,
            self.amount,
        )

        self.import_counter.update([key_for_counter])
        counts_for_this_transaction = self.import_counter[key_for_counter]

        self.import_id = f'YNAB:{self.amount}:{self.date}:{counts_for_this_transaction}:a'

    def __str__(self):
        return f'{self.import_id} "{self.payee_name}" ${self.amount / 1000}'
