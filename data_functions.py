import streamlit as st
import psycopg2
import login_functions
from datetime import datetime 
import matplotlib.pyplot as plt
import streamlit_shadcn_ui as ui
#add new product in shoap by owner

conn = psycopg2.connect(os.environ["conn_str"])
cursor=conn.cursor()

def add_product(username):
    quantity=None
    st.title("Add A New Product 🏷️")
    form=st.form('Add Product Form')
    name = form.text_input("Enter Your Product Name")
    select_type=form.selectbox('Type Of Product',['Countable','Weightable'])
    if select_type=='Countable':
        quantity=form.number_input('Enter The Quantity Of Product in unit/Kg',value=0,step=1)
    if select_type=='Weightable':
        quantity=form.number_input('Enter The Quantity Of Product in unit/Kg ',value=0,step=1,placeholder='Enter Quantity in Kg')
    price=form.number_input('Enter Price Of Product',value=0,step=1)
    submitted=form.form_submit_button("ADD")
    if submitted:
        if len(name)!=0:
            if quantity>0:
                if price>0:
                    try:
                        cursor.execute(" INSERT INTO {}_PRODUCT_LIST (PRODUCT_NAME,QUANTITY,PRODUCT_TYPE,PRICE) VALUES ('{}','{}', '{}','{}')".format(username,name,int(quantity),select_type,int(price)))
                        conn.commit()
                        st.success('Product Saved Successfully')
                    except:
                        st.error('This Product Already Exist')
                else:
                    st.error('Enter Valid Price')
            else:
                 st.error('Enter Valid Quantity')
        else:
             st.error('Please Enter Product Name')
        
# take a new order by owner
             
def add_new_order():
    name='N'
    current_date_time = datetime.now()
    cursor=conn.cursor()
    cursor.execute(f''' SELECT PRODUCT_NAME FROM {login_functions.variable.username}_PRODUCT_LIST''')
    res=cursor.fetchall()
    options=[]
    for n in res:
        for m in list(n):
            options.append(m)
    st.title("Add A New Order")
    form=st.form(key='Add Order form')
    select_product=form.selectbox('Select Product',options)
    cursor.execute(f''' SELECT PRICE FROM {login_functions.variable.username}_PRODUCT_LIST WHERE PRODUCT_NAME='{select_product}' ''')
    res=cursor.fetchall()
    auto_value=[]
    for n in res:
        for m in list(n):
            auto_value.append(m)
    for n in options:
        if select_product==f'{n}':
            quantity=form.number_input('Enter The Quantity Of Product',value=0,step=1)
    price=form.number_input('Check Price Of Product',value=auto_value[0]*quantity)

    submitted=form.form_submit_button("ADD")
    if submitted:
        new_data=(str(name),str(select_product),price)
        cursor.execute(f'''
                             INSERT INTO {login_functions.variable.username}_ALL_DATA(CUSTOMER_NAME,ORDER_NAME) VALUES {new_data}
                      ''')
        conn.commit()
        conn.close()
        st.success("THANK YOU NEW ORDER SUCCESSFULLY ADDED")

def today_sell(username):
        conn = psycopg2.connect("postgresql://MYPROJECT20.COM:ZNfo9DxeFp-WoNzpTDJPmg@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=verify-full")
        cursor=conn.cursor()
        df=pd.DataFrame()
        l=["CUSTOMER_NAME","ORDER_NAME","PRICE","ORDER_ID","DATE","TIME"]
        st.subheader('''Your Today Total Sell Data''')
        for n in l:
            query = f'''SELECT {n} FROM {username}_ALL_DATA WHERE DATE = '{datetime.now().date()}' '''
            cursor.execute(query)
            result=cursor.fetchall()
            p=[]
            for k in result:
                for m in list(k):
                    p.append(m)
            df[n]=p
        st.dataframe(df)
        st.caption(f'''Total Total Sell {sum(df['PRICE'])}Rs''')
