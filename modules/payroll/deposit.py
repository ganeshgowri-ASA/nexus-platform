"""
Enterprise Direct Deposit System
Handles ACH payments, multi-account splits, bank validation, and payment processing
Production-ready with NACHA file generation and banking integrations
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import logging
import re
from uuid import uuid4

logger = logging.getLogger(__name__)


class AccountType(Enum):
    """Bank account types"""
    CHECKING = "checking"
    SAVINGS = "savings"
    LOAN = "loan"


class DepositType(Enum):
    """Direct deposit allocation types"""
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    REMAINDER = "remainder"


class TransactionStatus(Enum):
    """ACH transaction status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    RETURNED = "returned"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReturnCode(Enum):
    """NACHA return codes"""
    R01 = "Insufficient Funds"
    R02 = "Account Closed"
    R03 = "No Account/Unable to Locate"
    R04 = "Invalid Account Number"
    R05 = "Unauthorized Debit"
    R06 = "Returned per ODFI Request"
    R07 = "Authorization Revoked"
    R08 = "Payment Stopped"
    R09 = "Uncollected Funds"
    R10 = "Customer Advises Not Authorized"
    R11 = "Check Truncation Entry Return"
    R12 = "Account Sold to Another DFI"
    R13 = "Invalid ACH Routing Number"
    R14 = "Representative Payee Deceased"
    R15 = "Beneficiary or Account Holder Deceased"
    R16 = "Account Frozen"
    R17 = "File Record Edit Criteria"
    R20 = "Non-Transaction Account"
    R29 = "Corporate Customer Advises Not Authorized"


