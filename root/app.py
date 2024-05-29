from flask import Flask, request, Blueprint
app = Flask(__name__)
import mysql.connector
from datetime import datetime
from flask_cors import CORS, cross_origin
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'secret!'
import os
from dotenv import load_dotenv
load_dotenv()
from flask_socketio import SocketIO, emit,join_room,leave_room
socketio = SocketIO(app, cors_allowed_origins="*",monitor_clients=True,async_mode='eventlet',allow_upgrades=False)
import jwt
import pytz
import datetime

from root.flask_routes.report import app_file1
from root.flask_routes.outletnames import app_file2
from root.flask_routes.itemStats import app_file3
from root.flask_routes.login import app_file4
from root.flask_routes.stats import app_file5
from root.flask_routes.orderhistory import app_file6
from root.flask_routes.salesreport import app_file7
from root.flask_routes.postsales import app_file8
from root.flask_routes.deletesales import app_file9
from root.flask_routes.statsummary import app_file10
from root.flask_routes.chartsummary import app_file11
from root.flask_routes.purchasereq import app_file12
from root.flask_routes.reqget import app_file13
from root.flask_routes.reqdetails import app_file14
from root.flask_routes.reqfilter import app_file15
from root.flask_routes.reqfilterfirst import app_file16
from root.flask_routes.reqitemhistory import app_file17
from root.flask_routes.customersaleshistory import app_file18
from root.flask_routes.billinfo import app_file19
from root.flask_routes.customerComplimentary import app_file20
from root.flask_routes.graphstats import app_file21
from root.flask_routes.years import app_file22
from root.flask_routes.billsearch import app_file23
from root.flask_routes.customercredit import app_file24
from root.flask_routes.CustomerCreditInsert import app_file25
from root.flask_routes.customerCreditdetails import app_file26
from root.flask_routes.customerCreditcheck import app_file27
from root.flask_routes.customerCreditleft import app_file28

app.register_blueprint(app_file1)
app.register_blueprint(app_file2)
app.register_blueprint(app_file3)
app.register_blueprint(app_file4)
app.register_blueprint(app_file5)
app.register_blueprint(app_file6)
app.register_blueprint(app_file7)
app.register_blueprint(app_file8)
app.register_blueprint(app_file9)
app.register_blueprint(app_file10)
app.register_blueprint(app_file11)
app.register_blueprint(app_file12)
app.register_blueprint(app_file13)
app.register_blueprint(app_file14)
app.register_blueprint(app_file15)
app.register_blueprint(app_file16)
app.register_blueprint(app_file17)
app.register_blueprint(app_file18)
app.register_blueprint(app_file19)
app.register_blueprint(app_file20)
app.register_blueprint(app_file21)
app.register_blueprint(app_file22)
app.register_blueprint(app_file23)
app.register_blueprint(app_file24)
app.register_blueprint(app_file25)
app.register_blueprint(app_file26)
app.register_blueprint(app_file27)
app.register_blueprint(app_file28)


