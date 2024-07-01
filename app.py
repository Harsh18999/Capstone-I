from flask import Flask, render_template, request,session,redirect
import bill_functions
from datetime import datetime
import login_functions
import calendar
from datetime import datetime
import random
import psycopg2
import os

app = Flask(__name__)
app.secret_key = 'Secret'
conn = psycopg2.connect(os.environ["conn_str"])

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
        return render_template('Notification.html',Title='Invalid',Massage='Invalid username or password',cont='/')
    
@app.route('/Signup',methods=['POST'])
def Signup():
    name=request.form['Name']
    username=request.form['username']
    email=request.form['email']
    if login_functions.email_exist(email=email):
        if login_functions.username_exist(username=username):
            if login_functions.data_sender(name=name,mail=email,username=username):
                return render_template('Notification.html',Title='Account Successfully Created',Massage='Your Account Successfully Created and Password has been sent in your given email. Please Login to Access Your account. Thank You',cont='/')
            else:
                return render_template('Notification.html',Title='Some Error Occuured',Massage='Please Try Again',cont='/')
        else:
            return render_template('Notification.html',Title='Username Warning',Massage='Given username already exist',cont='/')
    else:
        return render_template('Notification.html',Title='Account already exist',Massage='Given details already exist',cont='/')
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
        return render_template('Notification.html',Title='Please Log-in',Massage='Please login to access our services',cont='/')
    
# Fetch Price Directly From Database
def fetch_discount(username,product_name):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
                    SELECT DISCOUNT 
                    FROM {username}_PRODUCT_LIST
                    WHERE PRODUCT_NAME = '{product_name}' ''')
    return cursor.fetchall()[0][0]

def fetch_price(username, product_name):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor = conn.cursor()
    cursor.execute(f"SELECT PRICE FROM {username}_PRODUCT_LIST WHERE PRODUCT_NAME='{product_name}'")
    res = cursor.fetchone()
    return res[0] if res else None

# Capture Products list from database
def options(username):
    conn = psycopg2.connect(os.environ["conn_str"])
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
@app.route('/add_new_order/next' ,methods=['POST'])
def next():
        if request.method=='POST':
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
    CustomerEmail=request.form['customer_email']
    billStatus=request.form.get('bill')

    if CustomerName=='Mr ':
        CustomerName='Unknown'
        
    order_id=generate_order_id()

    for n in session['bill_products']:

        cost=CostCapture(n['Product_Name'])
        if add_product(username=session['username'],customer_name=CustomerName, select_product=n['Product_Name'], price=n['Price'], quantity=n['Product_Quantity'],order_id=order_id,cost=cost*n['Product_Quantity'],net_price=n['NetPrice']):
            pass
        else:
            conn = psycopg2.connect(os.environ["conn_str"])
            cursor=conn.cursor()
            cursor.execute(f'''
                            DELETE FROM {session['username']}_ALL_DATA
                            WHERE ORDER_ID = '{order_id}' ''')
            conn.commit()
            return Warning(massage=f'Please check the stocks of {n["Product_Name"]}',cont='/My_Products')
    if billStatus=='yes':
        if bill_functions.send_bill(customer_email=CustomerEmail,customer_name=CustomerName,items=session['bill_products']):
            pass
        else:
            return render_template('Warning.html',cont='/add_new_order/next')
    session['bill_products']=[]
    session.modified=True
    return Success(massage=f'Order Number {order_id} Successfully Saved, Thank you.',cont='/add_new_order')
#Send Bill 

# Cost capture
def CostCapture(product):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
                   SELECT COST_PRICE
                   FROM {session['username']}_PRODUCT_LIST
                   WHERE PRODUCT_NAME = '{product}'
                   ''')
    return cursor.fetchall()[0][0]

# Add order details on database

def add_product(username,customer_name,select_product,price,quantity,order_id,cost,net_price):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor = conn.cursor()
    current_date_time = datetime.now()
    try:
        cursor.execute(f'''
                        UPDATE {username}_PRODUCT_LIST
                        SET QUANTITY = QUANTITY-{quantity}
                        WHERE PRODUCT_NAME = '{select_product}'; ''')
        conn.commit()
    except:
        conn = psycopg2.connect(os.environ["conn_str"])
        cursor=conn.cursor()
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

# Edit products list in database
@app.route('/edit_product')
def edit_product_list():
    conn = psycopg2.connect(os.environ["conn_str"])
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
    if selected_type == 'DELETE':
        delete_product(selected_product=selected_product)
        return render_template('SuccessMassage.html',Massage=f'{selected_product} successfully deleted. Thank You',cont='/My_Products')
    return render_template('EditProduct.html',Product=selected_product,Edit=selected_type,next=True,Selected_Type=selected_type)
