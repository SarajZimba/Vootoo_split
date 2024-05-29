from flask import Flask, request, Blueprint
app = Flask(__name__)
import mysql.connector
from flask_cors import CORS, cross_origin
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'secret!'
import os
from dotenv import load_dotenv
load_dotenv()
from flask_socketio import SocketIO
socketio = SocketIO(app, cors_allowed_origins="*",monitor_clients=True,async_mode='eventlet',allow_upgrades=False)
app_file3 = Blueprint('app_file3',__name__)

from root.auth.check import token_auth



@app_file3.route("/completed", methods=["POST"])
@cross_origin()
def completed_items():
    try:
        json = request.get_json()
        if "token" not in json or "end_date" not in json or "start_date" not in json not in json or "outlet_name" not in json or not any([json["token"],json["end_date"],json["start_date"],json["outlet_name"]]) or json["start_date"]=="" or json["token"] =="" or json["end_date"]=="" or json["outlet_name"] =="":
            data = {"error":"Some fields missing."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400

        start_date = json["start_date"]
        end_date = json["end_date"]
        outlet_name = json["outlet_name"]
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        get_category_sql = f"""select distinct category from tblorderTracker_Details"""
        cursor.execute(get_category_sql)
        category_result = cursor.fetchall()
        row_headers=[x[0] for x in cursor.description] 
        category_json_data=[]
        for res in category_result:
            category_json_data.append(dict(zip(row_headers,res)))
        item_type_arr=[]
        for x in category_json_data:
            item_type_arr.append(x["category"])
        main_json ={}
        for j in item_type_arr:
            individual_category_json  = []
            get_outlet_sql =f"""SELECT DISTINCT ItemName from tblorderTracker_Details where category=%s"""
            cursor.execute(get_outlet_sql,(j,),)
            result = cursor.fetchall()
            if result == []:
                individual_category_json = {"item_name":"No Items","quantity":0}
            elif result!=[]:
                row_headers=[x[0] for x in cursor.description] 
                json_data=[]
                for res in result:
                    json_data.append(dict(zip(row_headers,res)))
                for i in json_data:
                    item_name  = i["ItemName"]
                    item_count_sql =f"""SELECT SUM(a.Quantity) as items from tblorderTracker_Details a, tblorderTracker b where a.ItemName=%s and a.orderTrackerID = b.idtblorderTracker and b.Date BETWEEN %s and %s and b.outlet_Name =%s and not a.completedAt='' and not a.completedAt='void'"""
                    cursor.execute(item_count_sql,(item_name,start_date,end_date,outlet_name,),)
                    count_result = cursor.fetchall()
                    if result == []:
                        data = {"error":"Temporarily unavailable."}
                        return data,400
                    row_headers=[x[0] for x in cursor.description] 
                    item_countjson_data=[]
                    for res in count_result:
                        item_countjson_data.append(dict(zip(row_headers,res)))
                    item_count = item_countjson_data[0]["items"]
                    item_json = {"item_name":item_name,"quantity":item_count}
                    individual_category_json.append(item_json)
                    main_json[""+j+""]=individual_category_json

        cursor.close()
        mydb.close() 
        return main_json,200
    
    except Exception as error:
        data ={'error':str(error)}
        return data,400

