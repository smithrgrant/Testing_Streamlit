import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# === Configuration ===
smtp_server   = 'smtp.gmail.com'
smtp_port     = 587
sender_email  = 'grantsmithdev@gmail.com'       # replace with your Gmail address
sender_pass   = 'vajb akxu tlvi mveg'          # replace with your Gmail App Password
recipient     = 'grantsmithdev@gmail.com'         # replace with your recipient

# === Create the message ===
msg = MIMEMultipart('alternative')
msg['Subject'] = 'Your Customized Catering Quote'
msg['From']    = sender_email
msg['To']      = recipient

# === HTML content ===
html = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; color: #333; background-color: #f4f4f4; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 20px auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .header { background: #2a9d8f; color: #fff; padding: 20px; text-align: center; }
    .header h1 { margin: 0; font-size: 24px; }
    .content { padding: 20px; }
    .content h2 { color: #264653; margin-top: 0; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th, td { text-align: left; padding: 10px; border-bottom: 1px solid #ddd; }
    th { background: #e9ecef; }
    .total-row th, .total-row td { font-weight: bold; }
    .footer { background: #e9ecef; padding: 15px; text-align: center; font-size: 12px; color: #666; }
    .button { display: inline-block; margin-top: 20px; padding: 12px 20px; background: #e76f51; color: #fff; text-decoration: none; border-radius: 4px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Sunrise Catering Co.</h1>
    </div>
    <div class="content">
      <p>Hi Jamie,</p>
      <p>Thank you for considering Sunrise Catering for your event on <strong>September 15, 2025</strong>. Below is your customized quote:</p>
      <h2>Event Details</h2>
      <p>
        <strong>Event:</strong> Corporate Luncheon<br>
        <strong>Guests:</strong> 50<br>
        <strong>Location:</strong> Riverside Conference Center
      </p>
      <h2>Your Quote</h2>
      <table>
        <tr><th>Menu Item</th><th>Qty</th><th>Unit Price</th><th>Line Total</th></tr>
        <tr><td>Grilled Chicken Caesar Salad</td><td>50</td><td>$12.00</td><td>$600.00</td></tr>
        <tr><td>Roasted Vegetable Quinoa Bowl</td><td>50</td><td>$11.50</td><td>$575.00</td></tr>
        <tr><td>Artisan Bread Basket</td><td>5</td><td>$15.00</td><td>$75.00</td></tr>
        <tr><td>Assorted Dessert Platter</td><td>1</td><td>$150.00</td><td>$150.00</td></tr>
        <tr class="total-row"><td colspan="3">Subtotal</td><td>$1,400.00</td></tr>
        <tr><td colspan="3">Tax (8%)</td><td>$112.00</td></tr>
        <tr class="total-row"><td colspan="3">Total</td><td>$1,512.00</td></tr>
      </table>
      <p style="text-align:center;">
        <a href="https://example.com/confirm-order" class="button">Confirm Your Quote</a>
      </p>
      <p>Warm regards,<br>
      <strong>Alex Monroe</strong><br>
      Sales Manager, Sunrise Catering Co.<br>
      (555) 123-4567 • alex@sunrisecatering.com</p>
    </div>
    <div class="footer">
      Sunrise Catering Co. • 123 Main St • Anytown, USA<br>
      <a href="https://example.com/unsubscribe">Unsubscribe</a>
    </div>
  </div>
</body>
</html>
"""

# Attach the HTML content
msg.attach(MIMEText(html, 'html'))

# === Send the email ===
try:
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(sender_email, sender_pass)
        server.sendmail(sender_email, recipient, msg.as_string())
    print("Email sent successfully!")
except Exception as e:
    print(f"Error sending email: {e}")