def delete_product(selected_product):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
                    DELETE FROM {session['username']}_PRODUCT_LIST
                    WHERE PRODUCT_NAME = '{selected_product}' ''')
    conn.commit()
    pass

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
    conn = psycopg2.connect(os.environ["conn_str"])
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
        return render_template('SuccessMassage.html',Massage=f'{product} successfully Edited. Thank You',cont='/My_Products')


# My Products
@app.route('/My_Products')
def My_Products():
    if 'username' not in session:
        return render_template('Notification.html',Title='Please Log-in',Massage='Please login to access our services',cont='/')
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''SELECT * FROM {session['username']}_PRODUCT_LIST''')
    all_data=cursor.fetchall()
    return render_template('MyProducts.html',Products=all_data)


# Monthly Dashboard
@app.route('/MonthSell')
def MonthSell():
    if 'username' not in session:
        return render_template('Notification.html',Title='Please Log-in',Massage='Please login to access our services',cont='/')
    month=datetime.now().month
    year=datetime.now().year
    HistRes=Hist(session['username'],month=month,year=year)
    LineChart=lineChart(session['username'],month=month,year=year)
    PieChart=Pie(session['username'],month=month,year=year)
    OrderDist=NumOrders(session['username'],month=month,year=year)
    NumberOfOrders=NumberOrders(session['username'],month=month,year=year)
    revpro=RevPro(session['username'],month=month,year=year)
    Total_Revenue=round(revpro[0],2)
    Total_Cost=round(revpro[1],2)
    return render_template('Dashboard.html',Title='CURRENT MONTH SELL DASHBOARD',Orders=Total_Orders(session['username'],month=month,year=year),Hist_labels=HistRes[0],Hist_values=HistRes[1],LineChart_labels=LineChart[0],LineChart_values=LineChart[1],PieChart1_labels=PieChart[0],PieChart1_values=PieChart[1],PieChart2_labels=OrderDist[0],PieChart2_values=OrderDist[1],Total_Orders=NumberOfOrders,Total_Revenue=Total_Revenue,Total_Cost=Total_Cost,Total_Profit=float(Total_Revenue)-float(Total_Cost))


def Hist(username,month,year):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
                   SELECT ORDER_NAME,SUM(PRICE)
                   FROM {username}_ALL_DATA
                   WHERE EXTRACT(MONTH FROM DATE )= {month} AND EXTRACT(YEAR FROM DATE)= {year}
                   GROUP BY ORDER_NAME
    ''')
    labels=[]
    values=[]
    for n in cursor.fetchall():
        labels.append(n[0])
        values.append(n[1])
    return [labels,values]


def lineChart(username,month,year):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    labels=[]
    values=[]
    date=f'{year}-{month}-'
    days=calendar.monthrange(year,month)[1]
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


def Total_Orders(username,month,year):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    TotalData=[]
    query = f''' SELECT "customer_name","order_name","price","order_id","date","time","quantity" FROM {username}_ALL_DATA WHERE EXTRACT(MONTH FROM DATE )= {month} AND EXTRACT(YEAR FROM DATE)= {year} '''
    cursor.execute(query)
    result=cursor.fetchall()
    for n in result:
        n=list(n)
        dic={"CUSTOMER_NAME":n[0],"ORDER_NAME":n[1],"PRICE":n[2],"ORDER_ID":n[3],"DATE":n[4],"TIME":n[5],"QUANTITY":n[6]}
        TotalData.append(dic)

    return TotalData

def Pie(username,month,year):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
    SELECT ORDER_NAME,CAST(SUM(NET_PRICE) AS INTEGER)-CAST(SUM(COST) AS INTEGER)
    FROM {username}_ALL_DATA
    WHERE EXTRACT(MONTH FROM DATE)={month} AND EXTRACT(YEAR FROM DATE)= {year}
    GROUP BY ORDER_NAME''')
    d=cursor.fetchall()
    d=dict(d)
    return [list(d.keys()),list(d.values())]

def NumOrders(username,month,year):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
    SELECT ORDER_NAME,COUNT(ORDER_ID)
    FROM {username}_ALL_DATA
    WHERE EXTRACT(MONTH FROM DATE)={month} AND EXTRACT(YEAR FROM DATE)= {year}
    GROUP BY ORDER_NAME''')
    d=dict(cursor.fetchall())
    return [list(d.keys()),list(d.values())]

def NumberOrders(username,month,year):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
    SELECT COUNT(DISTINCT(ORDER_ID))
    FROM {username}_ALL_DATA 
    WHERE EXTRACT(MONTH FROM DATE)={month} AND EXTRACT(YEAR FROM DATE)= {year}''')
    return cursor.fetchall()[0][0]

