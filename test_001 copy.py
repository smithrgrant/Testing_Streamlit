import pandas as pd
from pathlib import Path
from datetime import datetime
from jinja2 import Template
import webbrowser

# ---------- CONFIG ----------
EXCEL_PATH = Path("catering_quotes.xlsx")   # your workbook
FILTER_COL  = "QuoteID"                     # how to pick the row
FILTER_VAL  = 1001                          # value to match
OUT_DIR     = Path("quotes_out")            # where HTML goes
# ----------------------------

# (Optional) fake data if file is missing
def seed_fake(path: Path):
    if path.exists():
        return
    df = pd.DataFrame([
        {
            "QuoteID": 1001,
            "ClientName": "Acme Corp",
            "ContactEmail": "events@acme.com",
            "EventDate": "2025-08-15",
            "Headcount": 75,
            "MenuItems": "Roasted Chicken; Seasonal Veggies; Quinoa Salad; Lemon Tart",
            "ItemCosts": "12.50; 4.25; 5.10; 3.75",
            "ServiceFeePct": 0.15,
            "TaxPct": 0.06,
            "Notes": "Buffet style. Gluten-free options for 8 guests."
        },
        {
            "QuoteID": 1002,
            "ClientName": "Sunrise Weddings",
            "ContactEmail": "info@sunriseweddings.com",
            "EventDate": "2025-09-02",
            "Headcount": 120,
            "MenuItems": "Filet Mignon; Lobster Tail; Caesar Salad; Chocolate Mousse",
            "ItemCosts": "28.00; 26.00; 3.25; 4.50",
            "ServiceFeePct": 0.18,
            "TaxPct": 0.07,
            "Notes": "Plated dinner. Vegan mains for 10 guests."
        },
    ])
    df.to_excel(path, index=False)

# Simple Jinja2 HTML template
HTML_TMPL = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Catering Quote {{ quote_id }}</title>
<link rel="preconnect" href="https://fonts.gstatic.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{
  --accent:#3f6ad8;
  --light:#f5f7fa;
  --gray:#6b7280;
  --border:#e5e7eb;
  --text:#1f2937;
}
body{
  margin:0;
  font-family:'Montserrat', sans-serif;
  background:var(--light);
  color:var(--text);
}
.wrapper{
  max-width:900px;
  margin:40px auto;
  background:white;
  box-shadow:0 8px 20px rgba(0,0,0,.08);
  border-radius:16px;
  overflow:hidden;
}
.header{
  background:var(--accent);
  color:white;
  padding:32px 40px 24px;
  text-align:center;
}
.header h1{
  margin:0 0 8px;
  font-weight:600;
  font-size:28px;
}
.section{
  padding:28px 40px;
  border-bottom:1px solid var(--border);
}
.section:last-child{
  border-bottom:none;
}
.section h2{
  margin:0 0 14px;
  font-size:18px;
  font-weight:600;
  color:var(--accent);
}
.kv{
  display:flex;
  margin-bottom:6px;
}
.kv span.key{
  width:140px;
  font-weight:600;
  color:var(--gray);
}
.kv span.val{
  flex:1;
}
.table{
  width:100%;
  border-collapse:collapse;
  margin-top:8px;
}
.table th{
  background:var(--light);
  text-align:left;
  padding:10px 12px;
  border-bottom:2px solid var(--border);
  font-weight:600;
  font-size:14px;
}
.table td{
  padding:8px 12px;
  border-bottom:1px solid var(--border);
  font-size:14px;
}
.table td.num{
  text-align:right;
}
.total-row td{
  font-weight:600;
  background:var(--light);
}
.notes{
  line-height:1.5;
  white-space:pre-wrap;
}
.footer{
  text-align:center;
  padding:16px 0 28px;
  font-size:12px;
  color:var(--gray);
}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Catering Quote</h1>
    <div>Generated {{ generated }}</div>
  </div>

  <div class="section">
    <h2>Client &amp; Event Details</h2>
    <div class="kv"><span class="key">Quote ID:</span><span class="val">{{ quote_id }}</span></div>
    <div class="kv"><span class="key">Client:</span><span class="val">{{ client }}</span></div>
    <div class="kv"><span class="key">Email:</span><span class="val">{{ email }}</span></div>
    <div class="kv"><span class="key">Event Date:</span><span class="val">{{ event_date }}</span></div>
    <div class="kv"><span class="key">Headcount:</span><span class="val">{{ headcount }}</span></div>
  </div>

  <div class="section">
    <h2>Menu &amp; Pricing (per person)</h2>
    <table class="table">
      <thead>
        <tr><th>Item</th><th class="num">Cost ($)</th></tr>
      </thead>
      <tbody>
      {% for item, cost in rows %}
        <tr>
          <td>{{ item }}</td>
          <td class="num">{{ "{:,.2f}".format(cost) }}</td>
        </tr>
      {% endfor %}
        <tr class="total-row">
          <td>Subtotal / Person</td>
          <td class="num">{{ "{:,.2f}".format(subtotal_pp) }}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>Totals</h2>
    <table class="table">
      <tbody>
        <tr><td>Food Subtotal</td><td class="num">${{ "{:,.2f}".format(subtotal_total) }}</td></tr>
        <tr><td>Service Fee ({{ svc_pct }}%)</td><td class="num">${{ "{:,.2f}".format(service_fee) }}</td></tr>
        <tr><td>Tax ({{ tax_pct }}%)</td><td class="num">${{ "{:,.2f}".format(tax) }}</td></tr>
        <tr class="total-row"><td>Grand Total</td><td class="num">${{ "{:,.2f}".format(grand_total) }}</td></tr>
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>Notes / Special Instructions</h2>
    <div class="notes">{{ notes }}</div>
  </div>

  <div class="footer">
    © {{ year }} Your Catering Co. — Thank you for considering us!
  </div>
