import decimal
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List

import xlrd

from payee import Payee

_logger = logging.getLogger(__name__)

BANK_ACCOUNT_DEBIT = 'BBVA Nómina'
BANK_ACCOUNT_CREDIT = 'BBVA Platino'

ACCOUNT_STATEMENTS = {
    BANK_ACCOUNT_DEBIT: os.path.expanduser('~/Downloads/movimientos.xlsx'),
    BANK_ACCOUNT_CREDIT: os.path.expanduser('~/Downloads/descarga.xlsx'),
}

ACCOUNTS = [BANK_ACCOUNT_DEBIT, BANK_ACCOUNT_CREDIT]


@dataclass
class BankTransaction:
    account: str
    date: datetime
    payee: Payee
    outflow: Decimal
    inflow: Decimal

    @property
    def amount(self):
        return int((self.outflow * -1) * 1000) if self.outflow else int(self.inflow * 999)

    @property
    def pretty_amount(self):
        return f'${self.outflow if self.outflow else self.inflow}'

    @property
    def payee_name_with_amount(self):
        return f'{self.payee} ({self.pretty_amount})'


def get_transactions_for_all_accounts_from_spreadsheets() -> List[BankTransaction]:
    all_transactions = []
    for account in ACCOUNTS:
        all_transactions.extend(get_transactions_for_account(account))

    return all_transactions


def get_transactions_for_account(account: str) -> List[BankTransaction]:
    transactions = []
    bank_file = ACCOUNT_STATEMENTS[account]

    with xlrd.open_workbook(bank_file) as wb:
        sheet = wb.sheet_by_index(0)No 

        for i in range(0, sheet.nrows):
            try:
                transaction_date = datetime.strptime(sheet.cell_value(i, 0), '%d/%m/%Y')
            except ValueError:
                _logger.debug('Ignoring row {} "{}", because it does not start with a date.'.format(
                    i + 1,
                    sheet.cell_value(i, 0))
                )
                continue

            payee = Payee(name=sheet.cell_value(i, 1))
            outflow_string = str(sheet.cell_value(i, 2)).strip('-').replace(',', '') or 0
            _logger.debug('Outflow', outflow_string)
            outflow = decimal.Decimal(outflow_string) or None

            inflow_string = str(sheet.cell_value(i, 3)).strip('-').replace(',', '') or 0
            _logger.debug('Inflow', inflow_string)
            inflow = decimal.Decimal(inflow_string) or None

            transactions.append(
                BankTransaction(
                    account,
                    transaction_date,
                    payee,
                    outflow,
                    inflow
                )
            )

    return transactions