def RevPro(username,month,year):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
    SELECT SUM(PRICE)
    FROM {username}_ALL_DATA
    WHERE EXTRACT(MONTH FROM DATE)={month} AND EXTRACT(YEAR FROM DATE)= {year} ''')
    revenue=cursor.fetchall()[0][0]
    cursor.execute(f'''
    SELECT SUM(COST)
    FROM {username}_ALL_DATA
    WHERE EXTRACT(MONTH FROM DATE)={month} AND EXTRACT(YEAR FROM DATE)= {year} ''')
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
            conn = psycopg2.connect(os.environ["conn_str"])
            cursor=conn.cursor()
            cursor.execute(f'''
                            INSERT INTO {session['username']}_PRODUCT_LIST
                            (PRODUCT_NAME,PRICE,PRODUCT_ID,QUANTITY,DISCOUNT,COST_PRICE,PRODUCT_TYPE) VALUES ('{ProductName}',{Price},{ProductId},{Quantity},{Discount},{CostPrice},'{ProductType}')''')
            conn.commit() 
            return render_template('SuccessMassage.html',Massage=f'{ProductName} Successfully saved',cont='/My_Products')
        else:
            return render_template('AddNewProduct.html')
    else:
        return render_template('Notification.html',Title='Please Log-in',Massage='Please login to access our services',cont='/')

@app.route('/Dashboard')
def dash():
    if 'username' not in session:
        return render_template('Notification.html',Title='Please Log-in',Massage='Please login to access our services',cont='/')
    current_date=datetime.now().date()
    orders=Orders(session['username'],current_date)
    Hist=TopSelling_Product(session['username'],current_date)
    pie1=PieOne(username=session['username'],date=current_date)
    pie2=PieTwo(session['username'],date=current_date)
    line_chart=today_sell_linechart(username=session['username'],start_time='00:00:00',end_time='23:00:00',time_gap=2,date=current_date)
    revpro=TodayRevPro(session['username'],current_date)
    Total_Revenue=round(revpro[0],2) if revpro[0] else 0
    Total_Cost=round(revpro[1],2) if revpro[1] else 0
    Total_Profit=Total_Revenue-Total_Cost
    Total_Orders=TodayNumberOrders(session['username'],current_date)
    return render_template('Dashboard.html',Title='TODAY SELL DASHBOARD',Hist_labels=Hist[0],Hist_values=Hist[1],LineChart_labels=line_chart[0],LineChart_values=line_chart[1],PieChart1_labels=pie1[0],PieChart1_values= pie1[1],PieChart2_labels=pie2[0],PieChart2_values=pie2[1],Total_Revenue=Total_Revenue,Total_Cost=Total_Cost,Total_Orders=Total_Orders,Total_Profit=round(Total_Profit,2),Orders=orders)

def PieOne(username,date):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
                    SELECT ORDER_NAME,CAST(SUM(NET_PRICE) AS FLOAT)-CAST(SUM(COST) AS FLOAT)
                    FROM {username}_ALL_DATA
                    WHERE DATE= '{date}'
                    GROUP BY ORDER_NAME ''')
    d=cursor.fetchall()
    d=dict(d)
    return [list(d.keys()),list(d.values())]

def PieTwo(username,date):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
                    SELECT ORDER_NAME,COUNT(ORDER_ID)
                    FROM {username}_ALL_DATA
                    WHERE DATE= '{date}'
                    GROUP BY ORDER_NAME''')
    d=dict(cursor.fetchall())
    return [list(d.keys()),list(d.values())]

def TodayNumberOrders(username,date):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
                    SELECT COUNT(DISTINCT(ORDER_ID))
                    FROM {username}_ALL_DATA
                    WHERE DATE = '{date}' ''')
    return cursor.fetchall()[0][0]