@dataclass
class BankAccount:
    """Bank account information"""
    id: str = field(default_factory=lambda: str(uuid4()))
    account_holder_name: str = ""
    routing_number: str = ""  # 9-digit ABA routing number
    account_number: str = ""
    account_type: AccountType = AccountType.CHECKING
    bank_name: str = ""
    verified: bool = False
    verification_date: Optional[datetime] = None
    prenote_sent: bool = False  # Pre-notification sent
    prenote_date: Optional[datetime] = None
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate account information"""
        self.routing_number = self.routing_number.strip()
        self.account_number = self.account_number.strip()

    @property
    def last4(self) -> str:
        """Get last 4 digits of account number"""
        return self.account_number[-4:] if len(self.account_number) >= 4 else self.account_number

    @property
    def masked_account(self) -> str:
        """Get masked account number"""
        if len(self.account_number) <= 4:
            return "****"
        return f"****{self.last4}"


@dataclass
class DepositAllocation:
    """Direct deposit allocation configuration"""
    id: str = field(default_factory=lambda: str(uuid4()))
    bank_account_id: str = ""
    deposit_type: DepositType = DepositType.PERCENTAGE
    amount: Decimal = Decimal("0")  # Dollar amount or percentage
    priority: int = 0  # Allocation order (lower = higher priority)
    active: bool = True

    def calculate_amount(self, net_pay: Decimal, allocated_so_far: Decimal) -> Decimal:
        """Calculate allocation amount"""
        if not self.active:
            return Decimal("0")

        if self.deposit_type == DepositType.FIXED_AMOUNT:
            # Fixed dollar amount
            remaining = net_pay - allocated_so_far
            return min(self.amount, remaining)

        elif self.deposit_type == DepositType.PERCENTAGE:
            # Percentage of net pay
            calculated = net_pay * (self.amount / Decimal("100"))
            remaining = net_pay - allocated_so_far
            return min(calculated, remaining)

        elif self.deposit_type == DepositType.REMAINDER:
            # Everything that's left
            return net_pay - allocated_so_far

        return Decimal("0")


@dataclass
class ACHTransaction:
    """Individual ACH transaction"""
    id: str = field(default_factory=lambda: str(uuid4()))
    transaction_code: str = "22"  # 22=Checking Credit, 32=Savings Credit
    receiving_dfi_routing: str = ""
    receiving_dfi_account: str = ""
    amount: Decimal = Decimal("0")
    individual_id: str = ""  # Employee ID
    individual_name: str = ""
    discretionary_data: str = ""
    addenda_indicator: str = "0"
    trace_number: str = ""

    # Status tracking
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    return_code: Optional[ReturnCode] = None
    return_date: Optional[datetime] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def format_for_nacha(self, sequence_number: int) -> str:
        """Format transaction as NACHA Entry Detail Record"""
        # NACHA file format is very specific - fixed width fields

        # Amount in cents, no decimal point, 10 digits
        amount_cents = int(self.amount * 100)
        amount_str = str(amount_cents).zfill(10)

        # DFI Account Number - 17 characters, left-justified, space-filled
        account_str = self.receiving_dfi_account.ljust(17)[:17]

        # Individual Name - 22 characters
        name_str = self.individual_name.ljust(22)[:22]

        # Individual ID - 15 characters
        id_str = self.individual_id.ljust(15)[:15]

        # Trace number - 15 characters (8-digit routing + 7-digit sequence)
        trace_str = f"{self.receiving_dfi_routing[:8]}{str(sequence_number).zfill(7)}"

        # Build Entry Detail Record (94 characters)
        record = (
            "6"  # Record Type Code
            f"{self.transaction_code}"  # Transaction Code
            f"{self.receiving_dfi_routing[:8]}"  # Receiving DFI Routing (first 8 digits)
            f"{self.receiving_dfi_routing[8]}"  # Check Digit (9th digit)
            f"{account_str}"  # DFI Account Number
            f"{amount_str}"  # Amount
            f"{id_str}"  # Individual ID
            f"{name_str}"  # Individual Name
            f"{self.discretionary_data.ljust(2)[:2]}"  # Discretionary Data
            f"{self.addenda_indicator}"  # Addenda Record Indicator
            f"{trace_str}"  # Trace Number
        )

        return record


@dataclass
class ACHBatch:
    """ACH batch for NACHA file"""
    id: str = field(default_factory=lambda: str(uuid4()))
    batch_number: int = 1
    company_name: str = ""
    company_id: str = ""  # Tax ID
    company_entry_description: str = "PAYROLL"
    effective_date: date = field(default_factory=date.today)
    odfi_routing: str = ""  # Originating DFI routing number

    transactions: List[ACHTransaction] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_transaction(self, transaction: ACHTransaction) -> None:
        """Add transaction to batch"""
        self.transactions.append(transaction)

    def get_total_amount(self) -> Decimal:
        """Get total batch amount"""
        return sum(t.amount for t in self.transactions)

    def get_transaction_count(self) -> int:
        """Get number of transactions"""
        return len(self.transactions)

    def format_batch_header(self) -> str:
        """Format NACHA Batch Header Record"""
        # Service Class Code: 200 = Mixed, 220 = Credits only, 225 = Debits only
        service_class = "220"  # Credits only for payroll

        # Company Entry Description - 10 characters
        entry_desc = self.company_entry_description.ljust(10)[:10]

        # Effective date - YYMMDD
        effective_date_str = self.effective_date.strftime("%y%m%d")

        # Originator Status Code - 1 = originator
        originator_status = "1"

        # Company Name - 16 characters
        company_name_str = self.company_name.ljust(16)[:16]

        # Company ID (Tax ID) - 10 characters
        company_id_str = self.company_id.ljust(10)[:10]

        record = (
            "5"  # Record Type Code
            f"{service_class}"  # Service Class Code
            f"{company_name_str}"  # Company Name
            f"{''.ljust(20)}"  # Company Discretionary Data
            f"{company_id_str}"  # Company Identification
            "PPD"  # Standard Entry Class Code (PPD = Prearranged Payment and Deposit)
            f"{entry_desc}"  # Company Entry Description
            f"{''.ljust(6)}"  # Company Descriptive Date
            f"{effective_date_str}"  # Effective Entry Date
            "   "  # Settlement Date (Julian, filled by ACH operator)
            f"{originator_status}"  # Originator Status Code
            f"{self.odfi_routing[:8]}"  # Originating DFI Identification
            f"{str(self.batch_number).zfill(7)}"  # Batch Number
        )

        return record

    def format_batch_control(self) -> str:
        """Format NACHA Batch Control Record"""
        service_class = "220"

        # Entry/Addenda Count
        entry_count = str(len(self.transactions)).zfill(6)

        # Entry Hash - sum of first 8 digits of all routing numbers
        entry_hash = sum(int(t.receiving_dfi_routing[:8]) for t in self.transactions)
        entry_hash_str = str(entry_hash)[-10:].zfill(10)  # Last 10 digits

        # Total Debit/Credit amounts in cents
        total_debit = "000000000000"  # No debits in payroll
        total_credit = str(int(self.get_total_amount() * 100)).zfill(12)

        record = (
            "8"  # Record Type Code
            f"{service_class}"  # Service Class Code
            f"{entry_count}"  # Entry/Addenda Count
            f"{entry_hash_str}"  # Entry Hash
            f"{total_debit}"  # Total Debit Entry Dollar Amount
            f"{total_credit}"  # Total Credit Entry Dollar Amount
            f"{self.company_id.ljust(10)[:10]}"  # Company Identification
            "".ljust(19)  # Message Authentication Code
            "".ljust(6)  # Reserved
            f"{self.odfi_routing[:8]}"  # Originating DFI Identification
            f"{str(self.batch_number).zfill(7)}"  # Batch Number
        )

        return record


class BankValidator:
    """Bank account validation utilities"""

    @staticmethod
    def validate_routing_number(routing: str) -> Tuple[bool, Optional[str]]:
        """
        Validate ABA routing number using checksum algorithm
        Returns: (is_valid, error_message)
        """
        # Remove any non-digits
        routing = re.sub(r'\D', '', routing)

        # Must be exactly 9 digits
        if len(routing) != 9:
            return False, "Routing number must be 9 digits"

        # Convert to integers
        digits = [int(d) for d in routing]

        # Checksum algorithm (modulus 10)
        checksum = (
            3 * (digits[0] + digits[3] + digits[6]) +
            7 * (digits[1] + digits[4] + digits[7]) +
            1 * (digits[2] + digits[5] + digits[8])
        )

        if checksum % 10 != 0:
            return False, "Invalid routing number checksum"

        return True, None

    @staticmethod
    def validate_account_number(account: str) -> Tuple[bool, Optional[str]]:
        """
        Basic account number validation
        Returns: (is_valid, error_message)
        """
        # Remove any non-alphanumeric characters
        account = re.sub(r'[^a-zA-Z0-9]', '', account)

        # Must be between 4 and 17 characters
        if len(account) < 4:
            return False, "Account number too short"

        if len(account) > 17:
            return False, "Account number too long"

        return True, None

    @staticmethod
    def mask_account_number(account: str) -> str:
        """Mask account number for display"""
        if len(account) <= 4:
            return "****"
        return f"****{account[-4:]}"


class DirectDepositProcessor:
    """
    Direct deposit processing engine
    Handles ACH file generation, bank validation, and payment distribution
    """

    def __init__(
        self,
        company_name: str,
        company_tax_id: str,
        odfi_routing: str
    ):
        self.company_name = company_name
        self.company_tax_id = company_tax_id
        self.odfi_routing = odfi_routing  # Originating bank routing number

        self.bank_accounts: Dict[str, BankAccount] = {}
        self.deposit_allocations: Dict[str, List[DepositAllocation]] = {}  # employee_id -> allocations
        self.ach_batches: List[ACHBatch] = []
        self.validator = BankValidator()

    def register_bank_account(self, account: BankAccount) -> Tuple[bool, Optional[str]]:
        """
        Register and validate a bank account
        Returns: (success, error_message)
        """
        # Validate routing number
        valid, error = self.validator.validate_routing_number(account.routing_number)
        if not valid:
            return False, error

        # Validate account number
        valid, error = self.validator.validate_account_number(account.account_number)
        if not valid:
            return False, error

        # Store account
        self.bank_accounts[account.id] = account

        logger.info(
            f"Registered bank account {account.id}: "
            f"{account.bank_name} {account.masked_account}"
        )

        return True, None

    def add_deposit_allocation(
        self,
        employee_id: str,
        allocation: DepositAllocation
    ) -> bool:
        """Add direct deposit allocation for employee"""
        # Verify bank account exists
        if allocation.bank_account_id not in self.bank_accounts:
            logger.error(f"Bank account {allocation.bank_account_id} not found")
            return False

        if employee_id not in self.deposit_allocations:
            self.deposit_allocations[employee_id] = []

        self.deposit_allocations[employee_id].append(allocation)

        logger.info(
            f"Added deposit allocation for employee {employee_id}: "
            f"{allocation.deposit_type.value} - {allocation.amount}"
        )

        return True

    def calculate_deposit_distribution(
        self,
        employee_id: str,
        net_pay: Decimal
    ) -> List[Tuple[BankAccount, Decimal]]:
        """
        Calculate how net pay should be distributed across accounts
        Returns: List of (BankAccount, amount) tuples
        """
        allocations = self.deposit_allocations.get(employee_id, [])

        if not allocations:
            # No allocations configured
            return []

        # Sort allocations by priority (lower number = higher priority)
        sorted_allocations = sorted(allocations, key=lambda a: (a.priority, a.id))

        distribution = []
        allocated_total = Decimal("0")

        for allocation in sorted_allocations:
            if not allocation.active:
                continue

            # Calculate amount for this allocation
            amount = allocation.calculate_amount(net_pay, allocated_total)

            if amount > 0:
                bank_account = self.bank_accounts.get(allocation.bank_account_id)
                if bank_account and bank_account.active:
                    distribution.append((bank_account, amount))
                    allocated_total += amount

            # If we've allocated everything, stop
            if allocated_total >= net_pay:
                break

        # Verify we allocated the full amount
        if allocated_total != net_pay:
            logger.warning(
                f"Deposit distribution mismatch for employee {employee_id}: "
                f"allocated ${allocated_total}, net pay ${net_pay}"
            )

        return distribution

    def create_ach_batch(
        self,
        effective_date: Optional[date] = None,
        batch_number: int = 1
    ) -> ACHBatch:
        """Create new ACH batch"""
        if effective_date is None:
            # Default to next business day
            effective_date = date.today() + timedelta(days=1)

        batch = ACHBatch(
            batch_number=batch_number,
            company_name=self.company_name,
            company_id=self.company_tax_id,
            effective_date=effective_date,
            odfi_routing=self.odfi_routing
        )

        self.ach_batches.append(batch)
        return batch

    def process_direct_deposit(
        self,
        employee_id: str,
        employee_name: str,
        net_pay: Decimal,
        batch: ACHBatch
    ) -> List[ACHTransaction]:
        """
        Process direct deposit for an employee
        Creates ACH transactions and adds to batch
        """
        # Calculate distribution
        distribution = self.calculate_deposit_distribution(employee_id, net_pay)

        if not distribution:
            logger.warning(f"No deposit allocations for employee {employee_id}")
            return []

        transactions = []

        for bank_account, amount in distribution:
            # Determine transaction code
            if bank_account.account_type == AccountType.CHECKING:
                transaction_code = "22"  # Checking Credit
            elif bank_account.account_type == AccountType.SAVINGS:
                transaction_code = "32"  # Savings Credit
            else:
                transaction_code = "22"  # Default to checking

            # Create ACH transaction
            transaction = ACHTransaction(
                transaction_code=transaction_code,
                receiving_dfi_routing=bank_account.routing_number,
                receiving_dfi_account=bank_account.account_number,
                amount=amount,
                individual_id=employee_id,
                individual_name=employee_name[:22],  # Max 22 chars
                status=TransactionStatus.PENDING
            )

            # Add to batch
            batch.add_transaction(transaction)
            transactions.append(transaction)

            logger.info(
                f"Created ACH transaction: {employee_name} -> "
                f"{bank_account.masked_account} ${amount}"
            )

        return transactions

    def generate_nacha_file(self, batch: ACHBatch) -> str:
        """
        Generate NACHA ACH file
        Returns file content as string
        """
        lines = []

        # File Header Record
        file_header = self._generate_file_header(batch)
        lines.append(file_header)

        # Batch Header Record
        batch_header = batch.format_batch_header()
        lines.append(batch_header)

        # Entry Detail Records
        for idx, transaction in enumerate(batch.transactions, start=1):
            entry_detail = transaction.format_for_nacha(idx)
            lines.append(entry_detail)

        # Batch Control Record
        batch_control = batch.format_batch_control()
        lines.append(batch_control)

        # File Control Record
        file_control = self._generate_file_control(batch, len(batch.transactions))
        lines.append(file_control)

        # Padding records (files must be in blocks of 10)
        total_records = len(lines)
        records_needed = ((total_records // 10) + 1) * 10
        padding_needed = records_needed - total_records

        for _ in range(padding_needed):
            lines.append("9" * 94)  # Padding record

        nacha_content = "\n".join(lines)

        logger.info(
            f"Generated NACHA file: {len(batch.transactions)} transactions, "
            f"{len(lines)} total records"
        )

        return nacha_content

    def _generate_file_header(self, batch: ACHBatch) -> str:
        """Generate NACHA File Header Record"""
        now = datetime.now()

        # File Creation Date/Time
        file_date = now.strftime("%y%m%d")
        file_time = now.strftime("%H%M")

        # Immediate Destination (receiving bank routing)
        immediate_dest = " " + self.odfi_routing[:9].ljust(9)[:9]

        # Immediate Origin (company tax ID)
        immediate_origin = " " + self.company_tax_id[:9].ljust(9)[:9]

        # File ID Modifier (A-Z, 0-9)
        file_id_modifier = "A"

        record = (
            "1"  # Record Type Code
            "01"  # Priority Code
            f"{immediate_dest}"  # Immediate Destination
            f"{immediate_origin}"  # Immediate Origin
            f"{file_date}"  # File Creation Date
            f"{file_time}"  # File Creation Time
            f"{file_id_modifier}"  # File ID Modifier
            "094"  # Record Size (always 094)
            "10"  # Blocking Factor (always 10)
            "1"  # Format Code (always 1)
            f"{self.company_name.ljust(23)[:23]}"  # Immediate Destination Name
            f"{self.company_name.ljust(23)[:23]}"  # Immediate Origin Name
            "        "  # Reference Code
        )

        return record

    def _generate_file_control(self, batch: ACHBatch, entry_count: int) -> str:
        """Generate NACHA File Control Record"""
        # Batch count
        batch_count = str(1).zfill(6)

        # Block count
        total_records = 2 + entry_count + 2  # file header + batch header + entries + batch control + file control
        block_count = str(((total_records // 10) + 1)).zfill(6)

        # Entry/Addenda count
        entry_addenda_count = str(entry_count).zfill(8)

        # Entry hash
        entry_hash = sum(int(t.receiving_dfi_routing[:8]) for t in batch.transactions)
        entry_hash_str = str(entry_hash)[-10:].zfill(10)

        # Total debits/credits
        total_debit = "000000000000000000"
        total_credit = str(int(batch.get_total_amount() * 100)).zfill(18)

        record = (
            "9"  # Record Type Code
            f"{batch_count}"  # Batch Count
            f"{block_count}"  # Block Count
            f"{entry_addenda_count}"  # Entry/Addenda Count
            f"{entry_hash_str}"  # Entry Hash
            f"{total_debit}"  # Total Debit Entry Dollar Amount
            f"{total_credit}"  # Total Credit Entry Dollar Amount
            "".ljust(39)  # Reserved
        )

        return record

    def save_nacha_file(self, batch: ACHBatch, filepath: str) -> bool:
        """Save NACHA file to disk"""
        try:
            content = self.generate_nacha_file(batch)

            with open(filepath, 'w') as f:
                f.write(content)

            logger.info(f"NACHA file saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save NACHA file: {e}")
            return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize processor
    processor = DirectDepositProcessor(
        company_name="Acme Corporation",
        company_tax_id="123456789",
        odfi_routing="121000248"  # Example: Wells Fargo
    )

    # Create employee bank account
    bank_account = BankAccount(
        account_holder_name="John Doe",
        routing_number="121000248",
        account_number="1234567890",
        account_type=AccountType.CHECKING,
        bank_name="Wells Fargo",
        verified=True
    )

    success, error = processor.register_bank_account(bank_account)
    if success:
        print(f"Bank account registered: {bank_account.masked_account}")

        # Add deposit allocation (100% to this account)
        allocation = DepositAllocation(
            bank_account_id=bank_account.id,
            deposit_type=DepositType.PERCENTAGE,
            amount=Decimal("100"),
            priority=1
        )

        processor.add_deposit_allocation("emp_001", allocation)

        # Create ACH batch
        batch = processor.create_ach_batch()

        # Process direct deposit
        transactions = processor.process_direct_deposit(
            employee_id="emp_001",
            employee_name="John Doe",
            net_pay=Decimal("2500.00"),
            batch=batch
        )

        print(f"\nCreated {len(transactions)} ACH transaction(s)")
        print(f"Batch total: ${batch.get_total_amount()}")

        # Generate NACHA file
        nacha_content = processor.generate_nacha_file(batch)
        print(f"\nNACHA file generated ({len(nacha_content)} characters)")
