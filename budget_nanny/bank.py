import decimal
import itertools
import os
from datetime import datetime

import xlrd

BANK_ACCOUNT_DEBIT = 'debit'
BANK_ACCOUNT_CREDIT = 'credit'

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
                print('Ignoring row {} "{}", because it does not start with a date.'.format(
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
