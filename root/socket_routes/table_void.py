from root.app import socketio
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()
from root.auth.check import token_auth



@socketio.on('table_void')
def table_void(data):
        try:
            if "token" not in data  or "table_id" not in data  or "roomId" not in data  or "hash" not in data or not any([data,data["table_id"],data["roomId"],data["hash"]]):
                return "Failure"
            token = data["token"]
            if not token_auth(token):
                cursor.close()
                mydb.close()
                roomid = "{}tablevoid_error".format(endpoint)
                socketio.emit(roomid, {"error":"Wrong token provided"})
                return "Failure"
            table_id = data["table_id"]
            endpoint=data["hash"]
            mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
            cursor = mydb.cursor(buffered=True)
            database_sql = "USE {};".format(os.getenv('database'))
            cursor.execute(database_sql)
            get_sql = f"""select currentState from tblorderTracker where idtblorderTracker=%s and not completedAt='void' and completedAt='' and not currentState='Completed' and not currentState='void'"""
            cursor.execute(get_sql,(table_id,),)
            temp_sql_data= cursor.fetchall()       
            if temp_sql_data ==[]:
                cursor.close()
                mydb.close()
                roomid = "{}tablevoid_error".format(endpoint)
                socketio.emit(roomid,{"error":"The order is either void, completed, does not exist, or is already being prepared."})
                return "Failure"
            success_items_sql =f"""update tblorderTracker set currentState='void' where idtblorderTracker=%s and not completedAt = 'void' and completedAt=''"""
            cursor.execute(success_items_sql,(table_id,),)
            mydb.commit()
            cursor.close()
            mydb.close()
            roomid = "{}tablevoid_response".format(endpoint)
            socketio.emit(roomid,{"success":"The status for the order has been marked as cooking.","item_id":data["item_id"]},broadcast=True)
            return "success"

        except Exception as error:
            data ={'error':str(error)}
            return data,400