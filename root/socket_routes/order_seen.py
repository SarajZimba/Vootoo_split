from root.app import socketio
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()
from root.auth.check import token_auth



@socketio.on('order_seen')
def order_seen(data):
        try:
            if "table_id" not in data  or "roomId" not in data  or "hash" not in data  or "token" not in data or not any([data,data["table_id"],data["roomId"],data["hash"]]):
                return "Failure"
            token = data["token"]
            if not token_auth(token):
                cursor.close()
                mydb.close()
                roomid = "{}orderseen_error".format(endpoint)
                socketio.emit(roomid, {"error":"Wrong token provided"})
                return "Failure"
            table_id = data["table_id"]
            endpoint=data["hash"]
            mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
            cursor = mydb.cursor(buffered=True)
            database_sql = "USE {};".format(os.getenv('database'))
            cursor.execute(database_sql)
            get_sql = f"""select currentState from tblorderTracker where idtblorderTracker=%s and not completedAt='void' and completedAt='' and not currentState='Completed'"""
            cursor.execute(get_sql,(table_id,),)
            temp_sql_data= cursor.fetchall()       
            if temp_sql_data ==[]:
                cursor.close()
                mydb.close()
                roomid = "{}orderseen_error".format(endpoint)
                socketio.emit(roomid,{"error":"The order is either void, completed, or already being prepared."})
                return "Failure"
            row_headers=[x[0] for x in cursor.description] 
            json_data=[]
            for result in temp_sql_data:
                json_data.append(dict(zip(row_headers,result))) 
            status = json_data[0]["currentState"]
            if status =="Cooking":
                roomid = "{}orderseen_error".format(endpoint)
                socketio.emit(roomid,{"error":"The order is already in the state 'Cooking'"})
                return "Failure"
            success_items_sql =f"""update tblorderTracker set currentState='Cooking' where idtblorderTracker=%s and not completedAt = 'void' and completedAt=''"""
            cursor.execute(success_items_sql,(table_id,),)
            mydb.commit()
            cursor.close()
            mydb.close()
            roomid = "{}orderseen_response".format(endpoint)
            socketio.emit(roomid,{"success":"Th e status for the order has been marked as cooking.","table_id":data["table_id"]},broadcast=True)
            return "success"

        except Exception as error:
            data ={'error':str(error)}
            return data,400