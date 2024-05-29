from root.app import socketio
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
from root.auth.check import token_auth
import pytz
import time


@socketio.on('quantity_decrease')
def quantity_increase(data):
        try:
            if "token" not in data  or "item_id" not in data  or "hash" not in data:
                return "failure"
            token = data["token"]
            item_id = data["item_id"]
            endpoint = data["hash"]
            if not token_auth(token):
                cursor.close()
                mydb.close()
                roomid = "{}quantity_error".format(endpoint)
                socketio.emit(roomid, {"error":"Wrong token provided"})
                return "Failure"
            mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
            cursor = mydb.cursor(buffered=True)
            database_sql = "USE {};".format(os.getenv('database'))
            cursor.execute(database_sql)
            get_sql = f"""select * from tblorderTracker_Details where idtblorderTracker_Details=%s and not completedAt='void' and completedAt='' """
            cursor.execute(get_sql,(item_id,),)
            temp_sql_data= cursor.fetchall()       
            if temp_sql_data ==[]:
                cursor.close()
                mydb.close()
                roomid = "{}quantity_error".format(endpoint)
                socketio.emit(roomid,{"error":"Quantity error."})
                return "Failure"
            row_headers=[x[0] for x in cursor.description] 
            json_data=[]
            for res in temp_sql_data:
                json_data.append(dict(zip(row_headers,res)))
            quant = json_data[0]["Quantity"]
            itemname = json_data[0]["ItemName"]
            category = json_data[0]["category"]
            orderTrackerID = json_data[0]["orderTrackerID"]
            quantity = float(quant)
            if quantity<1 or quantity==1:
                return "Quantity value must be atleast one."
            quantity -=1
            quantity_sql = f"""insert into tblorderTracker_Details (idtblorderTracker_Details) values (%s) on duplicate key update Quantity=%s"""
            cursor.execute(quantity_sql,(item_id,quantity,),)
            mydb.commit()
            getDateSql=f"""select Date,KOTID from tblorderTracker where idtblorderTracker=%s"""
            cursor.execute(getDateSql,(orderTrackerID,),)
            temp_voidDate_sql_data= cursor.fetchall() 
            row_headers=[x[0] for x in cursor.description] 
            temp_Void_json_data=[]
            for result in temp_voidDate_sql_data:
                temp_Void_json_data.append(dict(zip(row_headers,result)))    
            itemOrderDate = temp_Void_json_data[0]["Date"]
            itemOrderedAt = json_data[0]["orderedAt"]
            void_date_time_str = '{} {}'.format(itemOrderDate,itemOrderedAt)
            void_orderedAt = datetime.strptime(void_date_time_str,'%Y-%m-%d %H:%M:%S')
            void_current = datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime('%Y-%m-%d %H:%M:%S')
            void_current = datetime.strptime(void_current,'%Y-%m-%d %H:%M:%S')
            void_TotalTime= void_current-void_orderedAt
            void_time_taken_seconds = void_TotalTime.total_seconds()
            void_time_taken = time.strftime('%H:%M:%S', time.gmtime(void_time_taken_seconds))
            void_current = datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime('%H:%M:%S')
            quantity_void_log_sql = f"""insert into tblorderTracker_Details (ItemName,orderedAt,completedAt,TotalTime,Quantity,orderTrackerID,voidAt,voidTotalTime,category) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(quantity_void_log_sql,(itemname,itemOrderedAt,"void","void",1,orderTrackerID,void_current,void_time_taken,category,),)
            mydb.commit()
            mydb.close()
            roomid = "{}quantity_response".format(endpoint)
            socketio.emit(roomid,{"success":"Quantity has been decreased","item_id":int(data["item_id"]),"quantity":quantity,"table_id":orderTrackerID},broadcast=True)
            return str(quantity)
        except Exception as error:
            data ={'error':str(error)}
            return data,400