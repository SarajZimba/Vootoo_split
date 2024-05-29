from flask import  Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file10= Blueprint('app_file10',__name__)
from root.auth.check import token_auth
import re

def valid_date(datestring):
        try:
                regex = re.compile("^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$")
                match = re.match(regex, datestring)
                if match is not None:
                    return True
        except ValueError:
            return False
        return False
@app_file10.route("/summaryreport", methods=["POST"])
@cross_origin()
def statsummary():
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
        outletName = json["outlet"]
        start_Date = json["dateStart"]
        end_Date = json["dateEnd"]
        if not valid_date(start_Date) or not valid_date(end_Date):
            data={"error":"Invalid date supplied."}
            return data,400


        statsSql =f"""SELECT (SELECT sum(b.total) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s) AS TOTALSALES,(SELECT sum(b.total) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and b.Type='Dine-In' ) AS DineInSALES,(SELECT sum(b.total) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and b.Type='Order') AS TabSALES,
(SELECT SUM(b.Total-b.serviceCharge-b.VAT) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s) AS netTOTALSALES,
(SELECT SUM(b.Total-b.serviceCharge-b.VAT) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and b.Type='Dine-In') AS netDineInSALES,
(SELECT SUM(b.Total-b.serviceCharge-b.VAT) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and b.Type='Order') AS netTabSALES,
(SELECT SUM(b.VAT) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s) AS TotalVat,(SELECT SUM(b.VAT) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and b.Type='Dine-In') AS DineInVAT,
(SELECT SUM(b.VAT) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and b.Type='Order') AS TabVAT,(SELECT SUM(b.serviceCharge) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s) AS TotalServiceCharge,(SELECT SUM(b.serviceCharge) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and b.Type='Dine-In') AS DineInServiceCharge,(SELECT SUM(b.serviceCharge) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and b.Type='Order') AS TabServiceCharge,(SELECT SUM(b.NoOfGuests) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s ) AS TotalGuests,(SELECT SUM(b.DiscountAmt) FROM  tblorderhistory b WHERE not b.bill_no='' and  b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s ) AS DiscountAmountSum,
(SELECT SUM(a.total) FROM tblorder_detailshistory a, tblorderhistory b WHERE not b.bill_no='' and a.order_ID = b.idtblorderHistory and b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and a.itemType='Food' ) AS FoodSale,(SELECT SUM(a.total) FROM tblorder_detailshistory a, tblorderhistory b WHERE not b.bill_no='' and a.order_ID = b.idtblorderHistory and b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and a.itemType='Beverage' ) AS BeverageSale,(SELECT SUM(a.total) FROM tblorder_detailshistory a, tblorderhistory b WHERE not b.bill_no='' and a.order_ID = b.idtblorderHistory and b.Date BETWEEN '{start_Date}' and '{end_Date}' and b.Outlet_Name = %s and a.itemType='Other' ) AS OtherSale"""
        cursor.execute(statsSql,(outletName,outletName,outletName,outletName,outletName,outletName,outletName,outletName,outletName,outletName,outletName,outletName,outletName,outletName,outletName,outletName,outletName,),)
        statsResult = cursor.fetchall()
        Stats_json_data=[]
        if statsResult == []:
            Stats_json_data["Data"] = {"error":"No data available."}
        else:    
            row_headers=[x[0] for x in cursor.description] 
            for res in statsResult:
                Stats_json_data.append(dict(zip(row_headers,res)))
        paymentStats_Sql =f"""SELECT  CONVERT(sum(Total),CHAR) as Total, PaymentMode FROM tblorderhistory where Date BETWEEN %s and %s and Outlet_Name =%s group by PaymentMode """
        cursor.execute(paymentStats_Sql,(start_Date,end_Date,outletName,),)
        paymentStatsResult = cursor.fetchall()
        # print(paymentStatsResult)
        paymentStats_json_data={}
        if paymentStatsResult == []:
            paymentStats_json_data["Data"] = {"error":"No data available."}
        else:
            row_headers=[x[0] for x in cursor.description] 
            for res in paymentStatsResult:
                paymentkey= dict(zip(row_headers,res))["PaymentMode"]
                paymentkey=paymentkey.replace(" ", "")
                # if paymentkey.lower() != "split":
                paymentStats_json_data[paymentkey]=dict(zip(row_headers,res))["Total"]
            if "Cash" not in paymentStats_json_data:
                paymentStats_json_data["Cash"]="0"
        
            if "Complimentary" not in paymentStats_json_data and "NonChargeable" not in paymentStats_json_data:
                paymentStats_json_data["Complimentary"]="0"
            if "CreditCard" not in paymentStats_json_data:
                paymentStats_json_data["CreditCard"]="0"    
            if "MobilePayment" not in paymentStats_json_data:
                paymentStats_json_data["MobilePayment"]="0"    
            if "NonChargeable" not in paymentStats_json_data:
                paymentStats_json_data["NonChargeable"]="0"
            if "Split" not in paymentStats_json_data:
                paymentStats_json_data["Split"]="0"    
            if "Credit" not in paymentStats_json_data:
                paymentStats_json_data["Credit"]="0"  
            if "NonChargeable" in paymentStats_json_data and "Complimentary" in paymentStats_json_data:
                paymentStats_json_data["Complimentary"]=str(float(paymentStats_json_data["NonChargeable"]) +   float(paymentStats_json_data["Complimentary"]) or 0 )        
            if "NonChargeable" in paymentStats_json_data and "Complimentary" not in paymentStats_json_data:
                paymentStats_json_data["Complimentary"]= paymentStats_json_data["NonChargeable"]
            
        # Stats_json_data[0]["paymentStats"]=paymentStats_json_data
        
        # split_sql = """
        #     SELECT paymentMode, paymentAmount, orderHistoryid, bill_No
        #     FROM payment_history
        #     WHERE orderHistoryid IN (
        #         SELECT idtblorderhistory
        #         FROM tblorderhistory
        #         WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s
        #     );
        # """
        # cursor.execute(split_sql, (start_Date, end_Date, outletName,))
        # split_result = cursor.fetchall()
        # # print(split_result)
        # # Convert the split_result into a list of dictionaries
        # split_list = [{'paymentMode': row[0], 'paymentAmount': float(row[1]), 'orderHistoryid': row[2], 'bill_No': row[3]} for row in split_result]
        split_sql = """
            SELECT paymentMode, SUM(paymentAmount), orderHistoryid, bill_No
            FROM payment_history
            WHERE orderHistoryid IN (
                SELECT idtblorderhistory
                FROM tblorderhistory
                WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s
            )GROUP BY paymentMode;
        """
        cursor.execute(split_sql, (start_Date, end_Date, outletName,))
        split_result = cursor.fetchall()
        # print(split_result)
        # Convert the split_result into a list of dictionaries
        payment_totals = {"Cash": 0.0, "Credit Card": 0.0, "Mobile Payment": 0.0}

        for row in split_result:
            payment_mode = row[0]
            total_payment_amount = float(row[1])
            payment_totals[payment_mode] = total_payment_amount
        split_list = [
            {
                "paymentMode": "Cash",
                "paymentAmount": payment_totals.get("Cash", 0.0)
            },
            {
                "paymentMode": "Credit Card",   
                "paymentAmount": payment_totals.get("Credit Card", 0.0)
            },
            {
                "paymentMode": "Mobile Payment",
                "paymentAmount": payment_totals.get("Mobile Payment", 0.0)
            }
        ]

        # Stats_json_data = {
        #     "paymentStats": paymentStats_json_data,
        #     "splitDetails": split_list  # Include the split list
        # }
        Stats_json_data[0]["paymentStats"]=paymentStats_json_data
        Stats_json_data[0]["splitDetails"] =split_list
        mydb.close()
        # return Stats_json_data[0]
        return Stats_json_data[0]
    except Exception as error:
        data ={'error':str(error)}
        return data,400
