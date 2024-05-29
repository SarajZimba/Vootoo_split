from root.app import socketio
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
import pytz
import time
from root.auth.check import token_auth





@socketio.on('table_done')
def table_done(data):
        try:
            if "token" not in data  or "table_id" not in data  or "roomId" not in data  or "hash" not in data or not any([data,data["table_id"],data["roomId"],data["hash"],data["token"]]):
                return "Failure"
            token = data["token"]
            if not token_auth(token):
                cursor.close()
                mydb.close()
                roomid = "{}table_response_error".format(endpoint)
                socketio.emit(roomid, {"error":"Wrong token provided"})
                return "Failure"
            table_id = data["table_id"]
            endpoint=data["hash"]
            mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
            cursor = mydb.cursor(buffered=True)
            database_sql = "USE {};".format(os.getenv('database'))
            cursor.execute(database_sql)
            get_sql =f"""select Date,orderedAt,idtblorderTracker from tblorderTracker where idtblorderTracker=%s and not currentState='Completed'"""
            cursor.execute(get_sql,(table_id,),)
            temp_sql_data= cursor.fetchall() 
            if temp_sql_data ==[]:
                cursor.close()
                mydb.close()
                roomid = "{}table_response_error".format(endpoint)
                socketio.emit(roomid, {"error":"The entry for the id does not exist."})
                return "Failure"
            row_headers=[x[0] for x in cursor.description] 
            json_data=[]
            for result in temp_sql_data:
                json_data.append(dict(zip(row_headers,result))) 
            order_date = json_data[0]["Date"]
            ordertime = json_data[0]["orderedAt"]
            primarykey = json_data[0]["idtblorderTracker"]
            date_time_str = '{} {}'.format(order_date,ordertime)
            orderedAt = datetime.strptime(date_time_str,'%Y-%m-%d %H:%M:%S')
            current = datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime('%Y-%m-%d %H:%M:%S')
            current = datetime.strptime(current,'%Y-%m-%d %H:%M:%S')
            TotalTime= current-orderedAt
            total_time_seconds=TotalTime.total_seconds()
            TotalTime = time.strftime('%H:%M:%S', time.gmtime(total_time_seconds))
            ordertime_elapsed = "{}".format(str(TotalTime))
            current_time  =datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime('%H:%M:%S')
            success_sql = f"""insert into tblorderTracker (idtblorderTracker) values (%s) on duplicate key update completedAt=%s, TotalTime=%s, currentState='Completed'"""
            cursor.execute(success_sql,(table_id,current_time,ordertime_elapsed,),)
            mydb.commit()
            item_table_sql =f"""select idtblorderTracker_Details from tblorderTracker_Details where orderTrackerID=%s and completedAt=''"""
            cursor.execute(item_table_sql,(primarykey,),)
            temp_table_sql_data= cursor.fetchall() 
            row_headers=[x[0] for x in cursor.description] 
            json_item_data=[]
            for result in temp_table_sql_data:
                json_item_data.append(dict(zip(row_headers,result))) 
            for index,key in enumerate(json_item_data):
                order_number = json_item_data[index]["idtblorderTracker_Details"]
                item_sql =f"""select orderedAt,AvgPrepTime from tblorderTracker_Details where idtblorderTracker_Details=%s and completedAt=''"""
                cursor.execute(item_sql,(order_number,),)
                item_result = cursor.fetchall()
                if item_result == []:
                    return "No such entry"
                row_headers=[x[0] for x in cursor.description] 
                item_json_data=[]
                for res in item_result:
                    item_json_data.append(dict(zip(row_headers,res))) 
                current = datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime('%Y-%m-%d %H:%M:%S')
                current = datetime.strptime(current,'%Y-%m-%d %H:%M:%S')
                item_orderedAt =  item_json_data[0]["orderedAt"]
                item_date_time_str = '{} {}'.format(order_date,item_orderedAt)
                item_orderedTime = datetime.strptime(item_date_time_str,'%Y-%m-%d %H:%M:%S')
                item_TotalTime= current-item_orderedTime
                total_time_seconds=item_TotalTime.total_seconds()
                item_TotalTime = time.strftime('%H:%M:%S', time.gmtime(total_time_seconds))
                item_total_time=item_TotalTime
                item_TotalTime = "{} {}".format(order_date,item_TotalTime)
                item_total_time_taken = datetime.strptime(item_TotalTime,'%Y-%m-%d %H:%M:%S')
                Avgpreptime = item_json_data[0]["AvgPrepTime"]
                if Avgpreptime==""or Avgpreptime=="00:00:00":
                    prep_time_diff=""
                    avgtimediff=""
                elif Avgpreptime!="":   
                    prepTimedate= "{} {}".format(order_date,Avgpreptime)
                    prep_time_diff = datetime.strptime(prepTimedate,'%Y-%m-%d %H:%M:%S')
                    if prep_time_diff> item_total_time_taken:
                        time_taken = prep_time_diff-item_total_time_taken
                        total_second_time_taken = time_taken.total_seconds()
                        item_total_time_taken = time.strftime('%H:%M:%S', time.gmtime(total_second_time_taken))
                    else:
                        time_taken = item_total_time_taken-prep_time_diff
                        total_second_time_taken = time_taken.total_seconds()
                        item_total_time_taken = time.strftime('%H:%M:%S', time.gmtime(total_second_time_taken))
                    avgtimediff = "{}".format(str(item_total_time_taken))
                preptime_success_items_sql =f"""update tblorderTracker_Details set prepTimeDifference=%s, TotalTime=%s  where idtblorderTracker_Details=%s"""
                cursor.execute(preptime_success_items_sql,(avgtimediff,item_total_time,order_number,),)
                mydb.commit()
            success_items_sql =f"""update tblorderTracker_Details set completedAt=%s where orderTrackerID=%s and not completedAt = 'void' and completedAt=''"""
            cursor.execute(success_items_sql,(current_time,table_id,),)
            mydb.commit()
            cursor.close()
            mydb.close()
            roomid = "{}table_response".format(endpoint)
            socketio.emit(roomid, {"success":"The order has been marked as completed","table_id":int(data["table_id"])},broadcast=True)
            return "success"



        except Exception as error:
            data ={'error':str(error)}
            return data,400