@app.route("/entry1", methods=["POST"])
@cross_origin()
def entry1():
    mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
    cursor = mydb.cursor(buffered=True)
    database_sql = "USE {};".format(os.getenv('database'))
    cursor.execute(database_sql)
    json_data = request.get_json()
    
    perm_outlet_orderID = json_data["outlet_orderID"]
    perm_orderTime = json_data["orderTime"]
    perm_completedAt = json_data["completedAt"]
    perm_totalTime = json_data["TotalTime"]
    perm_tableNum = json_data["tableNum"]
    perm_employee = json_data["employee"]
    perm_orderType = json_data["orderType"]
    perm_currentState = json_data["currentState"]
    perm_outlet_Name = json_data["outlet_Name"]
    perm_guests = json_data["Guest_count"]
    perm_OrderItemDetailsList = json_data["OrderItemDetailsList"]
    perm_kotid = json_data["KOTID"]
    date = datetime.date.today().strftime('%Y-%m-%d')

    try:
        # Insert main order details into tblorderTracker
        sql_order_tracker = """INSERT INTO tblorderTracker (outlet_orderID, Date, tableNum, orderedAt, completedAt, TotalTime, orderType, currentState, Quantity, outlet_Name, Employee, Guest_count, KOTID)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql_order_tracker, (perm_outlet_orderID, date, perm_tableNum, perm_orderTime, perm_completedAt, perm_totalTime, perm_orderType, perm_currentState, perm_guests, perm_outlet_Name, perm_employee, perm_guests, perm_kotid))
        mydb.commit()

        # Get the ID of the inserted order
        order_id = cursor.lastrowid

        # Insert each item detail into tblorderTracker_Details
        for item_details in perm_OrderItemDetailsList:
            item_name = item_details["ItemName"]
            item_quantity = item_details["Quantity"]
            item_modifications = item_details.get("Modifications", "")
            item_prep_time = item_details.get("AveragePrepTime", "")
            item_price = item_details["item_price"]
            item_category = item_details["category"]
            item_completedAt = item_details["completedAt"]
            item_totalTime = item_details["TotalTime"]
            item_prepTime = item_details["prepTimeDifference"]
            # item_voidAt = item_details["voidAt"]
            # item_voidTotalTime = item_details["voidTotalTime"]

            if "voidAt" in item_details and "voidTotalTime" in item_details:
                item_voidAt = item_details["voidAt"]
                item_voidTotalTime = item_details["voidTotalTime"]
            else:
                item_voidAt = None  # If not present, set to None
                item_voidTotalTime = None

            sql_item_details = """INSERT INTO tblorderTracker_Details (orderedAt, completedAt, TotalTime, ItemName, Quantity, Modification, AvgPrepTime, item_price, category, orderTrackerID, prepTimeDifference, voidAt, voidTotalTime)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql_item_details, (perm_orderTime, item_completedAt, item_totalTime, item_name, item_quantity, item_modifications, item_prep_time, item_price, item_category, order_id, item_prepTime, item_voidAt, item_voidTotalTime))
            mydb.commit()

        cursor.close()
        mydb.close()

        return json_data, 200  # Return a success response

    except Exception as error:
        data = {'error': str(error)}
        return data, 400  # Return an error response



