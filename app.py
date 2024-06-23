from flask import Flask, render_template, request,session,redirect,jsonify,url_for,send_file
import bill_functions
from datetime import datetime
from database import conn,conn_str
import login_functions
import calendar
import pandas as pd
from datetime import datetime
import random
import psycopg2 as database
import pdfkit


app = Flask(__name__)
app.secret_key = 'Secret'


@app.route('/')
def login_page():
    if 'username' not in session:
        return render_template('index.html',NotLogin=True)
    
    return render_template('index.html')


@app.route('/login' , methods=['POST','GET'])
def login():
    if request.method=='POST':
        pass
    else :
        return render_template('Login_Page.html')
    if login_functions.password_and_username_validator(password=request.form['password'],username=request.form['username']):
        session['username']=request.form['username']
        session['products']=[]
        session['bill_products']=[]
        return render_template('index.html')
    else:
        return 'Invalid username or password'
    
    
@app.route('/add_new_order', methods=['GET', 'POST'])
def add_new_order():
    if 'username' in session:
        if request.method == 'POST':
            username = session['username']
            select_product = request.form['select_product']
            quantity = int(request.form['quantity'])
            price = fetch_price(username, select_product) * quantity
            if quantity > 0:
                try:
                    # Update selected_products in session
                    discount=fetch_discount(session['username'],product_name=select_product)
                    netprice=round(price-(price*(discount/100)),2)
                    for n in range(len(session['bill_products'])):
                        if select_product == session['bill_products'][n]['Product_Name'] :
                            session['bill_products'][n]['Product_Quantity']=session['bill_products'][n]['Product_Quantity']+quantity
                            session['bill_products'][n]['Price']=session['bill_products'][n]['Price']+price
                            session['bill_products'][n]['Discount']=session['bill_products'][n]['Discount']+discount
                            session['bill_products'][n]['NetPrice']=session['bill_products'][n]['NetPrice']+netprice
                            session.modified=True
                            return render_template('AddNewOrder.html',success=f'Successfully Added',products=session['bill_products'],options=options(session['username']))
                        
                    session['bill_products'].append({"Product_Name": select_product, "Product_Quantity": quantity, "Unit_Price": price/quantity ,"Price": price,'Discount':discount,'NetPrice':netprice})
                    session.modified=True

                    # Render the updated table
                    return render_template('AddNewOrder.html',success=f'Successfully Added',products=session['bill_products'],options=options(session['username']))
                except Exception as e:
                    return False
            else:
                return render_template('add_new_order.html',error=f'There is an error',products=session['products'],options=options(session['username']))
        else:
            return render_template('AddNewOrder.html', options=options(session['username']),products=session['bill_products'])
    else:
        return False
    
# Fetch Price Directly From Database
def fetch_discount(username,product_name):
    cursor=conn.cursor()
    cursor.execute(f'''
                    SELECT DISCOUNT 
                    FROM {username}_PRODUCT_LIST
                    WHERE PRODUCT_NAME = '{product_name}' ''')
    return cursor.fetchall()[0][0]

