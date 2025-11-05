# backend/app/generate_mock_pdfs.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pathlib import Path
import textwrap

OUT_DIR = Path("backend/app/mock_docs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def write_pdf(filename: Path, title: str, paragraphs):
    p = filename
    c = canvas.Canvas(str(p), pagesize=letter)
    width, height = letter
    margin = 50
    y = height - margin
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, title)
    y -= 30
    c.setFont("Helvetica", 11)
    for para in paragraphs:
        wrapped = textwrap.wrap(para, width=90)
        for line in wrapped:
            if y < margin + 40:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 11)
            c.drawString(margin, y, line)
            y -= 14
        y -= 10
    c.showPage()
    c.save()
    print(f"Written {p}")

# Mock content for FinServe docs
policies_paras = [
    "Overview: FinServe is a fictional retail trading platform for equities and ETFs. "
    "This document summarizes account and trading policies that govern customer behavior and platform rules.",
    "Account Limits: Margin accounts may be subject to maintenance margin requirements. "
    "Pattern day trading rules apply to accounts with < $25,000 equity and frequent day trades.",
    "Order Types: Market, limit, stop loss, and trailing stop orders are supported. "
    "Orders are subject to market hours and exchange rules.",
    "Settlements & Clearing: Trades settle on T+2 settlement cycles for most equities. "
    "Customers should expect settlement delays during market holidays."
]

fees_paras = [
    "Account Types and Fees: FinServe offers Free and Pro account tiers. Free accounts have $0 monthly fee, "
    "while Pro accounts have a $9.99 monthly subscription that includes advanced charting tools.",
    "Commissions: FinServe charges no commission on standard equity trades. Certain premium data feeds or broker-assisted trades may carry fees.",
    "Margin Interest: Margin interest is charged monthly based on outstanding margin balances. "
    "Rates vary by tier and are documented here.",
    "Withdrawal & Transfer Fees: Domestic ACH withdrawals are free; bank wire withdrawals incur a $15 fee."
]

tech_paras = [
    "Overview: This Technical FAQ is intended to help customers troubleshoot common issues with the FinServe web and mobile apps, and with API access.",
    "Login & Authentication: If you cannot log in, try clearing cookies and resetting your password. Two-factor authentication (2FA) is available and recommended.",
    "API: The FinServe public API supports REST endpoints for fetching account info, positions, and market quotes. Rate limits are enforced: 100 requests per minute for Free tier, higher for Pro.",
    "Data Feed Issues: Delays in quotes can occur during market open/close. If you observe missing data, check 'market_status' endpoint and contact support with trace IDs."
]

# Create three PDFs
write_pdf(OUT_DIR / "FinServe_Trading_Policies.pdf", "FinServe — Trading Policies", policies_paras)
write_pdf(OUT_DIR / "FinServe_Account_Fees.pdf", "FinServe — Account Fees & Pricing", fees_paras)
write_pdf(OUT_DIR / "FinServe_Technical_FAQ.pdf", "FinServe — Technical FAQ", tech_paras)

print("All mock PDFs generated in:", OUT_DIR.resolve())

