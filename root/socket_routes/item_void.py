from root.app import socketio
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
import pytz
import time
from root.auth.check import token_auth




@socketio.on('item_void')
def item_void(data):
        try:
            if "roomId" not in data  or "item_id"  not in data  or "hash" not in data  or "token" not in data or  not any([data,data["item_id"],data["roomId"],data["hash"],data["token"]]):
                return "Failure"
            item_id = data["item_id"]
            endpoint=data["hash"]
            token = data["token"]
            if not token_auth(token):
                cursor.close()
                mydb.close()
                roomid = "{}itemvoid_error".format(endpoint)
                socketio.emit(roomid, {"error":"Wrong token provided"})
                return "Failure"
            
            mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
            cursor = mydb.cursor(buffered=True)
            database_sql = "USE {};".format(os.getenv('database'))
            cursor.execute(database_sql)
            get_sql =f"""select * from tblorderTracker_Details where idtblorderTracker_Details=%s and not completedAt='void' and completedAt=''"""
            cursor.execute(get_sql,(item_id,),)
            temp_sql_data= cursor.fetchall() 
            if temp_sql_data ==[]:
                cursor.close()
                mydb.close()
                roomid = "{}itemvoid_error".format(endpoint)
                socketio.emit(roomid,{"error":"The item is either already void or does not exist"})
                return "Failure"
            row_headers=[x[0] for x in cursor.description] 
            json_data=[]
            for result in temp_sql_data:
                json_data.append(dict(zip(row_headers,result)))
            orderTrackerID=json_data[0]["orderTrackerID"]
            category=json_data[0]["category"]
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
            ordertime_elapsed="void"
            table_id = json_data[0]["orderTrackerID"]
            void_current = datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime('%H:%M:%S')
            success_items_sql =f"""update tblorderTracker_Details set completedAt='void', TotalTime=%s,voidAt=%s,voidTotalTime=%s,category=%s  where idtblorderTracker_Details=%s and TotalTime=''"""
            cursor.execute(success_items_sql,(ordertime_elapsed,void_current,void_time_taken,category,item_id,),)
            mydb.commit()
            count_sql =f"""select count(orderTrackerID) as table_count from tblorderTracker_Details where orderTrackerID=%s and not TotalTime = 'void'"""
            cursor.execute(count_sql,(table_id,),)
            count_sql_data= cursor.fetchall() 
            row_headers=[x[0] for x in cursor.description] 
            count_json_data=[]
            for result in count_sql_data:
                count_json_data.append(dict(zip(row_headers,result))) 
            table_count= count_json_data[0]["table_count"]
            table_count_sql =f"""select count(orderTrackerID) as table_count from tblorderTracker_Details where orderTrackerID=%s and TotalTime = ''"""    
            cursor.execute(table_count_sql,(table_id,))
            count_sql_data= cursor.fetchall() 
            row_headers=[x[0] for x in cursor.description] 
            table_count_json_data=[]
            for result in count_sql_data:
                table_count_json_data.append(dict(zip(row_headers,result)))
            item_count = table_count_json_data[0]["table_count"]
            if table_count>0 and item_count==0:
                date_get_sql = f"""select Date,orderedAt from tblorderTracker where idtblorderTracker=%s and not currentState='Completed'"""
                cursor.execute(date_get_sql,(table_id,),)
                date_sql_data= cursor.fetchall() 
                row_headers=[x[0] for x in cursor.description] 
                date_json_data=[]
                for result in date_sql_data:
                    date_json_data.append(dict(zip(row_headers,result))) 
                ordertime = date_json_data[0]["orderedAt"]
                date_time_str = '{}'.format(ordertime)
                orderedAt = datetime.strptime(date_time_str,'%H:%M:%S')
                current = datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime('%H:%M:%S')
                current = datetime.strptime(current,'%H:%M:%S')
                TotalTime= current-orderedAt
                time_taken_seconds = TotalTime.total_seconds()
                time_taken = time.strftime('%H:%M:%S', time.gmtime(time_taken_seconds))
                order_total_time_taken = datetime.strptime(str(time_taken),'%H:%M:%S')
                ordertime_elapsed = "{}".format(str(order_total_time_taken.time()))
                current_time  =datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime('%H:%M:%S')
                success_sql =f"""insert into tblorderTracker (idtblorderTracker) values (%s) on duplicate key update completedAt=%s, TotalTime=%s, currentState='Completed'"""
                cursor.execute(success_sql,(table_id,current_time,ordertime_elapsed,),)
                mydb.commit()
            if table_count==0 and item_count==0:
                count_sql =f"""select count(orderTrackerID) as cooked_count from tblorderTracker_Details where orderTrackerID=%s and completedAt='Completed'"""
                cursor.execute(count_sql,(table_id,),)
                count_sql_data= cursor.fetchall() 
                row_headers=[x[0] for x in cursor.description] 
                count_json_data=[]
                for result in count_sql_data:
                    count_json_data.append(dict(zip(row_headers,result))) 
                table_count= count_json_data[0]["cooked_count"]
                void_sql =f"""insert into tblorderTracker (idtblorderTracker) values (%s) on duplicate key update completedAt='void', TotalTime='void', currentState='void'"""
                cursor.execute(void_sql,(table_id,),)
                mydb.commit()
            cursor.close()
            mydb.close()
            roomid = "{}itemvoid_response".format(endpoint)
            socketio.emit(roomid,{"success":"The order for the item has been marked as void","item_id":data["item_id"],"table_id":table_id,"item_count":item_count},broadcast=True)
            return "success"
        except Exception as error:
            data ={'error':str(error)}
            return data,400