def sell_bar_graph(username):
    st.subheader("Today Top Sell Products Analysis")
    conn = psycopg2.connect("postgresql://MYPROJECT20.COM:ZNfo9DxeFp-WoNzpTDJPmg@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=verify-full")
    cursor=conn.cursor()
    current_date=str(datetime.now().date())
    df=pd.DataFrame(columns=['Sell','Today Selling Products'])
    cursor.execute(f''' SELECT order_name,SUM(Price) AS Total_Price
                        FROM {username}_all_data
                        WHERE date = '{current_date}'
                        GROUP BY order_name
                        ORDER BY SUM(Price) DESC;
                   ''')
    result=cursor.fetchall()
    
    for k in result:
        new_row={'Today Selling Products':k[0],'Sell':int(k[1])}
        df.loc[len(df)]=new_row
    st.bar_chart(data=df, x='Today Selling Products',y='Sell')
   
def today_sell_linechart(username,start_time='09:00:00',end_time='22:00:00',time_gap=1):
    st.subheader("Today Sell Time Analysis ")
    conn = psycopg2.connect("postgresql://MYPROJECT20.COM:ZNfo9DxeFp-WoNzpTDJPmg@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=verify-full")
    cursor=conn.cursor()
    current_date=str(datetime.now().date())
    df=pd.DataFrame()
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
    df['Sell']=Sell
    df['Time']=Time
    st.line_chart(data=df,x='Time',y='Sell')
def product_list(username):
    conn = psycopg2.connect("postgresql://MYPROJECT20.COM:ZNfo9DxeFp-WoNzpTDJPmg@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=verify-full")
    cursor=conn.cursor()
    cursor.execute(f'''
                    SELECT product_name,price,product_type,quantity,product_id
                    FROM {username}_product_list ''')
    result= cursor.fetchall()
    df = pd.DataFrame(columns=['PRODUCT_ID','PRODUCT_NAME','PRODUCT_PRICE','PRODUCT_TYPE','QUANTITY'])
    for n in result:
        new_row={'PRODUCT_ID':n[4],'PRODUCT_NAME':n[0],'PRODUCT_PRICE':n[1],'PRODUCT_TYPE':n[2],'QUANTITY':n[3]}
        df.loc[len(df)]=new_row
    st.table(df)
def edit_product_list(username):
    st.title('Edit Your Products 🛍️')
    st.divider( )
    conn = psycopg2.connect("postgresql://MYPROJECT20.COM:ZNfo9DxeFp-WoNzpTDJPmg@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=verify-full")
    cursor=conn.cursor()
    cursor.execute(f''' SELECT PRODUCT_NAME FROM {username}_PRODUCT_LIST ''')
    result=cursor.fetchall()
    product_name_options=[]
    for n in result:
        product_name_options.append(n[0])
    product=st.selectbox('Select A Product',options=product_name_options)
    edit=st.selectbox(f'Select What You want Change in {product}',options=['PRODUCT_NAME','PRICE','PRODUCT_TYPE','QUANTITY'])
    product_id=None
    cursor.execute(f''' SELECT PRODUCT_ID FROM {username}_PRODUCT_LIST WHERE PRODUCT_NAME='{product}' ''')
    result=cursor.fetchall()
    for n in result:
        product_id=n[0]
    with st.popover('Next'):
        st.warning('You are going to change sensitive data')
        new_value=None
        if edit=='PRODUCT_TYPE':
            new_value=st.selectbox('Select Your Choice',options=['Weightable','Countable'])
        else:
            if edit=='PRODUCT_NAME':
                new_value=st.text_input('Enter Product New Name')
            else:
                new_value=st.number_input(f'Enter Product New {edit.lower()}',step=1)
        button=st.button('Save The Changes')
        if button:
            cursor.execute(f''' SELECT PRODUCT_ID FROM {username}_PRODUCT_LIST WHERE PRODUCT_NAME='{product}' ''')
            result=cursor.fetchall()
            for n in result:
                product_id=n[0]
            if edit == 'PRODUCT_NAME' or edit =='PRODUCT_TYPE':
                cursor.execute(f''' UPDATE {username}_PRODUCT_LIST
                                    SET {edit} ='{new_value}'
                                    WHERE PRODUCT_ID = {product_id} ''')
                conn.commit()
                st.success('Successfully Changed')
                st.rerun()
            else:
                cursor.execute(f''' UPDATE {username}_PRODUCT_LIST
                                    SET {edit} ={new_value}
                                    WHERE PRODUCT_ID = {product_id} ''')
                conn.commit()
                st.success('Successfully Changed')
                st.rerun()
