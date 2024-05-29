
from root.app import socketio
import mysql.connector

import json
import re
from flask_cors import CORS
import os
from dotenv import load_dotenv
load_dotenv()
from flask_socketio import emit,join_room,leave_room
from root.auth.check import token_auth




@socketio.on('get_live')
def get_live(data):
        try:
            if "roomId" not in data or "token" not in data or not any([data,data["roomId"]]):
                return "Failure"
            outlet_name = data["outlet_name"]
            token = data["token"]
            if not token_auth(token):
                data = {'error':"Wrong token provided."}
                join_room(room_id)
                emit('get_live_error', data,to=room_id)
                leave_room  (room_id)
                return "Wrong token provided."
            room_id = data["roomId"]
            mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
            cursor = mydb.cursor(buffered=True)
            database_sql = "USE {};".format(os.getenv('database'))
            cursor.execute(database_sql)
            get_sql =f"""select KOTID,outlet_orderID,Guest_count,orderedAt,tableNum,Employee,orderType,currentState,outlet_Name ,idtblorderTracker from tblorderTracker where (currentState = 'Started' or currentState = 'Cooking') and outlet_Name=%s order by idtblorderTracker desc"""
            cursor.execute(get_sql,(outlet_name,),)
            temp_sql_data= cursor.fetchall()
            if temp_sql_data==[]:
                data = {'error':"Outlet name does not exist."}
                join_room(room_id)
                emit('get_live_error', data,to=room_id)
                leave_room  (room_id)
                return "Outlet name does not exist."
            row_headers=[x[0] for x in cursor.description] 
            json_data=[]
            for result in temp_sql_data:
                json_data.append(dict(zip(row_headers,result)))
            api_json = json.loads(json.dumps(json_data))
            temp_arr = []
            response_json = {}
            global arr
            for x in api_json:
                temp_arr.append(x["idtblorderTracker"])
                order_items_details_sql =f"""SELECT orderedAt,ItemName,CONVERT(Quantity,UNSIGNED INT),Modification,idtblorderTracker_Details,item_price FROM `tblorderTracker_Details` WHERE orderTrackerID =%s and completedAt=''"""
                cursor.execute(order_items_details_sql,(x["idtblorderTracker"],),)
                order_items_detail= cursor.fetchall()
                row_headers=[x[0] for x in cursor.description]
                order_items_detail_json=[]
                for temp_result in order_items_detail:
                    order_items_detail_json.append(dict(zip(row_headers,temp_result)))
                order_details_json = json.loads(json.dumps(order_items_detail_json))
                if order_details_json!=[]:
                    for t in order_details_json:
                        t["orderTime"] = t.pop("orderedAt")
                        t["Quantity"] = t.pop("CONVERT(Quantity,UNSIGNED INT)")
                        t["Modifications"] = t.pop("Modification")
                        t["item_id"]= t.pop("idtblorderTracker_Details")
                    json_structure = '{{"outlet_orderID": "{}", "orderTime": "{}", "tableNum": "{}",  "employee": "{}", "orderType": "{}", "currentState": "{}", "outlet_Name": "{}", "table_id":{}, "Guest_count":"{}","KOTID":"{}" ,"OrderItemDetailsList": {}}}'
                    parsed_req_json = json.loads(json.dumps(x))
                    json_structure=json_structure.format(parsed_req_json["outlet_orderID"],parsed_req_json["orderedAt"],parsed_req_json["tableNum"],parsed_req_json["Employee"],parsed_req_json["orderType"],parsed_req_json["currentState"],parsed_req_json["outlet_Name"],parsed_req_json["idtblorderTracker"],parsed_req_json["Guest_count"],parsed_req_json["KOTID"],json.dumps(order_details_json))
                response_json.setdefault("data",[]).append(json_structure)
            clean_response = re.sub("'{","{",str(response_json))
            clean_response= re.sub("}'","}",clean_response)
            clean_response= re.sub("'data'",'"data"',clean_response)
            cursor.close()
            mydb.close()
            join_room(room_id)
            emit('initial_load', clean_response,to=room_id)
            leave_room(room_id)
        except Exception as error:
            data ={'error':str(error)}
            return data,400
        


