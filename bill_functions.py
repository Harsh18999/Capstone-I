
import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64
from io import BytesIO
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

def main(items,customer_name,email,order_id='',date=datetime.datetime.now().date(),time=datetime.datetime.now().time().strftime("%H:%M:%S")):
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

        # Embed base64-encoded PDF content using iframe

    if order_id!='' :
        return render_template('Bill.html',pdf=pdf_base64,customer_name=customer_name,order_id=True)
    
    return render_template('Bill.html',pdf=pdf_base64,customer_name=customer_name)
