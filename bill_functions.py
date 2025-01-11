
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from flask import Flask,render_template

def create_invoice(bill_info,items):
    buffer=BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    c.setFont('Helvetica-Bold', 12)
    c.drawString(50, height - 50, bill_info['header'])
    
    # Address and Contact Info
    c.setFont('Helvetica', 10)
    y_position = height - 70
    for line in bill_info['address']:
        c.drawString(50, y_position, line)
        y_position -= 15
    
    # Bill To Section
    y_position -= 15 
    for line in bill_info['bill_to']:
        c.drawString(50, y_position, line)
        y_position -= 15
    
    # Table Header
    headers = ['PRODUCT NAME', 'QUANTITY', 'UNIT PRICE (Rs)', 'MRP (Rs)','DISCOUNT (Rs)','TOTAL AMOUNT (Rs)']
    x_positions = [50, 150,230, 340, 430,530]
    y_position -= 30
     
    for x_pos, header in zip(x_positions, headers):
        c.drawString(x_pos, y_position, header)

    # Table Content 
    y_position -= 30 
     
    # Grand Total
    Total_Quantity=0
    Total_MRP=0
    Total_Discount=0
    Total_Amount=0
    for item in items:
        x_pos = x_positions[0]
        c.drawString(x_pos, y_position, str(item['Product_Name']))
        x_pos += 100 
        c.drawString(x_pos, y_position, str(item['Product_Quantity']))
        Total_Quantity+=item['Product_Quantity']
        x_pos += 100
        c.drawString(x_pos, y_position, str(format(item['Unit_Price'],".2f")))
        x_pos += 100
        c.drawString(x_pos, y_position, str(format(item['Price'],".2f")))
        Total_MRP+=round(item['Price'],2)
        x_pos += 100
        c.drawString(x_pos, y_position, str(format(item['Price']-item['NetPrice'],".2f")))
        x_pos += 100
        Total_Discount+=round((item['Price']-item['NetPrice']),2)
        c.drawString(x_pos,y_position,str(format(item['NetPrice'],".2f")))
        Total_Amount+=round(item['NetPrice'],2)
        y_position -= 20 
    y_position-=10

    # Total Amount
    x_pos = x_positions[0]
    c.drawString(x_pos,y_position,str('Grand Total'))
    x_pos+=100
    c.drawString(x_pos,y_position,f'{Total_Quantity}')
    x_pos+=200
    c.drawString(x_pos,y_position,f'{Total_MRP:.2f}')
    x_pos+=100
    c.drawString(x_pos,y_position,f'{Total_Discount:.2f}')
    x_pos+=100
    c.drawString(x_pos,y_position,f'{Total_Amount:.2f}')
    

    # Footer 
    footer_y_position = 100 
    for line in bill_info['footer']:
        c.drawCentredString(width / 2.0, footer_y_position, line)
        footer_y_position -= 15 
    c.save()
    return buffer.getvalue()

def main(items,customer_name,email,order_id='',date=datetime.datetime.now().date(),time=datetime.datetime.now().time().strftime("%H:%M:%S"),base=False):
    bill_information = {
    "header": "SHOAP MANAGEMENT SYSTEM",
    "address": [
        "Near Allahabad Medical Asosiation",
        "Prayagraj,Uttar Pradesh",
        "211001",
        "Con-7897972297"
    ],
    "bill_to": [
        f"Date : {date}",
        f"Time : {time}",
        f"Customer Name : {customer_name}",
        f"Email : {email}",
        f"Order Id : {order_id}"
    ],
    "footer": ["THANK YOU FOR YOUR SHOAPING!"]
}
    # Upload PDF file
    
        # Read the uploaded PDF file as bytes
    pdf_contents = create_invoice(bill_information,items)

        # Convert binary data to base64
    pdf_base64 = base64.b64encode(pdf_contents).decode("utf-8")

    if base==True:
        return pdf_base64

        # Embed base64-encoded PDF content using iframe

    if order_id!='' :
        return render_template('Bill.html',pdf=pdf_base64,customer_name=customer_name,order_id=True)
    
    return render_template('Bill.html',pdf=pdf_base64,customer_name=customer_name,customer_email=email)

def send_email_with_invoice(to_address, subject, body, base, from_address="kumarh18999@gmail.com", password="hkqt csvi zwhi jvyy", smtp_server="smtp.gmail.com", smtp_port=465):
    # Create the email header
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject
    
    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Open the PDF file in binary mode
        # Create a MIMEBase object for the attachment
    pdf_bytes = base64.b64decode(base)
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= Invoice.pdf ")

        # Attach the MIMEBase object to the email message
    msg.attach(part)

    # Create the SMTP server connection with SSL
    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    server.login(from_address, password)
    server.sendmail(from_address, to_address, msg.as_string())
    server.quit()
    return True

def send_bill(customer_name='HARSH Kumar',customer_email='kumarh18909@gmail.com',items=[]):
    base=main(customer_name=customer_name,email='kumarh18909@gmail.com',base=True,items=items)
    body=f'''
{customer_name},

I hope this message finds you well.

Please find attached your invoice for the recent purchase/order with Shop Management System. We appreciate your value you as a customer.


Invoice Date: {datetime.datetime.now().date()}

If you have any questions or need further clarification regarding the invoice, please do not hesitate to contact us at kumarh18909@gmail.com .

Payment Instructions: On Time

We kindly request that the payment be made by the due date mentioned above to ensure timely processing. 

Thank you for your prompt attention to this matter. We look forward to serving you again.
'''
    if send_email_with_invoice(to_address=customer_email,subject='Invoice' ,body=body,base=base):
        return True
    return False
