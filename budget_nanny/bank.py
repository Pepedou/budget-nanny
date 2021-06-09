import decimal
import itertools
import logging
import os
from datetime import datetime

import xlrd

_logger = logging.getLogger(__name__)

BANK_ACCOUNT_DEBIT = 'BBVA Nómina'
BANK_ACCOUNT_CREDIT = 'BBVA Platino'

ACCOUNT_STATEMENTS = {
    BANK_ACCOUNT_DEBIT: os.path.expanduser('~/Downloads/movimientos.xlsx'),
    BANK_ACCOUNT_CREDIT: os.path.expanduser('~/Downloads/descarga.xlsx'),
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
                transaction_date = datetime.strptime(sheet.cell_value(i, 0), '%d/%m/%Y')
            except ValueError:
                _logger.debug('Ignoring row {} "{}", because it does not start with a date.'.format(
                    i + 1,
                    sheet.cell_value(i, 0))
                )
                continue

            payee = sheet.cell_value(i, 1)
            outflow_string = str(sheet.cell_value(i, 2)).strip('-').replace(',', '') or 0
            _logger.debug('Outflow', outflow_string)
            outflow = decimal.Decimal(outflow_string) or None

            inflow_string = str(sheet.cell_value(i, 3)).strip('-').replace(',', '') or 0
            _logger.debug('Inflow', inflow_string)
            inflow = decimal.Decimal(inflow_string) or None

            transactions.append({
                'account': account,
                'date': transaction_date,
                'payee': payee,
                'outflow': outflow,
                'inflow': inflow,
            })

    return transactions