@app.route("/entry", methods=["POST"])
@cross_origin()
def entry():
    mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
    cursor = mydb.cursor(buffered=True)
    database_sql = "USE {};".format(os.getenv('database'))
    cursor.execute(database_sql)
    json = request.get_json()
    TotalTime= ""
    completedAt= ""
    perm_Quantity=0
    
    formatted_date = datetime.date.today().strftime('%Y-%m-%d')
    perm_outlet_orderID = json["outlet_orderID"]
    perm_orderTime = json["orderTime"]
    perm_tableNum = json["tableNum"]
    perm_employee = json["employee"]
    perm_orderType = json["orderType"]
    perm_currentState = json["currentState"]
    perm_outlet_Name = json["outlet_Name"]
    perm_guests = json["Guest_count"]
    perm_OrderItemDetailsList = json["OrderItemDetailsList"] 
    OrderItemDetailsList_details=  perm_OrderItemDetailsList[0]
    perm_kotid = json["KOTID"]
    if perm_orderType =="Take-Away":
        json["Guest_count"]=0
        json["tableNum"]="Take-Away"
        perm_guests = 0
        perm_tableNum="Take-Away"
    if  perm_kotid=="" or OrderItemDetailsList_details=="" or OrderItemDetailsList_details==[]  or  perm_OrderItemDetailsList=="" or  perm_guests=="" or perm_outlet_Name=="" or perm_currentState=="" or perm_orderType=="" or perm_employee=="" or perm_tableNum=="" or perm_orderTime=="" or not any([perm_guests,perm_outlet_orderID,perm_orderTime,perm_tableNum,perm_employee,perm_orderType,perm_currentState,perm_outlet_Name]) or perm_outlet_orderID=="":
        data = {"error":"Some fields are missing."}
        return data,400
    check = True
    orderDetails_length = len(perm_OrderItemDetailsList)
    if orderDetails_length==0:
        data ={'error':"Some fields under 'OrderItemDetailsList' missing."}
        return data,400
    for y in range(orderDetails_length):
        for x in perm_OrderItemDetailsList:
            try:
                if x["orderTime"]==""or x["ItemName"]=="" or x["Quantity"]=="" or x["item_price"]=="" or x["category"]==""  or x["item_price"] is None or x["category"] is None or x["orderTime"]is None  or x["ItemName"]is None or x["Quantity"]is None  or x["item_price"] is None :
                    check =False 
                orderDetails_length = orderDetails_length - 1
            except Exception as error:
                check =False
    if not check:
        data ={'error':"Some fields under 'OrderItemDetailsList' missing."}
        return data,400
    else:
        try:
            sql =f"""INSERT INTO tblorderTracker (outlet_orderID,Date,tableNum,orderedAt,completedAt,TotalTime,orderType,currentState,Quantity,outlet_Name,Employee,Guest_count,KOTID) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(sql,(perm_outlet_orderID,formatted_date,perm_tableNum,perm_orderTime,completedAt,TotalTime,perm_orderType,perm_currentState,perm_Quantity,perm_outlet_Name,perm_employee,perm_guests,perm_kotid,),)
            mydb.commit()
            global ordertracker_id
            ordertracker_sql =f"""select idtblorderTracker from tblorderTracker order by idtblorderTracker desc limit 1"""
            cursor.execute(ordertracker_sql)
            mydb.commit()
            result = cursor.fetchall()
            row_headers=[x[0] for x in cursor.description] 
            json_data=[]
            for res in result:
                json_data.append(dict(zip(row_headers,res)))
            main_orderid = json_data[0]["idtblorderTracker"]
            json["table_id"]=main_orderid
            ordertracker_id = result[0][0]
            if ordertracker_sql == "":
                ordertracker_id=1
            OrderItemDetailsList = json["OrderItemDetailsList"]   
            OrderItemDetailsList_details=  OrderItemDetailsList
            temp_ordertime =""
            temp_ItemName =""
            temp_Quantity=0
            temp_Modifications= ""
            temp_AvgPrepTime =""
            temp_itemprice=""
            temp_orderType=""
            for i in OrderItemDetailsList_details:
                for j in i:
                    if j == "orderTime":
                        temp_ordertime= i[j]
                    if j == "ItemName":
                        temp_ItemName=i[j]
                    if j == "Quantity":
                        temp_Quantity = i[j]
                    if j == "ItemName":
                        temp_ItemName = i[j]
                    if j =="AveragePrepTime":
                        temp_AvgPrepTime =i[j]
                    if j =="Modifications":
                        temp_Modifications =i[j]
                    if j =="item_price":
                        temp_itemprice = i[j]
                    if j =="category":
                        temp_orderType=i[j]
                orderdetails_sql =f"""INSERT INTO tblorderTracker_Details (orderedAt,ItemName,completedAt,TotalTime,Quantity,Modification,orderTrackerID,AvgPrepTime,item_price,category) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                cursor.execute(orderdetails_sql,(temp_ordertime,temp_ItemName,completedAt,TotalTime,temp_Quantity,temp_Modifications,ordertracker_id,temp_AvgPrepTime,temp_itemprice,temp_orderType,),)
                mydb.commit()
                get_id_subitem=f"""select idtblorderTracker_Details from tblorderTracker_Details where orderedAt=%s and ItemName=%s and completedAt=%s and TotalTime=%s and Quantity=%s and Modification=%s and orderTrackerID=%s"""
                cursor.execute(get_id_subitem,(temp_ordertime,temp_ItemName,completedAt,TotalTime,temp_Quantity,temp_Modifications,ordertracker_id,),)
                sub_temp_sql_data= cursor.fetchall()
                row_headers=[x[0] for x in cursor.description] 
                subitem_json_data=[]
                for result in sub_temp_sql_data:
                    subitem_json_data.append(dict(zip(row_headers,result)))
                sub_id = subitem_json_data[0]["idtblorderTracker_Details"]
                i["item_id"]=sub_id
            cursor.close()
            mydb.close()
            roomid = "{}".format(perm_outlet_Name)
            encoded = jwt.encode({"outletName": roomid},'test@123', algorithm="HS256")
            socketio.emit(encoded, json,broadcast=True)
            return json,200
        
        
        except Exception as error:
            data ={'error':str(error)}
            return data,400










@app.route("/")
def index():
    return "working"



