"""
NEXUS Accounting - General Ledger Module
Double-entry bookkeeping, chart of accounts, journal entries.
Rival to QuickBooks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
from decimal import Decimal


class AccountType(Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class AccountSubtype(Enum):
    # Assets
    CASH = "cash"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    INVENTORY = "inventory"
    FIXED_ASSETS = "fixed_assets"

    # Liabilities
    ACCOUNTS_PAYABLE = "accounts_payable"
    CREDIT_CARD = "credit_card"
    LOANS = "loans"

    # Equity
    OWNERS_EQUITY = "owners_equity"
    RETAINED_EARNINGS = "retained_earnings"

    # Revenue
    SALES = "sales"
    SERVICE_REVENUE = "service_revenue"

    # Expenses
    COST_OF_GOODS_SOLD = "cogs"
    OPERATING_EXPENSE = "operating_expense"


@dataclass
class Account:
    """Chart of accounts entry"""
    id: str
    account_number: str
    name: str
    account_type: AccountType
    account_subtype: AccountSubtype

    # Balance
    balance: Decimal = Decimal("0.00")
    opening_balance: Decimal = Decimal("0.00")

    # Settings
    is_active: bool = True
    is_system: bool = False  # System accounts cannot be deleted
    parent_id: Optional[str] = None

    # Metadata
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class JournalEntry:
    """Journal entry with debits and credits"""
    id: str
    entry_number: str
    date: datetime
    description: str

    # Lines (debits and credits)
    lines: List['JournalLine'] = field(default_factory=list)

    # Status
    is_posted: bool = False
    is_reversed: bool = False

    # Metadata
    reference: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    posted_at: Optional[datetime] = None


@dataclass
class JournalLine:
    """Individual line in journal entry"""
    id: str
    account_id: str
    account_name: str
    debit: Decimal = Decimal("0.00")
    credit: Decimal = Decimal("0.00")
    description: str = ""


class GeneralLedger:
    """General ledger management"""

    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.journal_entries: Dict[str, JournalEntry] = {}
        self.entry_counter = 1000
        self._setup_default_accounts()

    def _setup_default_accounts(self):
        """Setup default chart of accounts"""
        default_accounts = [
            ("1000", "Cash", AccountType.ASSET, AccountSubtype.CASH),
            ("1200", "Accounts Receivable", AccountType.ASSET, AccountSubtype.ACCOUNTS_RECEIVABLE),
            ("1300", "Inventory", AccountType.ASSET, AccountSubtype.INVENTORY),
            ("2000", "Accounts Payable", AccountType.LIABILITY, AccountSubtype.ACCOUNTS_PAYABLE),
            ("3000", "Owner's Equity", AccountType.EQUITY, AccountSubtype.OWNERS_EQUITY),
            ("4000", "Sales Revenue", AccountType.REVENUE, AccountSubtype.SALES),
            ("5000", "Cost of Goods Sold", AccountType.EXPENSE, AccountSubtype.COST_OF_GOODS_SOLD),
            ("6000", "Operating Expenses", AccountType.EXPENSE, AccountSubtype.OPERATING_EXPENSE),
        ]

        for num, name, acc_type, subtype in default_accounts:
            self.create_account(num, name, acc_type, subtype, is_system=True)

    def create_account(
        self,
        account_number: str,
        name: str,
        account_type: AccountType,
        account_subtype: AccountSubtype,
        **kwargs
    ) -> Account:
        """Create account"""
        import uuid
        account = Account(
            id=str(uuid.uuid4()),
            account_number=account_number,
            name=name,
            account_type=account_type,
            account_subtype=account_subtype,
            **kwargs
        )
        self.accounts[account.id] = account
        return account

    def create_journal_entry(
        self,
        date: datetime,
        description: str,
        lines: List[Dict],
        **kwargs
    ) -> Optional[JournalEntry]:
        """Create journal entry"""
        import uuid

        # Validate double-entry (debits = credits)
        total_debits = sum(Decimal(str(line.get('debit', 0))) for line in lines)
        total_credits = sum(Decimal(str(line.get('credit', 0))) for line in lines)

        if total_debits != total_credits:
            raise ValueError(f"Debits ({total_debits}) must equal credits ({total_credits})")

        entry_number = f"JE-{self.entry_counter}"
        self.entry_counter += 1

        # Create journal lines
        journal_lines = []
        for line_data in lines:
            account = self.accounts.get(line_data['account_id'])
            if not account:
                raise ValueError(f"Account {line_data['account_id']} not found")

            line = JournalLine(
                id=str(uuid.uuid4()),
                account_id=line_data['account_id'],
                account_name=account.name,
                debit=Decimal(str(line_data.get('debit', 0))),
                credit=Decimal(str(line_data.get('credit', 0))),
                description=line_data.get('description', '')
            )
            journal_lines.append(line)

        entry = JournalEntry(
            id=str(uuid.uuid4()),
            entry_number=entry_number,
            date=date,
            description=description,
            lines=journal_lines,
            **kwargs
        )

        self.journal_entries[entry.id] = entry
        return entry

    def post_entry(self, entry_id: str) -> bool:
        """Post journal entry to ledger"""
        entry = self.journal_entries.get(entry_id)
        if not entry or entry.is_posted:
            return False

        # Update account balances
        for line in entry.lines:
            account = self.accounts[line.account_id]

            if line.debit > 0:
                if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                    account.balance += line.debit
                else:
                    account.balance -= line.debit

            if line.credit > 0:
                if account.account_type in [AccountType.LIABILITY, AccountType.EQUITY, AccountType.REVENUE]:
                    account.balance += line.credit
                else:
                    account.balance -= line.credit

        entry.is_posted = True
        entry.posted_at = datetime.now()
        return True

    def get_account_balance(self, account_id: str) -> Decimal:
        """Get account balance"""
        account = self.accounts.get(account_id)
        return account.balance if account else Decimal("0.00")

    def get_trial_balance(self) -> Dict[str, Any]:
        """Generate trial balance"""
        debits = Decimal("0.00")
        credits = Decimal("0.00")
        accounts = []

        for account in self.accounts.values():
            if not account.is_active:
                continue

            # Determine if debit or credit balance
            if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                debit_balance = account.balance
                credit_balance = Decimal("0.00")
                debits += debit_balance
            else:
                debit_balance = Decimal("0.00")
                credit_balance = account.balance
                credits += credit_balance

            accounts.append({
                "account_number": account.account_number,
                "name": account.name,
                "type": account.account_type.value,
                "debit": float(debit_balance),
                "credit": float(credit_balance)
            })

        return {
            "accounts": accounts,
            "total_debits": float(debits),
            "total_credits": float(credits),
            "balanced": debits == credits
        }


if __name__ == "__main__":
    ledger = GeneralLedger()

    # Create journal entry
    entry = ledger.create_journal_entry(
        date=datetime.now(),
        description="Customer payment received",
        lines=[
            {"account_id": list(ledger.accounts.values())[0].id, "debit": 1000, "description": "Cash"},
            {"account_id": list(ledger.accounts.values())[1].id, "credit": 1000, "description": "AR"}
        ]
    )

    ledger.post_entry(entry.id)

    trial_balance = ledger.get_trial_balance()
    print(f"Trial Balance: {trial_balance['balanced']}")
    print(f"Total Debits: ${trial_balance['total_debits']:.2f}")
