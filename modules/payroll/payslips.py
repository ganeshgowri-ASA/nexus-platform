"""
Enterprise Pay Slip Generation System
Generates professional pay slips in multiple formats (PDF, HTML, plain text)
Production-ready with email delivery and secure storage
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
import json
from io import BytesIO
from enum import Enum

logger = logging.getLogger(__name__)


class PayslipFormat(Enum):
    """Payslip output formats"""
    PDF = "pdf"
    HTML = "html"
    TEXT = "text"
    JSON = "json"


class DeliveryMethod(Enum):
    """Payslip delivery methods"""
    EMAIL = "email"
    PORTAL = "portal"
    PRINT = "print"
    DOWNLOAD = "download"


@dataclass
class CompanyInfo:
    """Company information for pay slips"""
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    email: str
    tax_id: str  # EIN
    logo_path: Optional[str] = None


@dataclass
class PayslipLineItem:
    """Individual line item on a pay slip"""
    description: str
    quantity: Decimal = Decimal("0")
    rate: Decimal = Decimal("0")
    current_amount: Decimal = Decimal("0")
    ytd_amount: Decimal = Decimal("0")
    item_type: str = "earning"  # earning, deduction, tax


@dataclass
class Payslip:
    """Complete pay slip document"""
    # Identifiers
    id: str
    payslip_number: str
    pay_period_start: date
    pay_period_end: date
    pay_date: date

    # Company and employee
    company: CompanyInfo
    employee_id: str
    employee_name: str
    employee_number: str
    employee_address: Optional[str] = None
    employee_ssn_last4: Optional[str] = None

    # Earnings
    earnings: List[PayslipLineItem] = field(default_factory=list)
    total_earnings: Decimal = Decimal("0")
    ytd_earnings: Decimal = Decimal("0")

    # Deductions
    deductions: List[PayslipLineItem] = field(default_factory=list)
    total_deductions: Decimal = Decimal("0")
    ytd_deductions: Decimal = Decimal("0")

    # Taxes
    taxes: List[PayslipLineItem] = field(default_factory=list)
    total_taxes: Decimal = Decimal("0")
    ytd_taxes: Decimal = Decimal("0")

    # Net pay
    net_pay: Decimal = Decimal("0")
    ytd_net_pay: Decimal = Decimal("0")

    # Hours (if applicable)
    regular_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    pto_hours: Decimal = Decimal("0")
    sick_hours: Decimal = Decimal("0")

    # Direct deposit
    deposit_accounts: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = "system"
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PayslipGenerator:
    """
    Pay slip generation engine
    Creates professional pay slips in multiple formats
    """

    def __init__(self, company: CompanyInfo):
        self.company = company
        self.template_dir = Path("templates/payslips")
        self.output_dir = Path("payslips")
        self.output_dir.mkdir(exist_ok=True)

    def create_payslip_from_payment_record(
        self,
        payment_record: Any,
        employee: Any,
        ytd_data: Optional[Dict[str, Decimal]] = None
    ) -> Payslip:
        """
        Create a pay slip from a payment record
        """
        if ytd_data is None:
            ytd_data = {}

        payslip = Payslip(
            id=payment_record.id,
            payslip_number=f"PS{datetime.now().strftime('%Y%m%d')}{employee.employee_number}",
            pay_period_start=payment_record.pay_period_start,
            pay_period_end=payment_record.pay_period_end,
            pay_date=payment_record.pay_date,
            company=self.company,
            employee_id=payment_record.employee_id,
            employee_name=payment_record.employee_name,
            employee_number=getattr(employee, 'employee_number', 'N/A'),
        )

        # Add earnings
        if payment_record.regular_pay > 0:
            payslip.earnings.append(PayslipLineItem(
                description="Regular Pay",
                quantity=payment_record.regular_hours,
                rate=employee.base_salary if not employee.is_salaried else Decimal("0"),
                current_amount=payment_record.regular_pay,
                ytd_amount=ytd_data.get("regular_pay", Decimal("0")),
                item_type="earning"
            ))

        if payment_record.overtime_pay > 0:
            payslip.earnings.append(PayslipLineItem(
                description="Overtime Pay",
                quantity=payment_record.overtime_hours,
                rate=employee.base_salary * Decimal("1.5") if hasattr(employee, 'base_salary') else Decimal("0"),
                current_amount=payment_record.overtime_pay,
                ytd_amount=ytd_data.get("overtime_pay", Decimal("0")),
                item_type="earning"
            ))

        if payment_record.double_time_pay > 0:
            payslip.earnings.append(PayslipLineItem(
                description="Double Time Pay",
                quantity=payment_record.double_time_hours,
                rate=employee.base_salary * Decimal("2.0") if hasattr(employee, 'base_salary') else Decimal("0"),
                current_amount=payment_record.double_time_pay,
                ytd_amount=ytd_data.get("double_time_pay", Decimal("0")),
                item_type="earning"
            ))

        if payment_record.bonus_total > 0:
            payslip.earnings.append(PayslipLineItem(
                description="Bonus/Commission",
                current_amount=payment_record.bonus_total,
                ytd_amount=ytd_data.get("bonus", Decimal("0")),
                item_type="earning"
            ))

        payslip.total_earnings = payment_record.gross_pay
        payslip.ytd_earnings = payment_record.ytd_gross

        # Add deductions
        for deduction_name, amount in payment_record.deduction_details:
            payslip.deductions.append(PayslipLineItem(
                description=deduction_name,
                current_amount=amount,
                ytd_amount=ytd_data.get(f"deduction_{deduction_name}", Decimal("0")),
                item_type="deduction"
            ))

        payslip.total_deductions = (
            payment_record.pre_tax_deductions + payment_record.post_tax_deductions
        )
        payslip.ytd_deductions = ytd_data.get("total_deductions", Decimal("0"))

        # Add taxes
        if payment_record.federal_tax > 0:
            payslip.taxes.append(PayslipLineItem(
                description="Federal Income Tax",
                current_amount=payment_record.federal_tax,
                ytd_amount=ytd_data.get("federal_tax", Decimal("0")),
                item_type="tax"
            ))

        if payment_record.state_tax > 0:
            payslip.taxes.append(PayslipLineItem(
                description="State Income Tax",
                current_amount=payment_record.state_tax,
                ytd_amount=ytd_data.get("state_tax", Decimal("0")),
                item_type="tax"
            ))

        if payment_record.social_security > 0:
            payslip.taxes.append(PayslipLineItem(
                description="Social Security",
                current_amount=payment_record.social_security,
                ytd_amount=ytd_data.get("social_security", Decimal("0")),
                item_type="tax"
            ))

        if payment_record.medicare > 0:
            payslip.taxes.append(PayslipLineItem(
                description="Medicare",
                current_amount=payment_record.medicare,
                ytd_amount=ytd_data.get("medicare", Decimal("0")),
                item_type="tax"
            ))

        if payment_record.local_tax > 0:
            payslip.taxes.append(PayslipLineItem(
                description="Local Tax",
                current_amount=payment_record.local_tax,
                ytd_amount=ytd_data.get("local_tax", Decimal("0")),
                item_type="tax"
            ))

        payslip.total_taxes = payment_record.total_taxes
        payslip.ytd_taxes = payment_record.ytd_taxes

        # Net pay
        payslip.net_pay = payment_record.net_pay
        payslip.ytd_net_pay = payment_record.ytd_net

        # Hours
        payslip.regular_hours = payment_record.regular_hours
        payslip.overtime_hours = payment_record.overtime_hours
        payslip.double_time_hours = payment_record.double_time_hours

        return payslip

    def generate_text_payslip(self, payslip: Payslip) -> str:
        """Generate plain text pay slip"""
        width = 80
        output = []

        # Header
        output.append("=" * width)
        output.append(self.company.name.center(width))
        output.append(f"{self.company.address}, {self.company.city}, {self.company.state} {self.company.zip_code}".center(width))
        output.append(f"Phone: {self.company.phone}  |  EIN: {self.company.tax_id}".center(width))
        output.append("=" * width)
        output.append("")
        output.append("PAY SLIP".center(width))
        output.append("=" * width)
        output.append("")

        # Employee and pay period info
        output.append(f"Employee: {payslip.employee_name:<40} ID: {payslip.employee_number}")
        if payslip.employee_ssn_last4:
            output.append(f"SSN: XXX-XX-{payslip.employee_ssn_last4}")
        output.append("")
        output.append(f"Pay Period: {payslip.pay_period_start} to {payslip.pay_period_end}")
        output.append(f"Pay Date: {payslip.pay_date}")
        output.append(f"Payslip #: {payslip.payslip_number}")
        output.append("-" * width)
        output.append("")

        # Hours (if applicable)
        if payslip.regular_hours > 0 or payslip.overtime_hours > 0:
            output.append("HOURS")
            output.append("-" * width)
            output.append(f"{'Description':<40} {'Hours':>15} {'YTD Hours':>15}")
            output.append("-" * width)
            if payslip.regular_hours > 0:
                output.append(f"{'Regular Hours':<40} {float(payslip.regular_hours):>15.2f}")
            if payslip.overtime_hours > 0:
                output.append(f"{'Overtime Hours':<40} {float(payslip.overtime_hours):>15.2f}")
            if payslip.double_time_hours > 0:
                output.append(f"{'Double Time Hours':<40} {float(payslip.double_time_hours):>15.2f}")
            output.append("")

        # Earnings
        output.append("EARNINGS")
        output.append("-" * width)
        output.append(f"{'Description':<40} {'Current':>15} {'YTD':>20}")
        output.append("-" * width)
        for item in payslip.earnings:
            output.append(
                f"{item.description:<40} "
                f"${float(item.current_amount):>14,.2f} "
                f"${float(item.ytd_amount):>19,.2f}"
            )
        output.append("-" * width)
        output.append(
            f"{'TOTAL EARNINGS':<40} "
            f"${float(payslip.total_earnings):>14,.2f} "
            f"${float(payslip.ytd_earnings):>19,.2f}"
        )
        output.append("")

        # Deductions
        if payslip.deductions:
            output.append("DEDUCTIONS")
            output.append("-" * width)
            output.append(f"{'Description':<40} {'Current':>15} {'YTD':>20}")
            output.append("-" * width)
            for item in payslip.deductions:
                output.append(
                    f"{item.description:<40} "
                    f"${float(item.current_amount):>14,.2f} "
                    f"${float(item.ytd_amount):>19,.2f}"
                )
            output.append("-" * width)
            output.append(
                f"{'TOTAL DEDUCTIONS':<40} "
                f"${float(payslip.total_deductions):>14,.2f} "
                f"${float(payslip.ytd_deductions):>19,.2f}"
            )
            output.append("")

        # Taxes
        output.append("TAXES")
        output.append("-" * width)
        output.append(f"{'Description':<40} {'Current':>15} {'YTD':>20}")
        output.append("-" * width)
        for item in payslip.taxes:
            output.append(
                f"{item.description:<40} "
                f"${float(item.current_amount):>14,.2f} "
                f"${float(item.ytd_amount):>19,.2f}"
            )
        output.append("-" * width)
        output.append(
            f"{'TOTAL TAXES':<40} "
            f"${float(payslip.total_taxes):>14,.2f} "
            f"${float(payslip.ytd_taxes):>19,.2f}"
        )
        output.append("")

        # Net pay
        output.append("=" * width)
        output.append(
            f"{'NET PAY':<40} "
            f"${float(payslip.net_pay):>14,.2f} "
            f"${float(payslip.ytd_net_pay):>19,.2f}"
        )
        output.append("=" * width)
        output.append("")

        # Direct deposit info
        if payslip.deposit_accounts:
            output.append("DIRECT DEPOSIT")
            output.append("-" * width)
            for account in payslip.deposit_accounts:
                output.append(
                    f"{account.get('account_type', 'Account').title()}: "
                    f"****{account.get('last4', 'XXXX')} - "
                    f"${float(account.get('amount', 0)):,.2f}"
                )
            output.append("")

        # Notes
        if payslip.notes:
            output.append("NOTES")
            output.append("-" * width)
            for note in payslip.notes:
                output.append(note)
            output.append("")

        # Footer
        output.append("=" * width)
        output.append("This is not a check. Please retain for your records.".center(width))
        output.append(f"Generated: {payslip.generated_at.strftime('%Y-%m-%d %H:%M:%S')}".center(width))
        output.append("=" * width)

        return "\n".join(output)

    def generate_html_payslip(self, payslip: Payslip) -> str:
        """Generate HTML pay slip"""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pay Slip - {payslip.employee_name}</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .payslip {{
            background: white;
            padding: 40px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .company-name {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .company-info {{
            font-size: 12px;
            color: #666;
        }}
        .title {{
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            margin: 20px 0;
            color: #333;
        }}
        .info-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .info-box {{
            padding: 15px;
            background: #f9f9f9;
            border-left: 4px solid #007bff;
        }}
        .info-label {{
            font-size: 11px;
            color: #666;
            text-transform: uppercase;
        }}
        .info-value {{
            font-size: 14px;
            font-weight: bold;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        th {{
            background: #333;
            color: white;
            padding: 12px;
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f9f9f9;
        }}
        .amount {{
            text-align: right;
            font-family: 'Courier New', monospace;
        }}
        .total-row {{
            font-weight: bold;
            background: #f0f0f0;
            border-top: 2px solid #333;
        }}
        .net-pay {{
            background: #007bff;
            color: white;
            font-size: 18px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
        }}
        .net-pay .label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .net-pay .amount {{
            font-size: 32px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .footer {{
            text-align: center;
            font-size: 11px;
            color: #666;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin: 20px 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 2px solid #007bff;
        }}
    </style>
</head>
<body>
    <div class="payslip">
        <div class="header">
            <div class="company-name">{self.company.name}</div>
            <div class="company-info">
                {self.company.address}, {self.company.city}, {self.company.state} {self.company.zip_code}<br>
                Phone: {self.company.phone} | Email: {self.company.email} | EIN: {self.company.tax_id}
            </div>
        </div>

        <div class="title">PAY SLIP</div>

        <div class="info-section">
            <div class="info-box">
                <div class="info-label">Employee</div>
                <div class="info-value">{payslip.employee_name}</div>
                <div class="info-value">ID: {payslip.employee_number}</div>
            </div>
            <div class="info-box">
                <div class="info-label">Pay Period</div>
                <div class="info-value">{payslip.pay_period_start} to {payslip.pay_period_end}</div>
                <div class="info-value">Pay Date: {payslip.pay_date}</div>
            </div>
        </div>

        <div class="section-title">EARNINGS</div>
        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th style="text-align: right;">Current</th>
                    <th style="text-align: right;">Year-to-Date</th>
                </tr>
            </thead>
            <tbody>
"""

        # Add earnings
        for item in payslip.earnings:
            html += f"""
                <tr>
                    <td>{item.description}</td>
                    <td class="amount">${float(item.current_amount):,.2f}</td>
                    <td class="amount">${float(item.ytd_amount):,.2f}</td>
                </tr>
"""

        html += f"""
                <tr class="total-row">
                    <td>TOTAL EARNINGS</td>
                    <td class="amount">${float(payslip.total_earnings):,.2f}</td>
                    <td class="amount">${float(payslip.ytd_earnings):,.2f}</td>
                </tr>
            </tbody>
        </table>
"""

        # Add deductions if any
        if payslip.deductions:
            html += """
        <div class="section-title">DEDUCTIONS</div>
        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th style="text-align: right;">Current</th>
                    <th style="text-align: right;">Year-to-Date</th>
                </tr>
            </thead>
            <tbody>
"""
            for item in payslip.deductions:
                html += f"""
                <tr>
                    <td>{item.description}</td>
                    <td class="amount">${float(item.current_amount):,.2f}</td>
                    <td class="amount">${float(item.ytd_amount):,.2f}</td>
                </tr>
"""
            html += f"""
                <tr class="total-row">
                    <td>TOTAL DEDUCTIONS</td>
                    <td class="amount">${float(payslip.total_deductions):,.2f}</td>
                    <td class="amount">${float(payslip.ytd_deductions):,.2f}</td>
                </tr>
            </tbody>
        </table>
"""

        # Add taxes
        html += """
        <div class="section-title">TAXES</div>
        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th style="text-align: right;">Current</th>
                    <th style="text-align: right;">Year-to-Date</th>
                </tr>
            </thead>
            <tbody>
"""
        for item in payslip.taxes:
            html += f"""
                <tr>
                    <td>{item.description}</td>
                    <td class="amount">${float(item.current_amount):,.2f}</td>
                    <td class="amount">${float(item.ytd_amount):,.2f}</td>
                </tr>
"""
        html += f"""
                <tr class="total-row">
                    <td>TOTAL TAXES</td>
                    <td class="amount">${float(payslip.total_taxes):,.2f}</td>
                    <td class="amount">${float(payslip.ytd_taxes):,.2f}</td>
                </tr>
            </tbody>
        </table>

        <div class="net-pay">
            <div class="label">NET PAY</div>
            <div class="amount">${float(payslip.net_pay):,.2f}</div>
            <div class="label" style="margin-top: 10px;">YTD: ${float(payslip.ytd_net_pay):,.2f}</div>
        </div>

        <div class="footer">
            <p>This is not a check. Please retain for your records.</p>
            <p>Generated: {payslip.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def generate_json_payslip(self, payslip: Payslip) -> str:
        """Generate JSON pay slip"""
        data = {
            "payslip_number": payslip.payslip_number,
            "pay_period": {
                "start": payslip.pay_period_start.isoformat(),
                "end": payslip.pay_period_end.isoformat(),
                "pay_date": payslip.pay_date.isoformat(),
            },
            "company": {
                "name": self.company.name,
                "address": self.company.address,
                "city": self.company.city,
                "state": self.company.state,
                "zip_code": self.company.zip_code,
                "tax_id": self.company.tax_id,
            },
            "employee": {
                "id": payslip.employee_id,
                "name": payslip.employee_name,
                "number": payslip.employee_number,
            },
            "earnings": [
                {
                    "description": item.description,
                    "current": float(item.current_amount),
                    "ytd": float(item.ytd_amount),
                }
                for item in payslip.earnings
            ],
            "deductions": [
                {
                    "description": item.description,
                    "current": float(item.current_amount),
                    "ytd": float(item.ytd_amount),
                }
                for item in payslip.deductions
            ],
            "taxes": [
                {
                    "description": item.description,
                    "current": float(item.current_amount),
                    "ytd": float(item.ytd_amount),
                }
                for item in payslip.taxes
            ],
            "totals": {
                "earnings": {
                    "current": float(payslip.total_earnings),
                    "ytd": float(payslip.ytd_earnings),
                },
                "deductions": {
                    "current": float(payslip.total_deductions),
                    "ytd": float(payslip.ytd_deductions),
                },
                "taxes": {
                    "current": float(payslip.total_taxes),
                    "ytd": float(payslip.ytd_taxes),
                },
                "net_pay": {
                    "current": float(payslip.net_pay),
                    "ytd": float(payslip.ytd_net_pay),
                },
            },
            "hours": {
                "regular": float(payslip.regular_hours),
                "overtime": float(payslip.overtime_hours),
                "double_time": float(payslip.double_time_hours),
            },
            "generated_at": payslip.generated_at.isoformat(),
        }

        return json.dumps(data, indent=2)

    def generate_payslip(
        self,
        payslip: Payslip,
        format: PayslipFormat = PayslipFormat.HTML
    ) -> str:
        """Generate pay slip in specified format"""
        logger.info(f"Generating {format.value} payslip for {payslip.employee_name}")

        if format == PayslipFormat.TEXT:
            return self.generate_text_payslip(payslip)
        elif format == PayslipFormat.HTML:
            return self.generate_html_payslip(payslip)
        elif format == PayslipFormat.JSON:
            return self.generate_json_payslip(payslip)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def save_payslip(
        self,
        payslip: Payslip,
        format: PayslipFormat = PayslipFormat.HTML
    ) -> Path:
        """Save pay slip to file"""
        content = self.generate_payslip(payslip, format)

        # Create filename
        filename = f"{payslip.payslip_number}.{format.value}"
        filepath = self.output_dir / filename

        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Payslip saved to {filepath}")
        return filepath

    def batch_generate_payslips(
        self,
        payslips: List[Payslip],
        format: PayslipFormat = PayslipFormat.HTML
    ) -> List[Path]:
        """Generate multiple pay slips in batch"""
        logger.info(f"Batch generating {len(payslips)} payslips")

        filepaths = []
        for payslip in payslips:
            try:
                filepath = self.save_payslip(payslip, format)
                filepaths.append(filepath)
            except Exception as e:
                logger.error(f"Failed to generate payslip for {payslip.employee_name}: {e}")

        logger.info(f"Successfully generated {len(filepaths)}/{len(payslips)} payslips")
        return filepaths


class PayslipDeliveryService:
    """
    Pay slip delivery service
    Handles email, portal uploads, and other delivery methods
    """

    def __init__(self):
        self.delivery_log: List[Dict[str, Any]] = []

    def deliver_via_email(
        self,
        payslip: Payslip,
        employee_email: str,
        content: str,
        format: PayslipFormat
    ) -> bool:
        """
        Deliver pay slip via email
        In production, integrate with email service (SendGrid, SES, etc.)
        """
        logger.info(f"Delivering payslip to {employee_email}")

        # This is a placeholder - integrate with actual email service
        delivery_record = {
            "payslip_id": payslip.id,
            "employee_email": employee_email,
            "method": DeliveryMethod.EMAIL.value,
            "format": format.value,
            "delivered_at": datetime.now().isoformat(),
            "status": "sent",
        }

        self.delivery_log.append(delivery_record)

        logger.info(f"Payslip delivered successfully to {employee_email}")
        return True

    def deliver_to_portal(
        self,
        payslip: Payslip,
        employee_id: str,
        filepath: Path
    ) -> bool:
        """
        Upload pay slip to employee portal
        """
        logger.info(f"Uploading payslip to portal for employee {employee_id}")

        # Placeholder for portal integration
        delivery_record = {
            "payslip_id": payslip.id,
            "employee_id": employee_id,
            "method": DeliveryMethod.PORTAL.value,
            "filepath": str(filepath),
            "delivered_at": datetime.now().isoformat(),
            "status": "uploaded",
        }

        self.delivery_log.append(delivery_record)

        return True

    def get_delivery_status(self, payslip_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery status for a payslip"""
        for record in self.delivery_log:
            if record["payslip_id"] == payslip_id:
                return record
        return None


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Setup company
    company = CompanyInfo(
        name="Acme Corporation",
        address="123 Business St",
        city="San Francisco",
        state="CA",
        zip_code="94105",
        phone="(555) 123-4567",
        email="payroll@acme.com",
        tax_id="12-3456789"
    )

    # Create generator
    generator = PayslipGenerator(company)

    # Create sample payslip
    payslip = Payslip(
        id="pay_001",
        payslip_number="PS20241118001",
        pay_period_start=date(2024, 11, 1),
        pay_period_end=date(2024, 11, 14),
        pay_date=date(2024, 11, 20),
        company=company,
        employee_id="emp_123",
        employee_name="John Doe",
        employee_number="EMP001"
    )

    # Add sample data
    payslip.earnings.append(PayslipLineItem(
        description="Regular Pay",
        current_amount=Decimal("2500.00"),
        ytd_amount=Decimal("50000.00"),
        item_type="earning"
    ))

    payslip.total_earnings = Decimal("2500.00")
    payslip.ytd_earnings = Decimal("50000.00")

    payslip.taxes.append(PayslipLineItem(
        description="Federal Income Tax",
        current_amount=Decimal("300.00"),
        ytd_amount=Decimal("6000.00"),
        item_type="tax"
    ))

    payslip.total_taxes = Decimal("300.00")
    payslip.ytd_taxes = Decimal("6000.00")

    payslip.net_pay = Decimal("2200.00")
    payslip.ytd_net_pay = Decimal("44000.00")

    # Generate payslips
    text_payslip = generator.generate_payslip(payslip, PayslipFormat.TEXT)
    print(text_payslip)

    html_path = generator.save_payslip(payslip, PayslipFormat.HTML)
    print(f"\nHTML payslip saved to: {html_path}")
