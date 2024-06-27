import random 
import psycopg2
import re
import random
import base64
import smtplib
conn = psycopg2.connect("postgresql://MYPROJECT20.COM:ZNfo9DxeFp-WoNzpTDJPmg@almond-heron-1166.j77.cockroachlabs.cloud:26257/project?sslmode=verify-full")
cursor=conn.cursor()

alphabet_list = [chr(i) for i in range(ord('a'), ord('z')+1)]
def password_and_username_validator(password,email,username):
    def password_validator(password,email):
        cursor.execute(f''' SELECT PASSWORD FROM USERS WHERE EMAIL='{email}' ''')
        res=cursor.fetchall()
        for n in res:
            n=list(n)
            if n[0]==password:
                return True
            else:
                False
    def username_validator(username,email):
        cursor.execute(f''' SELECT USERNAME FROM USERS WHERE EMAIL='{email}' ''')
        res=cursor.fetchall()
        for n in res:
            n=list(n)
            if n[0]==username:
                return True
            else:
                False
    if password_validator(password,email):
        if username_validator(username,email):
            return True
        else:
            return False
    else:
        return False

def valid_email(mail):
    # Define the regular expression pattern for a valid email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Use re.match to check if the email matches the pattern
    match = re.match(pattern, mail)
    return bool(match)



def password_and_username_validator(password,username):

    cursor = conn.cursor()
    try:
        cursor.execute(f''' SELECT PASSWORD FROM USERS WHERE USERNAME='{username}' ''')
        res=cursor.fetchall()
        for n in res:
            n=list(n)
            if n[0]==password:
                return True
            else:
                False
    except:
            return False
    
# def change_password(email):
#     form=st.form("Change Password")
#     form.header('Reset Password')
#     ps = form.text_input("Enter Your Password")
#     cps = form.text_input("Re-enter Your Password")
#     submitted=form.form_submit_button("Submit")
#     if submitted:
#         if ps==cps:
#             try:
#                 cursor.execute(f''' UPDATE USERS
#                                     SET PASSWORD = '{cps}'
#                                     WHERE EMAIL = '{email}'
#                                     ''')                                       
#                 conn.commit()
#                 st.success('PASSWORD CHANGE SUCCESSFULLY')
#             except:
#                 st.error('THIS USER IS NOT EXIST')
#         else:
#             st.warning('Password is not same ! Please check')
# session['bill_products'].append({"description": select_product, "quantity": quantity, "unit_price": price/quantity ,"amount": price,'discount':'5%'})

def username_exist(username):
    cursor.execute(f'''SELECT * FROM USERS
                       WHERE USERNAME= '{username}' ''')
    res=cursor.fetchall()
    if res==[]:
        return True
    else:
        return False
    
def email_exist(email):
    cursor.execute(f'''
    SELECT * FROM USERS
    WHERE EMAIL='{email}' ''')
    if cursor.fetchall()==[]:
        return True
    return False

def create_tables(username):
    cursor.execute(f'''
    CREATE TABLE {username}_ALL_DATA (
        CUSTOMER_NAME VARCHAR(100),
        ORDER_NAME VARCHAR(100),
        ORDER_ID VARCHAR(100),
        PRICE INT,
        DATE DATE,
        TIME TIME,
        QUANTITY FLOAT,
        COST FLOAT,
        NET_PRICE FLOAT
    )''')
    conn.commit()

    cursor.execute(f'''
    CREATE TABLE {username}_PRODUCT_LIST (
        PRODUCT_NAME VARCHAR(100) PRIMARY KEY,
        QUANTITY INT CHECK (QUANTITY >= 0),
        PRODUCT_TYPE VARCHAR(10),
        PRICE INT,
        PRODUCT_ID INT,
        COST_PRICE FLOAT,
        DISCOUNT FLOAT
    )''')
    conn.commit()

def data_sender(mail,username,name):
    l=[]
    for n in range(8):
        a=random.choice(alphabet_list)
        l.append(str(a))
    password="".join(l)
    def password_sender(mail):
        subject='Email Varification'
        message=f''' 
Your password is {password} 
Do not share this password to anyone.


if you are not then please inform us at kumarh18999@gmail.com
Thank You ..
'''
        server=smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login("kumarh18999@gmail.com",password="lnip xkba bauv ctsp")
        server.sendmail("kumarh18999@gmail",{mail},msg=f"Subject: {subject}\n\n{message}")
        server.quit()
    def database(name,user_name,mail,password):

        cursor.execute('''INSERT INTO USERS (USERNAME, PASSWORD, NAME, EMAIL) VALUES (%s, %s, %s, %s)''',
                       (user_name, password, name, mail))
        conn.commit()

    try:
        password_sender(mail)
    except:
        return False
    create_tables(username)
    database(name,username,mail,password)
    return True