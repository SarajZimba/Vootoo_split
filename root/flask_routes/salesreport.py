from flask import  Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file7= Blueprint('app_file7',__name__)
from root.auth.check import token_auth

@app_file7.route("/saleshistory", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()
        if "token" not in json  or not any([json["token"]])  or json["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400
        if "outlet" not in json or "dateStart" not in json or "dateEnd" not in json:
            data = {"error":"Some fields are missing"}
            return data,400
        outlet = json["outlet"]
        startDate = json["dateStart"]
        endDate = json["dateEnd"]
        # orderHistory =f"""SELECT Date,bill_no,(Total-serviceCharge-VAT) as 'Subtotal', Outlet_OrderID as id,serviceCharge, VAT,  Total, DiscountAmt, PaymentMode, GuestName, idtblorderhistory FROM `tblorderhistory` where Date BETWEEN %s and %s and Outlet_Name =%s  """
        orderHistory = """
SELECT
    tblorderhistory.Date, tblorderhistory.bill_no,
    (tblorderhistory.Total - tblorderhistory.serviceCharge - tblorderhistory.VAT) AS 'Subtotal',
    tblorderhistory.Outlet_OrderID AS id, tblorderhistory.serviceCharge, tblorderhistory.VAT, tblorderhistory.Total,
    tblorderhistory.DiscountAmt, tblorderhistory.PaymentMode, tblorderhistory.GuestName, tblorderhistory.idtblorderhistory,
    payment_history.paymentMode AS paymentModeHistory, payment_history.paymentAmount AS paymentAmountHistory, tblorderhistory.guestID
FROM
    tblorderhistory
LEFT JOIN
    payment_history  ON tblorderhistory.idtblorderhistory = payment_history.orderHistoryid AND tblorderhistory.PaymentMode = 'Split'
WHERE
    tblorderhistory.Date BETWEEN %s AND %s
    AND tblorderhistory.Outlet_Name = %s;
"""
        cursor.execute(orderHistory,(
            startDate,endDate,outlet,
        ),)
        result = cursor.fetchall()
        if result == []:
            data = {"error":"No data available."}
            return data,400
        row_headers=[x[0] for x in cursor.description] 
        json_data=[]
        for res in result:
            json_data.append(dict(zip(row_headers,res)))
        statsSql =f"""SELECT SUM(DiscountAmt) AS DiscountAmountSum, SUM(Total-serviceCharge-VAT) AS SubtotalAmountSum, SUM(Total) AS TotalSum, SUM(VAT) AS VatSum, SUM(serviceCharge) as ServiceChargeSum,SUM(NoOfGuests) as TotalGuestsServed,COUNT(idtblorderHistory) AS TotalOrders, COUNT(DISTINCT Date) AS DaysOperated FROM `tblorderhistory` where Date BETWEEN %s and %s and Outlet_Name =%s """
        cursor.execute(statsSql,(startDate,endDate,outlet,),)
        statsResult = cursor.fetchall()
        Stats_json_data=[]
        if statsResult == []:
            Stats_json_data[0]["orderDetails"]= {"error":"No data available."}
        else:
            row_headers=[x[0] for x in cursor.description] 
            for res in statsResult:
                Stats_json_data.append(dict(zip(row_headers,res)))
            Stats_json_data[0]["orderDetails"]= json_data
        items_food_Sql =f"""SELECT a.Description, a.itemName, sum(a.count)  as quantity, a.itemRate as itemrate, sum(a.Total) as total,a.ItemType FROM tblorder_detailshistory a, tblorderhistory b WHERE  a.ItemType='Food'  and  a.order_ID = b.idtblorderHistory and b.Outlet_Name =%s and b.Date BETWEEN %s and %s   group by a.ItemName,a.Description  order by a.Description """
        cursor.execute(items_food_Sql,(outlet,startDate,endDate,),)
        items_foodResult = cursor.fetchall()
        items_food_json_data=[]
        if items_foodResult == []:
            items_food_json_data["Data"] = {"error":"No data available."}
        row_headers=[x[0] for x in cursor.description] 
        for res in items_foodResult:
            items_food_json_data.append(dict(zip(row_headers,res)))
        items_beverage_Sql =f"""SELECT a.Description, a.itemName, sum(a.count)  as quantity, a.itemRate as itemrate, sum(a.Total) as total,a.ItemType FROM tblorder_detailshistory a, tblorderhistory b WHERE  a.ItemType='Beverage'  and  a.order_ID = b.idtblorderHistory and b.Outlet_Name =%s and b.Date BETWEEN %s and %s   group by a.ItemName,a.Description  order by a.Description """
        cursor.execute(items_beverage_Sql,(outlet,startDate,endDate,),)
        items_beverageResult = cursor.fetchall()
        if items_beverageResult == []:
            items_beverage_json_data= {"error":"No data available."}
        else:
            row_headers=[x[0] for x in cursor.description] 
            items_beverage_json_data=[]
            for res in items_beverageResult:
                items_beverage_json_data.append(dict(zip(row_headers,res)))
        items_sum_Sql =f"""SELECT (SELECT sum(a.total) as quantity FROM tblorder_detailshistory a, tblorderhistory b WHERE a.ItemType='Beverage'  and a.order_ID = b.idtblorderHistory and b.Outlet_Name =%s and b.Date BETWEEN %s and %s ) as beveragetotal, 
                        (SELECT sum( a.count) FROM tblorder_detailshistory a, tblorderhistory b WHERE a.ItemType='Beverage'  and a.order_ID = b.idtblorderHistory and b.Outlet_Name =%s and b.Date BETWEEN %s and %s )as beveragequantity , 
                        (SELECT sum(a.total) as quantity FROM tblorder_detailshistory a, tblorderhistory b WHERE a.ItemType='Food'  and a.order_ID = b.idtblorderHistory and b.Outlet_Name =%s and b.Date BETWEEN %s and %s ) as foodtotal, 
                        (SELECT sum( a.count) FROM tblorder_detailshistory a, tblorderhistory b WHERE a.ItemType='Food'  and a.order_ID = b.idtblorderHistory and b.Outlet_Name =%s and b.Date BETWEEN %s and %s )as foodquantity"""
        cursor.execute(items_sum_Sql,(outlet,startDate,endDate,outlet,startDate,endDate,outlet,startDate,endDate,outlet,startDate,endDate,),)
        items_sumResult = cursor.fetchall()
        if items_sumResult == []:
            items_sum_json_data = {"error":"No data available."}
        else:
            items_sum_json_data=[]
            row_headers=[x[0] for x in cursor.description] 
            for res in items_sumResult:
                items_sum_json_data.append(dict(zip(row_headers,res)))
        beverageGrouptotalSql= f"""SELECT sum(a.Total) as groupTotal, a.Description as groupName FROM tblorder_detailshistory a, tblorderhistory b WHERE  b.Outlet_Name =%s and b.Date BETWEEN %s and %s and a.ItemType='Beverage'  and  a.order_ID = b.idtblorderHistory   group by a.Description ORDER BY sum(a.Total)  DESC"""
        cursor.execute(beverageGrouptotalSql,(outlet,startDate,endDate,),)
        beverageGroupResult = cursor.fetchall()        
        if beverageGroupResult == []:
            beverageGroup_json_data = {"error":"No data available."}
        else:
            beverageGroup_json_data=[]
            row_headers=[x[0] for x in cursor.description] 
            for res in beverageGroupResult:
                beverageGroup_json_data.append(dict(zip(row_headers,res)))
        foodGrouptotalSql= f"""SELECT sum(a.Total) as groupTotal, a.Description as groupName FROM tblorder_detailshistory a, tblorderhistory b WHERE   b.Outlet_Name =%s and b.Date BETWEEN %s and %s and a.ItemType='Food'  and  a.order_ID = b.idtblorderHistory   group by a.Description ORDER BY sum(a.Total)  DESC"""
        cursor.execute(foodGrouptotalSql,(outlet,startDate,endDate,),)
        foodGroupResult = cursor.fetchall()        
        if foodGroupResult == []:
            foodGroup_json_data = {"error":"No data available."}
        else:
            foodGroup_json_data=[]
            row_headers=[x[0] for x in cursor.description] 
            for res in foodGroupResult:
                foodGroup_json_data.append(dict(zip(row_headers,res)))
        itemsumDetailsJson={"itemSum":items_sum_json_data,"food":items_food_json_data,"foodGroup":foodGroup_json_data,"beverage":items_beverage_json_data,"beverageGroup":beverageGroup_json_data}
 
        # split_payments_by_order_id = {}
 
        # for row in result:
        #     order_id = row[9]  # Assuming the order ID is in the 8th position
        #     if order_id not in split_payments_by_order_id:
        #         split_payments_by_order_id[order_id] = []
 
        #     split_payments_by_order_id[order_id].append({
        #         "PaymentMode": row[3],
        #         "PaymentAmount": float(row[10]),
        #     })

        # for order_detail in json_data:
        #     order_id = order_detail["id"]
        #     if order_id in split_payments_by_order_id:
        #         order_detail["SplitPayments"] = []
        #         for payment_info in split_payments_by_order_id[order_id]:
        #             order_detail["SplitPayments"].append({
        #                 "PaymentMode": payment_info["PaymentMode"],
        #                 "PaymentAmount": payment_info["PaymentAmount"],
        #             })
 
        # Initialize a dictionary to hold order details with split payments
        split_order_details = {}
 
        # Iterate through the order details and group them by order ID
        for order_detail in json_data:
            order_id = order_detail["idtblorderhistory"]
            if order_id not in split_order_details:
                # Create a new entry for this order ID
                split_order_details[order_id] = order_detail
                # Initialize an empty list to store split payments
                split_order_details[order_id]["SplitPayments"] = []
 
        # Iterate through the payment history and add split payments to the corresponding order
        # for row in result:
        #     order_id = row[10]  # Assuming the order ID is in the 8th position
        #     if order_id in split_order_details:
        #         # Append each split payment to the list
        #         split_order_details[order_id]["SplitPayments"].append({
        #             "PaymentMode": row[11],  # Use the correct index for PaymentMode from your query
        #             "PaymentAmount": float(row[12]),  # Use the correct index for PaymentAmount from your query
        #         })
 
        for row in result:
            order_id = row[10]  # Assuming the order ID is in the 8th position
            payment_mode = row[8] if row[8] is not None else "Unknown"
            if payment_mode == "Split" and order_id in split_order_details:
                # Check if paymentAmountHistory is not None before converting to float
                payment_amount = float(row[12]) if row[12] is not None else 0.0
                # Check if paymentModeHistory is not None
                payment_mode = row[11] if row[11] is not None else "Unknown"
 
                # Append each split payment to the list
                split_order_details[order_id]["SplitPayments"].append({
                    "PaymentMode": payment_mode,
                    "PaymentAmount": payment_amount,
                })
        # Convert the dictionary values to a list to get the final result
        final_order_details = list(split_order_details.values())
 
        for order_detail in final_order_details:
            del order_detail["paymentAmountHistory"]
            del order_detail["paymentModeHistory"]
 
        Stats_json_data[0]["itemDetails"]= itemsumDetailsJson
        Stats_json_data[0]["orderDetails"] = final_order_details
        mydb.close()
        return Stats_json_data[0]
    except Exception as error:
        data ={'error':str(error)}
        return data,400