def fetch_price(username, product_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT PRICE FROM {username}_PRODUCT_LIST WHERE PRODUCT_NAME='{product_name}'")
    res = cursor.fetchone()
    return res[0] if res else None

# Capture Products list from database
def options(username):
    cursor = conn.cursor()
    cursor.execute(f"SELECT PRODUCT_NAME FROM {username}_PRODUCT_LIST")
    result=cursor.fetchall()
    options=[]
    for n in result:
        options.append(n[0])
    return options

# Selected Products
def selected_products(items):
    session['selected_products'].aappend(items)
    return True

# Caputure Customer details
@app.route('/add_new_order/next')
def next():
        return render_template('AddNewOrder.html',customer_details=True)

@app.route('/add_new_order/next/bill',methods=['POST'])
def details():
    customer_name=request.form['customer_name']
    customer_email=request.form['customer_email']
    return bill_functions.main(session['bill_products'],customer_name=customer_name,email=customer_email)

# Reset Order 
@app.route('/add_new_order/reset' , methods=['POST'])
def reset():
    session['products']=[]
    session['bill_products']=[]
    return render_template('AddNewOrder.html',options=options(session['username']))

#Confrim The Order to Save in Data Base
@app.route('/add_new_order/next/bill/Confrim', methods=['POST'])
def Confrim ():
    CustomerName='Mr '+str(request.form['customer_name'])
    if CustomerName=='Mr ':
        CustomerName='Unknown'
    order_id=generate_order_id()
    for n in session['bill_products']:
        cost=CostCapture(n['Product_Name'])
        if add_product(username=session['username'],customer_name=CustomerName, select_product=n['Product_Name'], price=n['Price'], quantity=n['Product_Quantity'],order_id=order_id,cost=cost*n['Product_Quantity'],net_price=n['NetPrice']):
            pass
        else:
            cursor=conn.cursor()
            cursor.execute(f'''
                            DELETE FROM {session['username']}_ALL_DATA
                            WHERE ORDER_ID = '{order_id}' ''')
            conn.commit()
            return Warning(massage=f'Please check the stocks of {n["Product_Name"]}',cont='/My_Products')
        
    session['bill_products']=[]
    session.modified=True
    return Success(massage=f'Order Number {order_id} Successfully Saved, Thank you.',cont='/add_new_order')

# Cost capture
def CostCapture(product):
    cursor=conn.cursor()
    cursor.execute(f'''
                   SELECT COST_PRICE
                   FROM {session['username']}_PRODUCT_LIST
                   WHERE PRODUCT_NAME = '{product}'
                   ''')
    return cursor.fetchall()[0][0]

# Add order details on database

def add_product(username,customer_name,select_product,price,quantity,order_id,cost,net_price):
    cursor = conn.cursor()
    current_date_time = datetime.now()
    try:
        cursor.execute(f'''
                        UPDATE {username}_PRODUCT_LIST
                        SET QUANTITY = QUANTITY-{quantity}
                        WHERE PRODUCT_NAME = '{select_product}'; ''')
        conn.commit()
    except:
        con=database.connect(conn_str)
        cursor=con.cursor()
        cursor.execute(f'''
                       DELETE FROM HARSH20_ALL_DATA
                       WHERE ORDER_ID = '{order_id}'
                       ''')
        conn.commit()
        return False
    
    cursor.execute(f'''
                             INSERT INTO {username}_ALL_DATA(CUSTOMER_NAME, ORDER_NAME, PRICE, DATE, TIME, ORDER_ID,QUANTITY,COST,NET_PRICE) 
                             VALUES (%s, %s, %s, %s, %s,%s,%s,%s,%s)
                             ''', (customer_name, select_product, price, current_date_time.date(), current_date_time.strftime("%I:%M %p"),order_id,quantity,cost,net_price))
    conn.commit()
    return True

def generate_order_id():
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_number = random.randint(1000, 9999)
    order_id = f"{timestamp}{random_number}"
    return order_id

# Sell Dashboard 
@app.route('/table')
def table():
    username=session['username']
    cursor=conn.cursor()
    l=[]
    lables=[]
    values=[]
    query = f'''SELECT "customer_name","order_name","price","order_id","date","time","quantity" FROM {username}_ALL_DATA WHERE DATE = '{datetime.now().date()}' '''
    cursor.execute(query)
    result=cursor.fetchall()
    for n in result:
        n=list(n)
        dic={"CUSTOMER_NAME":n[0],"ORDER_NAME":n[1],"PRICE":n[2],"ORDER_ID":n[3],"DATE":n[4],"TIME":n[5],"QUANTITY":n[6]}
        l.append(dic)
    cursor.execute(f''' SELECT order_name,SUM(NET_PRICE) AS Total_Price
                        FROM {username}_all_data
                        WHERE date = '{datetime.now().date()}'
                        GROUP BY order_name
                        ORDER BY SUM(NET_PRICE) DESC;
                   ''')
    
    result=cursor.fetchall()
    for k in result:
        lables.append(k[0])
        values.append(k[1])
    line_Chart=today_sell_linechart(username)
    line_char_labels=line_Chart[0]
    line_char_values=line_Chart[1]
    Pie1=PieOne(username)
    Pie2=PieTwo(username)
    NumberOfOrders=TodayNumberOrders(username)
    revpro=TodayRevPro(username=username)
    return render_template('table.html',people=l,labels=lables,values=values,lineChart_labels=line_char_labels,lineChart_values=line_char_values,Pielabels=Pie1[0],Pievalues=Pie1[1],Pielabels2=Pie2[0],Pievalues2=Pie2[1],NumOrder=NumberOfOrders,revenue=revpro[0],cost=revpro[1])


# Edit products list in database
@app.route('/edit_product')
def edit_product_list():
    cursor = conn.cursor()
    cursor.execute(f''' SELECT PRODUCT_NAME FROM {session['username']}_PRODUCT_LIST ''')
    result = cursor.fetchall()
    product_name_options = [n[0] for n in result]
    session['products']=product_name_options
    return render_template('EditProduct.html', product_name_options=product_name_options)

#Edit Product List
@app.route('/edit_product/next', methods=['POST'])
def ProdcutEdit():
    selected_product = request.form['product']
    selected_type = request.form['edit']
    return render_template('EditProduct.html',Product=selected_product,Edit=selected_type,next=True,Selected_Type=selected_type)


# save edit things in database
@app.route('/edit_product/next/save' , methods=['POST'])
def save_changes():
    product = request.form['product_next']
    edit_type=request.form['edit_type']
    if edit_type=='PRODUCT_NAME':
        new_val=request.form['edit2']
        return edit(product,new_val,edit_type)
    elif edit_type=='PRODUCT_TYPE':
        new_val=request.form['edit1']
        return edit(product,new_val,edit_type)
    else:
        new_val=request.form['edit3']
        return edit(product,new_val,edit_type)

def edit(product,new_value,selected_type):
    cursor=conn.cursor()
    if selected_type == 'PRODUCT_TYPE'or selected_type=='PRODUCT_ID' or selected_type=='PRODUCT_NAME':
                cursor.execute(f''' UPDATE {session['username']}_PRODUCT_LIST
                                    SET {selected_type} ='{new_value}'
                                    WHERE PRODUCT_NAME = '{product}' ''')
                conn.commit()
                return redirect('/My_Products')
    else:
        cursor.execute(f''' UPDATE {session['username']}_PRODUCT_LIST
                                    SET {selected_type} ={new_value}
                                    WHERE PRODUCT_NAME = '{product}' ''')
        conn.commit()
        return redirect('/My_Products')


# My Products
@app.route('/My_Products')
def My_Products():
    conn=database.connect(conn_str)
    cursor=conn.cursor()
    cursor.execute(f'''SELECT * FROM {session['username']}_PRODUCT_LIST''')
    all_data=cursor.fetchall()
    return render_template('MyProducts.html',Products=all_data)


# Monthly Dashboard
@app.route('/MonthSell')
def MonthSell():
    HistRes=Hist(session['username'])
    LineChart=lineChart(session['username'])
    PieChart=Pie(session['username'])
    OrderDist=NumOrders(session['username'])
    NumberOfOrders=NumberOrders(session['username'])
    revpro=RevPro(session['username'])
    return render_template('Dashboard.html',Title='CURRENT MONTH SELL DASHBOARD',Orders=Total_Orders(session['username']),Hist_labels=HistRes[0],Hist_values=HistRes[1],LineChart_labels=LineChart[0],LineChart_values=LineChart[1],PieChart1_labels=PieChart[0],PieChart1_values=PieChart[1],PieChart2_labels=OrderDist[0],PieChart2_values=OrderDist[1],Total_Orders=NumberOfOrders,Total_Revenue=revpro[0],Total_Cost=revpro[1],Total_Profit=float(revpro[0])-float(revpro[1]))


def Hist(username):
    cursor=conn.cursor()
    cursor.execute(f'''
SELECT ORDER_NAME,SUM(PRICE)
FROM {username}_ALL_DATA
WHERE EXTRACT(MONTH FROM DATE )= {datetime.now().month}
GROUP BY ORDER_NAME
    ''')
    labels=[]
    values=[]
    for n in cursor.fetchall():
        labels.append(n[0])
        values.append(n[1])
    return [labels,values]


def lineChart(username):
    cursor=conn.cursor()
    labels=[]
    values=[]
    date=f'{datetime.now().year}-{datetime.now().month}-'
    days=calendar.monthrange(datetime.now().year,datetime.now().month)[1]
    for i in range(1,days+1):
        cursor.execute(f'''
    SELECT SUM(price)
    FROM {username}_ALL_DATA
    WHERE DATE = '{date+str(i)}'  ''')
        total=cursor.fetchall()[0][0]
        if not total:
            total=0
        labels.append(f'{date+str(i)}')
        values.append(total)
    return [labels,values]


def Total_Orders(username):
    cursor=conn.cursor()
    TotalData=[]
    query = f'''SELECT "customer_name","order_name","price","order_id","date","time","quantity" FROM {username}_ALL_DATA WHERE EXTRACT(MONTH FROM DATE )= {datetime.now().month} '''
    cursor.execute(query)
    result=cursor.fetchall()
    for n in result:
        n=list(n)
        dic={"CUSTOMER_NAME":n[0],"ORDER_NAME":n[1],"PRICE":n[2],"ORDER_ID":n[3],"DATE":n[4],"TIME":n[5],"QUANTITY":n[6]}
        TotalData.append(dic)
    
    return TotalData

def Pie(username):
    cursor=conn.cursor()
    cursor.execute(f'''
SELECT ORDER_NAME,CAST(SUM(NET_PRICE) AS INTEGER)-CAST(SUM(COST) AS INTEGER)
FROM {username}_ALL_DATA
WHERE EXTRACT(MONTH FROM DATE)={datetime.now().month}
GROUP BY ORDER_NAME''')
    d=cursor.fetchall()
    d=dict(d)
    return [list(d.keys()),list(d.values())]

def NumOrders(username):
    cursor=conn.cursor()
    cursor.execute(f'''
SELECT ORDER_NAME,COUNT(ORDER_ID)
FROM {username}_ALL_DATA
WHERE EXTRACT(MONTH FROM DATE)={datetime.now().month}
GROUP BY ORDER_NAME''')
    d=dict(cursor.fetchall())
    return [list(d.keys()),list(d.values())]

def NumberOrders(username):
    cursor=conn.cursor()
    cursor.execute(f'''
SELECT COUNT(DISTINCT(ORDER_ID))
FROM {username}_ALL_DATA ''')
    return cursor.fetchall()[0][0]

def RevPro(username):
    cursor=conn.cursor()
    cursor.execute(f'''
SELECT SUM(PRICE)
FROM {username}_ALL_DATA
WHERE EXTRACT(MONTH FROM DATE)={datetime.now().month}''')
    revenue=cursor.fetchall()[0][0]
    cursor.execute(f'''
SELECT SUM(COST)
FROM {username}_ALL_DATA
WHERE EXTRACT(MONTH FROM DATE)={datetime.now().month}''')
    cost=cursor.fetchall()[0][0]
    return [revenue,cost]

@app.route('/Add New Product',methods=['GET','POST'])
def add_new_product():
    if 'username' in session:
        if request.method=='POST':
            ProductName=request.form['ProductName']
            Price=request.form['Price']
            ProductId=request.form['ProductId']
            Quantity=request.form['Quantity']
            Discount=request.form['Discount']
            CostPrice=request.form['CostPrice']
            ProductType=request.form['ProductType']
            cursor=conn.cursor()
            cursor.execute(f'''
                            INSERT INTO {session['username']}_PRODUCT_LIST
                        (PRODUCT_NAME,PRICE,PRODUCT_ID,QUANTITY,DISCOUNT,COST_PRICE,PRODUCT_TYPE) VALUES ('{ProductName}',{Price},{ProductId},{Quantity},{Discount},{CostPrice},'{ProductType}')''')
            conn.commit() 
            return f'Successfully {ProductName} Saved ' 
        else:
            return render_template('AddNewProduct.html')
    else:
        False
path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
pdfkit_config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

# @app.route('/download_pdf', methods=['GET'])
# def download_pdf():
    
#     rendered_html = render_template('index.html')
    
#     # Create a temporary HTML file
#     with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_html:
#         temp_html.write(rendered_html.encode('utf-8'))
#         temp_html_path = temp_html.name
    
#     # Generate the PDF from the HTML file
#     pdf = pdfkit.from_file(temp_html_path,False, configuration=pdfkit_config)
    
#     # Remove the temporary HTML file
#     os.remove(temp_html_path)
    
#     # Save the PDF to a file
#     pdf_path = 'output.pdf'
#     with open(pdf_path, 'wb') as f:
#         f.write(pdf)
    
#     # Send the PDF file as a response
#     return send_file(pdf_path, as_attachment=True)

@app.route('/Dashboard')
def dash():
    orders=Orders(session['username'])
    Hist=TopSelling_Product(session['username'])
    pie1=PieOne(session['username'])
    pie2=PieTwo(session['username'])
    line_chart=today_sell_linechart(username=session['username'],start_time='00:00:00',end_time='23:00:00',time_gap=2)
    revpro=TodayRevPro(session['username'])
    Total_Revenue=revpro[0]
    Total_Cost=revpro[1]
    Total_Profit=Total_Revenue-Total_Cost
    Total_Orders=TodayNumberOrders(session['username'])
    return render_template('Dashboard.html',Title='TODAY SELL DASHBOARD',Hist_labels=Hist[0],Hist_values=Hist[1],LineChart_labels=line_chart[0],LineChart_values=line_chart[1],PieChart1_labels=pie1[0],PieChart1_values= pie1[1],PieChart2_labels=pie2[0],PieChart2_values=pie2[1],Total_Revenue=revpro[0],Total_Cost=revpro[1],Total_Orders=Total_Orders,Total_Profit=Total_Profit,Orders=orders)
def PieOne(username):
    cursor=conn.cursor()
    cursor.execute(f'''
SELECT ORDER_NAME,CAST(SUM(NET_PRICE) AS FLOAT)-CAST(SUM(COST) AS FLOAT)
FROM {username}_ALL_DATA
WHERE DATE= '{datetime.now().date()}'
GROUP BY ORDER_NAME''')
    d=cursor.fetchall()
    d=dict(d)
    return [list(d.keys()),list(d.values())]

def PieTwo(username):
    cursor=conn.cursor()
    cursor.execute(f'''
SELECT ORDER_NAME,COUNT(ORDER_ID)
FROM {username}_ALL_DATA
WHERE DATE= '{datetime.now().date()}'
GROUP BY ORDER_NAME''')
    d=dict(cursor.fetchall())
    return [list(d.keys()),list(d.values())]

def TodayNumberOrders(username):
    cursor=conn.cursor()
    cursor.execute(f'''
SELECT COUNT(DISTINCT(ORDER_ID))
FROM {username}_ALL_DATA
WHERE DATE = '{datetime.now().date()}' ''')
    return cursor.fetchall()[0][0]

def TodayRevPro(username):
    cursor=conn.cursor()
    cursor.execute(f'''
SELECT SUM(NET_PRICE)
FROM {username}_ALL_DATA
WHERE DATE= '{datetime.now().date()}' ''')
    revenue=cursor.fetchall()[0][0]
    cursor.execute(f'''
SELECT SUM(COST)
FROM {username}_ALL_DATA
WHERE DATE= '{datetime.now().date()}'  ''')
    cost=cursor.fetchall()[0][0]
    return [revenue,cost]

# Capture values for linechart from database
def today_sell_linechart(username,start_time='00:00:00',end_time='23:00:00',time_gap=1):
    cursor=conn.cursor()
    current_date=str(datetime.now().date())
    Time=[]
    Sell=[]
    start=start_time
    end=end_time
    time=int(start[0:2])
    for n in range(int(start[0:2]),int(end[0:2])):
        if time+time_gap>24:
            break
        if time<10:
            pt='0'+str(time)
            if time+time_gap>9:
                nt=str(time+time_gap)
            else:
                nt='0'+str(time+time_gap)
        else:
            pt=str(time)
            nt=str(time+time_gap)
        cursor.execute(f''' SELECT SUM(Price) AS Total_Price
                        FROM {username}_all_data
                        WHERE date = '{current_date}' AND time BETWEEN '{str(pt)+str(':00:00')}' AND '{str(nt)+str(':00:00')}';
                   ''')
        result=cursor.fetchall()
        for m in result:
            for k in m:
                if k:
                  Sell.append(int(k))
                else:
                    Sell.append(0)
                Time.append(pt+':00'+' to '+nt+':00')
        time+=time_gap
    return [Time,Sell]
def Orders(username):
    cursor=conn.cursor()
    Orders=[]
    query = f'''SELECT "customer_name","order_name","price","order_id","date","time","quantity" FROM {username}_ALL_DATA WHERE DATE = '{datetime.now().date()}' '''
    cursor.execute(query)
    result=cursor.fetchall()
    for n in result:
        n=list(n)
        dic={"CUSTOMER_NAME":n[0],"ORDER_NAME":n[1],"PRICE":n[2],"ORDER_ID":n[3],"DATE":n[4],"TIME":n[5],"QUANTITY":n[6]}
        Orders.append(dic)
    return Orders

def TopSelling_Product (username):
    labels=[]
    values=[]
    cursor=conn.cursor()
    cursor.execute(f''' SELECT order_name,SUM(NET_PRICE) AS Total_Price
                        FROM {username}_all_data
                        WHERE date = '{datetime.now().date()}'
                        GROUP BY order_name
                        ORDER BY SUM(NET_PRICE) DESC;
                   ''')
    result=cursor.fetchall()
    for k in result:
        labels.append(k[0])
        values.append(k[1])
    return [labels,values]

@app.route('/Success')
def Success(massage,cont):
    return render_template('SuccessMassage.html',Massage=massage,cont=cont)

@app.route('/Warning')
def Warning(massage,cont):
    return render_template('Warning.html',Massage=massage,cont=cont)

@app.route('/Track_Order' ,methods=['GET','POST'])
def Track():
    if request.method!='POST':
        return render_template('TrackOrder.html')
    order_id=request.form['OrderId']
    cursor=conn.cursor()
    cursor.execute(f'''
                    SELECT * FROM {session['username']}_ALL_DATA
                    WHERE ORDER_ID = '{order_id}' ''')
    res=cursor.fetchall()
    if res==[]:
        return 'Order is not exist'
    track_order_data=[]
    customer_name=res[0][0]
    date=res[0][4]
    time=res[0][5]
    order_items=[]
    total_amount=0
    for i in res:
        track_order_data.append({"Product_Name": i[1], "Product_Quantity": i[6], "Unit_Price": i[3]/i[6] ,"Price": i[3],'NetPrice':i[8]})
        order_items.append(i[1])
        total_amount+=i[3]
    session['track_order_data']=track_order_data
    return render_template('TrackOrder.html',customer_name=customer_name,order_items=order_items,order_id=order_id,date=date,time=time,total_amount=total_amount)

@app.route('/Track_Order/bill', methods=['POST'])
def TrackBill():
    customer_name=request.form['customer_name']
    order_id=request.form['order_id']
    date=request.form['date']
    time=request.form['time']
    return bill_functions.main(session['track_order_data'],customer_name='Harsh',email='',order_id=order_id,date=date,time=time)
if __name__ == '__main__':
    app.run(debug=True)