</div>
</body>
</html>
"""

def main():
    seed_fake(EXCEL_PATH)  # remove in production

    df = pd.read_excel(EXCEL_PATH)
    sel = df.loc[df[FILTER_COL] == FILTER_VAL]
    if sel.empty:
        raise ValueError(f"No row where {FILTER_COL} == {FILTER_VAL}")
    row = sel.iloc[0]

    items = [i.strip() for i in str(row["MenuItems"]).split(";")]
    costs = [float(c.strip()) for c in str(row["ItemCosts"]).split(";")]
    if len(items) != len(costs):
        raise ValueError("MenuItems and ItemCosts counts differ")

    subtotal_pp    = sum(costs)
    subtotal_total = subtotal_pp * row["Headcount"]
    service_fee    = subtotal_total * float(row["ServiceFeePct"])
    tax            = (subtotal_total + service_fee) * float(row["TaxPct"])
    grand_total    = subtotal_total + service_fee + tax

    ctx = {
        "generated":   datetime.now().strftime("%B %d, %Y"),
        "quote_id":    row["QuoteID"],
        "client":      row["ClientName"],
        "email":       row["ContactEmail"],
        "event_date":  pd.to_datetime(row["EventDate"]).strftime("%B %d, %Y"),
        "headcount":   row["Headcount"],
        "rows":        list(zip(items, costs)),
        "subtotal_pp": subtotal_pp,
        "subtotal_total": subtotal_total,
        "service_fee": service_fee,
        "tax":         tax,
        "grand_total": grand_total,
        "svc_pct":     int(row["ServiceFeePct"] * 100),
        "tax_pct":     int(row["TaxPct"] * 100),
        "notes":       row["Notes"] if pd.notna(row["Notes"]) else "—",
        "year":        datetime.now().year
    }

    html = Template(HTML_TMPL).render(**ctx)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"Quote_{row['QuoteID']}.html"
    out_path.write_text(html, encoding="utf-8")

    print("Saved:", out_path.resolve())
    # Open in default browser
    try:
        webbrowser.open(out_path.resolve().as_uri())
    except Exception:
        pass

    # html_to_pdf.py
    from pathlib import Path
    from weasyprint import HTML

    HTML_INPUT  = Path("quotes_out/Quote_1001.html")   # your existing file
    PDF_OUTPUT  = Path("quotes_out/Quote_1001.pdf")

    html = HTML_INPUT.read_text(encoding="utf-8")
    HTML(string=html, base_url=HTML_INPUT.parent.as_posix()).write_pdf(PDF_OUTPUT)

    print("Saved ->", PDF_OUTPUT.resolve())


if __name__ == "__main__":
    main()
