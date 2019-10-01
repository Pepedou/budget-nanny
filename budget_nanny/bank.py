import decimal
import itertools
import logging
import os
from datetime import datetime

import xlrd

_logger = logging.getLogger(__name__)

BANK_ACCOUNT_DEBIT = 'Bancomer Nómina'
BANK_ACCOUNT_CREDIT = 'Bancomer Platino'

ACCOUNT_STATEMENTS = {
    BANK_ACCOUNT_DEBIT: os.path.expanduser('~/Downloads/debito.xlsx'),
    BANK_ACCOUNT_CREDIT: os.path.expanduser('~/Downloads/credito.xlsx'),
}

ACCOUNTS = [BANK_ACCOUNT_DEBIT, BANK_ACCOUNT_CREDIT]


def get_transactions_for_all_accounts():
    return itertools.chain.from_iterable(map(get_transactions_for_account, ACCOUNTS))


def get_transactions_for_account(account):
    transactions = []
    bank_file = ACCOUNT_STATEMENTS[account]

    with xlrd.open_workbook(bank_file) as wb:
        sheet = wb.sheet_by_index(0)

        for i in range(0, sheet.nrows):
            try:
                my_date = datetime.strptime(sheet.cell_value(i, 0), '%d/%m/%Y')
            except ValueError:
                _logger.debug('Ignoring row {} "{}", because it does not start with a date.'.format(
                    i + 1,
                    sheet.cell_value(i, 0))
                )
                continue

            payee = sheet.cell_value(i, 1)
            outflow = decimal.Decimal(str(sheet.cell_value(i, 2)).strip('-') or 0) or None
            inflow = decimal.Decimal(str(sheet.cell_value(i, 3)).strip('-') or 0) or None

            transactions.append({
                'account': account,
                'date': my_date,
                'payee': payee,
                'outflow': outflow,
                'inflow': inflow,
            })

    return transactions
