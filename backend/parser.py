"""
M-Pesa PDF Statement Parser
Uses pdfplumber to extract transaction rows from Safaricom M-Pesa statement PDFs.
Returns structured transaction data for the SpinMobile scorer.
"""
import re
import json
from datetime import datetime
from typing import Optional

try:
    import pdfplumber
    PDFPLUMBER_OK = True
except ImportError:
    PDFPLUMBER_OK = False
    print("[PARSER] pdfplumber not installed — mock mode active")


# Typical M-Pesa statement column patterns
MPESA_DATE_PATTERN   = re.compile(r'\d{1,2}/\d{1,2}/\d{4}')
MPESA_AMOUNT_PATTERN = re.compile(r'[\d,]+\.\d{2}')
CREDIT_KEYWORDS = ['received', 'deposit', 'salary', 'reversal', 'fuliza received', 'agent deposit']
DEBIT_KEYWORDS  = ['sent', 'withdraw', 'payment', 'airtime', 'paybill', 'buy goods', 'fuliza']


def parse_mpesa_pdf(pdf_path: str) -> dict:
    """
    Parse an M-Pesa statement PDF and return structured summary.
    Falls back to mock data if pdfplumber unavailable or PDF unreadable.
    """
    if not PDFPLUMBER_OK:
        return _mock_parse(pdf_path)

    try:
        return _real_parse(pdf_path)
    except Exception as e:
        print(f"[PARSER] PDF parse error: {e} — using mock data")
        return _mock_parse(pdf_path)


def _real_parse(pdf_path: str) -> dict:
    transactions = []
    raw_text = ''

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            raw_text += text + '\n'
            table = page.extract_table()
            if table:
                for row in table:
                    if not row or len(row) < 4:
                        continue
                    tx = _parse_row(row)
                    if tx:
                        transactions.append(tx)

    # Fallback: parse raw text lines if no table found
    if not transactions:
        transactions = _parse_text_lines(raw_text)

    return _summarise(transactions, pdf_path)


def _parse_row(row: list) -> Optional[dict]:
    """Try to extract a transaction from a table row."""
    row_str = ' '.join(str(c) for c in row if c)
    if not MPESA_DATE_PATTERN.search(row_str):
        return None

    amounts = MPESA_AMOUNT_PATTERN.findall(row_str)
    if not amounts:
        return None

    row_lower = row_str.lower()
    tx_type = 'credit' if any(k in row_lower for k in CREDIT_KEYWORDS) else 'debit'
    amount = float(amounts[0].replace(',', ''))

    return {
        'raw':    row_str,
        'type':   tx_type,
        'amount': amount,
    }


def _parse_text_lines(text: str) -> list:
    transactions = []
    for line in text.split('\n'):
        if not MPESA_DATE_PATTERN.search(line):
            continue
        amounts = MPESA_AMOUNT_PATTERN.findall(line)
        if not amounts:
            continue
        line_lower = line.lower()
        tx_type = 'credit' if any(k in line_lower for k in CREDIT_KEYWORDS) else 'debit'
        amount = float(amounts[0].replace(',', ''))
        transactions.append({'raw': line, 'type': tx_type, 'amount': amount})
    return transactions


def _summarise(transactions: list, pdf_path: str) -> dict:
    if not transactions:
        return _mock_parse(pdf_path)

    credits = [t['amount'] for t in transactions if t['type'] == 'credit']
    debits  = [t['amount'] for t in transactions if t['type'] == 'debit']

    total_in  = sum(credits)
    total_out = sum(debits)
    count     = len(transactions)

    avg_credit = total_in  / len(credits) if credits else 0
    avg_debit  = total_out / len(debits)  if debits  else 0

    return {
        'parsed':        True,
        'pdf_path':      pdf_path,
        'tx_count':      count,
        'credit_count':  len(credits),
        'debit_count':   len(debits),
        'total_in':      round(total_in, 2),
        'total_out':     round(total_out, 2),
        'avg_credit':    round(avg_credit, 2),
        'avg_debit':     round(avg_debit, 2),
        'net_flow':      round(total_in - total_out, 2),
        'utilisation':   round(total_out / total_in, 4) if total_in > 0 else 1.0,
        'parsed_at':     datetime.now().isoformat(),
    }


def _mock_parse(pdf_path: str) -> dict:
    """Return plausible mock data when real parsing is unavailable."""
    import random
    random.seed(hash(pdf_path) % 9999)
    tx_count  = random.randint(45, 180)
    total_in  = round(random.uniform(30000, 250000), 2)
    total_out = round(total_in * random.uniform(0.5, 0.95), 2)
    return {
        'parsed':       False,
        'mock':         True,
        'pdf_path':     pdf_path,
        'tx_count':     tx_count,
        'credit_count': int(tx_count * 0.4),
        'debit_count':  int(tx_count * 0.6),
        'total_in':     total_in,
        'total_out':    total_out,
        'avg_credit':   round(total_in  / max(int(tx_count * 0.4), 1), 2),
        'avg_debit':    round(total_out / max(int(tx_count * 0.6), 1), 2),
        'net_flow':     round(total_in - total_out, 2),
        'utilisation':  round(total_out / total_in, 4) if total_in > 0 else 0.8,
        'parsed_at':    datetime.now().isoformat(),
    }


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else 'test.pdf'
    result = parse_mpesa_pdf(path)
    print(json.dumps(result, indent=2))
