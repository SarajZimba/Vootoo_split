
from root.app import app, socketio
from root.socket_routes.get_live import * 
from root.socket_routes.item_complete import *
from root.socket_routes.item_void import *
from root.socket_routes.join import * 
from root.socket_routes.order_seen import *
from root.socket_routes.quantity_decrease import *
from root.socket_routes.table_done import *
from root.socket_routes.table_void import *      



if __name__ == "__main__":
    socketio.run(app,debug=True,port=5001)    
    