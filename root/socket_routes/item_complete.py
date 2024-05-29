from root.app import socketio
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
import time
import pytz
from root.auth.check import token_auth


@socketio.on('item_complete')
def item_complete(data):
        try:
            if "roomId" not in data  or "item_id" not in data  or "hash" not in data  or "token" not in data or not any([data,data["item_id"],data["roomId"],data["hash"],data["token"]]):
                return "Failure"
            item_id = data["item_id"]
            endpoint=data["hash"]
            token = data["token"]
            if not token_auth(token):
                roomid = "{}itemresponse_error".format(endpoint)
                socketio.emit(roomid, {"error":"Wrong token provided"})
                return "Failure"
            mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
            cursor = mydb.cursor(buffered=True)
            database_sql = "USE {};".format(os.getenv('database'))
            cursor.execute(database_sql)
            get_sql =f"""select a.orderTrackerID,a.AvgPrepTime,a.orderedAt,b.Date from tblorderTracker_Details a, tblorderTracker b where a.idtblorderTracker_Details=%s and a.completedAt='' and a.orderTrackerID = b.idtblorderTracker"""
            cursor.execute(get_sql,(item_id,),)
            temp_sql_data= cursor.fetchall() 
            if temp_sql_data ==[]:
                cursor.close()
                mydb.close()
                roomid = "{}itemresponse_error".format(endpoint)
                socketio.emit(roomid, {"error":"The entry for the item id does not exist."})
                return "Failure"
            row_headers=[x[0] for x in cursor.description] 
            json_data=[]
            for result in temp_sql_data:
                json_data.append(dict(zip(row_headers,result))) 
            primary_key = json_data[0]["orderTrackerID"]
            ordertime = json_data[0]["orderedAt"]
            orderdate = json_data[0]["Date"]
            date_time_str = '{} {}'.format(orderdate,ordertime)
            orderedAt = datetime.strptime(date_time_str,'%Y-%m-%d %H:%M:%S')
            current = datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
            current_time  =datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime('%H:%M:%S')
            current_formatted = datetime.strptime(current,'%Y-%m-%d %H:%M:%S')
            TotalTime= current_formatted-orderedAt
            total_second_time_taken = TotalTime.total_seconds()
            total_ordertime_elapsed =  time.strftime('%H:%M:%S', time.gmtime(total_second_time_taken))
            TotalTime = time.strftime('%H:%M:%S', time.gmtime(total_second_time_taken))
            total_time_taken = "{} {}".format(orderdate,TotalTime)
            total_time_taken = datetime.strptime(total_time_taken,'%Y-%m-%d %H:%M:%S')
            ordertime_elapsed = "{}".format(str(total_ordertime_elapsed))
            AvgPrepTime = json_data[0]["AvgPrepTime"]  
            if AvgPrepTime!="" and AvgPrepTime!="00:00:00":    
                prepTimedate= "{} {}".format(orderdate,AvgPrepTime)
                prep_time_diff = datetime.strptime(prepTimedate,'%Y-%m-%d %H:%M:%S')
                if prep_time_diff> total_time_taken:
                    time_taken = prep_time_diff-total_time_taken
                    time_taken_seconds = time_taken.total_seconds()
                    time_taken = time.strftime('%H:%M:%S', time.gmtime(time_taken_seconds))
                else:
                    time_taken = total_time_taken-prep_time_diff
                    time_taken_seconds = time_taken.total_seconds()
                    time_taken = time.strftime('%H:%M:%S', time.gmtime(time_taken_seconds))
                avgtimediff = "{}".format(str(time_taken))
            elif AvgPrepTime=="" or AvgPrepTime=="00:00:00":
                avgtimediff = ""
            success_items_sql =f"""update tblorderTracker_Details set completedAt=%s, TotalTime=%s,prepTimeDifference=%s  where idtblorderTracker_Details=%s"""
            cursor.execute(success_items_sql,(current_time,ordertime_elapsed,avgtimediff,item_id,),)
            mydb.commit()
            count_sql =f"""select count(orderTrackerID) as table_count from tblorderTracker_Details where orderTrackerID=%s and TotalTime=''"""
            cursor.execute(count_sql,(primary_key,),)
            count_sql_data= cursor.fetchall() 
            row_headers=[x[0] for x in cursor.description] 
            count_json_data=[]
            for result in count_sql_data:
                count_json_data.append(dict(zip(row_headers,result))) 
            table_count= count_json_data[0]["table_count"]
            if table_count==0:
                date_get_sql =f"""select Date,orderedAt from tblorderTracker where idtblorderTracker=%s and not currentState='Completed'"""
                cursor.execute(date_get_sql,(primary_key,),)
                date_sql_data= cursor.fetchall() 
                row_headers=[x[0] for x in cursor.description] 
                date_json_data=[]
                for result in date_sql_data:
                    date_json_data.append(dict(zip(row_headers,result))) 
                ordertime = date_json_data[0]["orderedAt"]
                orderdate = date_json_data[0]["Date"]
                date_time_str = '{} {}'.format(orderdate,ordertime)
                orderedAt = datetime.strptime(date_time_str,'%Y-%m-%d %H:%M:%S')
                TotalTime= current_formatted-orderedAt
                time_taken_seconds = TotalTime.total_seconds()
                time_taken = time.strftime('%H:%M:%S', time.gmtime(time_taken_seconds))
                ordertime_elapsed = "{}".format(str(time_taken))
                success_sql =f"""insert into tblorderTracker (idtblorderTracker) values (%s) on duplicate key update completedAt=%s, TotalTime=%s, currentState='Completed'"""
                cursor.execute(success_sql,(primary_key,current_time,ordertime_elapsed,),)
                mydb.commit()
            cursor.close()
            mydb.close()
            roomid = "{}item_response".format(endpoint)
            socketio.emit(roomid, {"success":"The order for the item has been marked as completed","item_id":int(data["item_id"]),"primary_key":primary_key,"item_count":table_count},broadcast=True)
            return "success"
        except Exception as error:
            data ={'error':str(error)}
            return data,400