def TodayRevPro(username,date):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
                    SELECT SUM(NET_PRICE)
                    FROM {username}_ALL_DATA
                    WHERE DATE= '{date}' ''')
    revenue=cursor.fetchall()[0][0]
    cursor.execute(f'''
                   SELECT SUM(COST)
                   FROM {username}_ALL_DATA
                   WHERE DATE= '{date}'  ''')
    cost=cursor.fetchall()[0][0]
    return [revenue,cost]

# Capture values for linechart from database
def today_sell_linechart(username,date,start_time='00:00:00',end_time='23:00:00',time_gap=1):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
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
                            WHERE date = '{date}' AND time BETWEEN '{str(pt)+str(':00:00')}' AND '{str(nt)+str(':00:00')}';
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


def Orders(username,date):
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    Orders=[]
    query = f'''SELECT "customer_name","order_name","price","order_id","date","time","quantity" FROM {username}_ALL_DATA WHERE DATE = '{date}' '''
    cursor.execute(query)
    result=cursor.fetchall()
    for n in result:
        n=list(n)
        dic={"CUSTOMER_NAME":n[0],"ORDER_NAME":n[1],"PRICE":n[2],"ORDER_ID":n[3],"DATE":n[4],"TIME":n[5],"QUANTITY":n[6]}
        Orders.append(dic)
    return Orders


def TopSelling_Product (username,date):
    labels=[]
    values=[]
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f''' SELECT order_name,SUM(NET_PRICE) AS Total_Price
                        FROM {username}_all_data
                        WHERE date = '{date}'
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
    conn = psycopg2.connect(os.environ["conn_str"])
    cursor=conn.cursor()
    cursor.execute(f'''
                    SELECT * FROM {session['username']}_ALL_DATA
                    WHERE ORDER_ID = '{order_id}' ''')
    res=cursor.fetchall()
    if res==[]:
        return render_template('Warning.html',Massage='Order is not exist',cont='/Track_Order')
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
    return bill_functions.main(session['track_order_data'],customer_name=customer_name,email='',order_id=order_id,date=date,time=time)


@app.route('/another_day_sell',methods=['POST','GET'])
def AnotherDaySell():
    if 'username' in session:
        if request.method=='POST':
            current_date=request.form['date']
            orders=Orders(session['username'],current_date)
            Hist=TopSelling_Product(session['username'],current_date)
            pie1=PieOne(username=session['username'],date=current_date)
            pie2=PieTwo(session['username'],date=current_date)
            line_chart=today_sell_linechart(username=session['username'],start_time='00:00:00',end_time='23:00:00',time_gap=2,date=current_date)
            revpro=TodayRevPro(session['username'],current_date)
            Total_Revenue= round(revpro[0],2) if revpro[0] else 0
            Total_Cost= round(revpro[1],2) if revpro[1] else 0
            Total_Profit=Total_Revenue-Total_Cost
            Total_Orders=TodayNumberOrders(session['username'],current_date)
            return render_template('Dashboard.html',Title=current_date,Hist_labels=Hist[0],Hist_values=Hist[1],LineChart_labels=line_chart[0],LineChart_values=line_chart[1],PieChart1_labels=pie1[0],PieChart1_values= pie1[1],PieChart2_labels=pie2[0],PieChart2_values=pie2[1],Total_Revenue=revpro[0],Total_Cost=revpro[1],Total_Orders=Total_Orders,Total_Profit=Total_Profit,Orders=orders)
        
        return render_template('AnotherDaySell.html')
    
    return render_template('Notification.html',Title='Please Log-in',Massage='Please login to access our services',cont='/')
    

@app.route('/another_month_sell',methods=['POST','GET'])
def AnotherMonthSell():
    if 'username' in session:
        if request.method=='POST':
            month=request.form['month']
            year=int(month[:4])
            month=int(month[5:])
            HistRes=Hist(session['username'],month=month,year=year)
            LineChart=lineChart(session['username'],month=month,year=year)
            PieChart=Pie(session['username'],month=month,year=year)
            OrderDist=NumOrders(session['username'],month=month,year=year)
            NumberOfOrders=NumberOrders(session['username'],month=month,year=year)
            revpro=RevPro(session['username'],month=month,year=year)
            Total_Revenue=round(revpro[0]) if revpro[0] else 0
            Total_Cost= round(revpro[1]) if revpro[1] else 0
            return render_template('Dashboard.html',Title=f'{month}-{year}',Orders=Total_Orders(session['username'],month=month,year=year),Hist_labels=HistRes[0],Hist_values=HistRes[1],LineChart_labels=LineChart[0],LineChart_values=LineChart[1],PieChart1_labels=PieChart[0],PieChart1_values=PieChart[1],PieChart2_labels=OrderDist[0],PieChart2_values=OrderDist[1],Total_Orders=NumberOfOrders,Total_Revenue=round(Total_Revenue,2),Total_Cost=round(Total_Cost,2),Total_Profit=round(float(Total_Revenue)-float(Total_Cost),2))
        
        return render_template('AnotherMonthSell.html')
    
    return render_template('Notification.html',Title='Please Log-in',Massage='Please login to access our services',cont='/')
@app.route('/Back')
def back():
    return redirect('/')

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')
