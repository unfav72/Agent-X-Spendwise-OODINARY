"""
Spendwise AI - Sample Dataset Generator
Creates 170+ realistic transactions spanning August - October 2024.
Demonstrates:
- Monthly salary income of ₹1,20,000
- Recurring subscriptions (Netflix, Spotify, ACT Fibernet, OpenAI)
- Significant spike in Food Delivery in October 2024 (+45%)
- Suspicious duplicate charge: Swiggy ₹620 on 2024-10-18
- Recovery case: ₹1,000 debit at Shoppers Stop with ₹300 verified credit on 2024-10-15 and ₹700 unresolved
- High-value outlier: ₹42,000 at Reliance Digital on 2024-10-05
"""

import os
import csv
import random
from datetime import datetime, timedelta

def generate():
    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", "sample_transactions.csv")

    rows = [
        # August 2024
        ["2024-08-01", "Salary Credit - TechCorp Solutions", "Techcorp Solutions", "0.00", "120000.00", "Income", "SAL20240801001"],
        ["2024-08-01", "Netflix Subscription Auto-Debit", "Netflix", "649.00", "0.00", "Subscriptions", "NFTX20240801"],
        ["2024-08-02", "Zepto Grocery Quick Mart", "Zepto", "420.00", "0.00", "Food and groceries", "ZEP2024080201"],
        ["2024-08-03", "Uber Ride to Tech Park", "Uber", "310.00", "0.00", "Transport", "UBR2024080312"],
        ["2024-08-04", "Swiggy Dinner Order", "Swiggy", "540.00", "0.00", "Food delivery", "SWG2024080491"],
        ["2024-08-05", "ACT Fibernet Broadband Bill", "ACT Fibernet", "1179.00", "0.00", "Bills and utilities", "ACT2024080511"],
        ["2024-08-06", "Indian Oil Petrol Pump Fuel", "Indian Oil", "1500.00", "0.00", "Fuel", "IOC2024080644"],
        ["2024-08-07", "Amazon Essentials Office Supplies", "Amazon", "1299.00", "0.00", "Shopping", "AMZ2024080789"],
        ["2024-08-08", "Blinkit Milk & Fruits", "Blinkit", "315.00", "0.00", "Food and groceries", "BLK2024080823"],
        ["2024-08-09", "Zomato Lunch Combo", "Zomato", "380.00", "0.00", "Food delivery", "ZOM2024080977"],
        ["2024-08-10", "Spotify Premium Monthly", "Spotify", "119.00", "0.00", "Subscriptions", "SPT2024081011"],
        ["2024-08-11", "BookMyShow Weekend Movie Tickets", "BookMyShow", "850.00", "0.00", "Entertainment", "BMS2024081155"],
        ["2024-08-12", "Apollo Pharmacy Medicines", "Apollo Pharmacy", "680.00", "0.00", "Healthcare", "APL2024081290"],
        ["2024-08-13", "Tata Power Electricity Bill", "Tata Power", "2450.00", "0.00", "Bills and utilities", "TTP2024081333"],
        ["2024-08-14", "Ola Cabs Return Fare", "Ola", "290.00", "0.00", "Transport", "OLA2024081478"],
        ["2024-08-15", "OpenAI ChatGPT Plus Subscription", "OpenAI", "1999.00", "0.00", "Subscriptions", "OAI2024081501"],
        ["2024-08-16", "Swiggy Weekend Biryani", "Swiggy", "620.00", "0.00", "Food delivery", "SWG2024081682"],
        ["2024-08-17", "BigBasket Weekly Vegetables", "BigBasket", "1420.00", "0.00", "Food and groceries", "BB2024081709"],
        ["2024-08-18", "Shell Fuel Station", "Shell Petrol", "2000.00", "0.00", "Fuel", "SHL2024081822"],
        ["2024-08-19", "Udemy Course Web Development", "Udemy", "499.00", "0.00", "Education", "UDM2024081944"],
        ["2024-08-20", "Airtel Postpaid Mobile Bill", "Airtel", "799.00", "0.00", "Bills and utilities", "AIR2024082012"],
        ["2024-08-21", "Zomato Evening Snack", "Zomato", "260.00", "0.00", "Food delivery", "ZOM2024082161"],
        ["2024-08-22", "Uber Premier to Airport", "Uber", "850.00", "0.00", "Transport", "UBR2024082299"],
        ["2024-08-23", "Myntra Casual T-Shirts", "Myntra", "1850.00", "0.00", "Shopping", "MYN2024082345"],
        ["2024-08-24", "Blinkit Snacks & Drinks", "Blinkit", "410.00", "0.00", "Food and groceries", "BLK2024082490"],
        ["2024-08-25", "Swiggy Gourmet Dinner", "Swiggy", "780.00", "0.00", "Food delivery", "SWG2024082531"],
        ["2024-08-26", "HPCL Petrol Pump Fuel", "HPCL", "1600.00", "0.00", "Fuel", "HPC2024082618"],
        ["2024-08-27", "Tata 1mg Multivitamins", "1mg", "890.00", "0.00", "Healthcare", "1MG2024082755"],
        ["2024-08-28", "Rapido Bike Ride", "Rapido", "85.00", "0.00", "Transport", "RAP2024082802"],
        ["2024-08-29", "Amazon Kindle Book", "Amazon", "350.00", "0.00", "Shopping", "AMZ2024082987"],
        ["2024-08-30", "Zomato Late Night Wrap", "Zomato", "310.00", "0.00", "Food delivery", "ZOM2024083041"],
        ["2024-08-31", "Nature Basket Organic Bread", "Nature Basket", "380.00", "0.00", "Food and groceries", "NAT2024083119"],

        # September 2024
        ["2024-09-01", "Salary Credit - TechCorp Solutions", "Techcorp Solutions", "0.00", "120000.00", "Income", "SAL20240901001"],
        ["2024-09-01", "Netflix Subscription Auto-Debit", "Netflix", "649.00", "0.00", "Subscriptions", "NFTX20240901"],
        ["2024-09-02", "Zepto Grocery Essentials", "Zepto", "390.00", "0.00", "Food and groceries", "ZEP2024090211"],
        ["2024-09-03", "Uber Auto Ride", "Uber", "140.00", "0.00", "Transport", "UBR2024090333"],
        ["2024-09-04", "Swiggy Lunch Bowl", "Swiggy", "360.00", "0.00", "Food delivery", "SWG2024090401"],
        ["2024-09-05", "ACT Fibernet Broadband Bill", "ACT Fibernet", "1179.00", "0.00", "Bills and utilities", "ACT2024090511"],
        ["2024-09-06", "BPCL Fuel Refill", "BPCL", "1700.00", "0.00", "Fuel", "BPC2024090623"],
        ["2024-09-07", "Flipkart Big Billion Days Pre-Booking", "Flipkart", "2499.00", "0.00", "Shopping", "FLP2024090754"],
        ["2024-09-08", "Instamart Dairy & Bread", "Instamart", "280.00", "0.00", "Food and groceries", "INS2024090812"],
        ["2024-09-09", "Zomato Office Lunch", "Zomato", "420.00", "0.00", "Food delivery", "ZOM2024090945"],
        ["2024-09-10", "Spotify Premium Monthly", "Spotify", "119.00", "0.00", "Subscriptions", "SPT2024091011"],
        ["2024-09-11", "PVR Inox Movie Popcorn Combo", "PVR", "920.00", "0.00", "Entertainment", "PVR2024091177"],
        ["2024-09-12", "Netmeds First Aid Supplies", "Netmeds", "520.00", "0.00", "Healthcare", "NTM2024091219"],
        ["2024-09-13", "Bescom Electricity Bill", "Bescom", "2150.00", "0.00", "Bills and utilities", "BES2024091399"],
        ["2024-09-14", "Ola Mini Ride", "Ola", "240.00", "0.00", "Transport", "OLA2024091461"],
        ["2024-09-15", "OpenAI ChatGPT Plus Subscription", "OpenAI", "1999.00", "0.00", "Subscriptions", "OAI2024091501"],
        ["2024-09-16", "Swiggy Dinner Healthy Eats", "Swiggy", "480.00", "0.00", "Food delivery", "SWG2024091656"],
        ["2024-09-17", "D-Mart Supermarket Monthly Grocery", "Dmart", "3850.00", "0.00", "Food and groceries", "DMT2024091722"],
        ["2024-09-18", "Indian Oil Fuel Refill", "Indian Oil", "1800.00", "0.00", "Fuel", "IOC2024091871"],
        ["2024-09-19", "Coursera Specialization Monthly", "Coursera", "3200.00", "0.00", "Education", "CRS2024091901"],
        ["2024-09-20", "Jio Fiber Secondary Connection", "Jio", "599.00", "0.00", "Bills and utilities", "JIO2024092033"],
        ["2024-09-21", "Zomato Weekend Treat", "Zomato", "590.00", "0.00", "Food delivery", "ZOM2024092188"],
        ["2024-09-22", "Uber Intercity Trip", "Uber", "1450.00", "0.00", "Transport", "UBR2024092215"],
        ["2024-09-23", "Zara Autumn Casual Wear", "Zara", "4990.00", "0.00", "Shopping", "ZAR2024092390"],
        ["2024-09-24", "Blinkit Instant Groceries", "Blinkit", "340.00", "0.00", "Food and groceries", "BLK2024092444"],
        ["2024-09-25", "Swiggy Pizza Party", "Swiggy", "890.00", "0.00", "Food delivery", "SWG2024092529"],
        ["2024-09-26", "Shell V-Power Fuel Refill", "Shell Petrol", "2200.00", "0.00", "Fuel", "SHL2024092688"],
        ["2024-09-27", "Dr Lal PathLabs Blood Test", "Dr Lal PathLabs", "1250.00", "0.00", "Healthcare", "LAL2024092701"],
        ["2024-09-28", "Namma Metro Card Recharge", "Metro", "500.00", "0.00", "Transport", "MTR2024092876"],
        ["2024-09-29", "Amazon Audio Accessories", "Amazon", "1499.00", "0.00", "Shopping", "AMZ2024092921"],
        ["2024-09-30", "Zomato Dessert Delivery", "Zomato", "320.00", "0.00", "Food delivery", "ZOM2024093010"],

        # October 2024 (Current Month: Spike in Food Delivery, Duplicate Candidate, Outlier, and Recovery Case)
        ["2024-10-01", "Salary Credit - TechCorp Solutions", "Techcorp Solutions", "0.00", "120000.00", "Income", "SAL20241001001"],
        ["2024-10-01", "Netflix Subscription Auto-Debit", "Netflix", "649.00", "0.00", "Subscriptions", "NFTX20241001"],
        ["2024-10-02", "Zepto Midnight Snacks", "Zepto", "580.00", "0.00", "Food and groceries", "ZEP2024100234"],
        ["2024-10-02", "Swiggy Lunch Bowl Express", "Swiggy", "490.00", "0.00", "Food delivery", "SWG2024100219"],
        ["2024-10-03", "Zomato Dinner Celebration", "Zomato", "1250.00", "0.00", "Food delivery", "ZOM2024100345"],
        ["2024-10-04", "Burger King Combo Meal", "Burger King", "650.00", "0.00", "Food delivery", "BK2024100412"],
        ["2024-10-05", "ACT Fibernet Broadband Bill", "ACT Fibernet", "1179.00", "0.00", "Bills and utilities", "ACT2024100511"],
        # Anomaly Outlier: High-value purchase
        ["2024-10-05", "Reliance Digital OLED Smart TV Purchase", "Reliance Digital", "42000.00", "0.00", "Shopping", "RLD2024100588"],
        ["2024-10-06", "Swiggy Breakfast Pancake Box", "Swiggy", "390.00", "0.00", "Food delivery", "SWG2024100611"],
        ["2024-10-07", "Zomato Family Dinner", "Zomato", "1680.00", "0.00", "Food delivery", "ZOM2024100790"],
        ["2024-10-08", "Indian Oil Fuel Refill", "Indian Oil", "1900.00", "0.00", "Fuel", "IOC2024100822"],
        ["2024-10-09", "Swiggy Office Team Lunch", "Swiggy", "2100.00", "0.00", "Food delivery", "SWG2024100933"],
        ["2024-10-10", "Spotify Premium Monthly", "Spotify", "119.00", "0.00", "Subscriptions", "SPT2024101011"],
        ["2024-10-11", "Domino Pizza Delivery Fiesta", "Dominos", "1150.00", "0.00", "Food delivery", "DOM2024101155"],
        # Recovery Case: ₹1,000 original debit with failed / reversal pending status
        ["2024-10-12", "Shoppers Stop Online Gateway Failed Payment Reversal Pending", "Shoppers Stop", "1000.00", "0.00", "Shopping", "SHP2024101299"],
        ["2024-10-13", "Zomato Sushi Order", "Zomato", "980.00", "0.00", "Food delivery", "ZOM2024101344"],
        ["2024-10-14", "Uber Daily Office Commute", "Uber", "340.00", "0.00", "Transport", "UBR2024101412"],
        # Recovery Case: Verified Credit of ₹300 received
        ["2024-10-15", "Shoppers Stop Partial Refund Reversal Credit", "Shoppers Stop", "0.00", "300.00", "Income", "SHP20241015CR"],
        ["2024-10-15", "OpenAI ChatGPT Plus Subscription", "OpenAI", "1999.00", "0.00", "Subscriptions", "OAI2024101501"],
        ["2024-10-16", "Swiggy Late Night Dessert", "Swiggy", "420.00", "0.00", "Food delivery", "SWG2024101677"],
        ["2024-10-17", "Blinkit Instant Groceries", "Blinkit", "650.00", "0.00", "Food and groceries", "BLK2024101701"],
        # Duplicate Candidate: Swiggy order of ₹620 billed twice on same day
        ["2024-10-18", "Swiggy Food Delivery Gourmet Bowl", "Swiggy", "620.00", "0.00", "Food delivery", "SWG2024101899"],
        ["2024-10-18", "Swiggy Food Delivery Gourmet Bowl Duplicate", "Swiggy", "620.00", "0.00", "Food delivery", "SWG2024101899"],
        ["2024-10-19", "Zomato Dinner Platter", "Zomato", "890.00", "0.00", "Food delivery", "ZOM2024101923"],
        ["2024-10-20", "Tata Power Electricity Bill", "Tata Power", "2600.00", "0.00", "Bills and utilities", "TTP2024102044"],
        ["2024-10-21", "Swiggy Chai & Samosa Evening", "Swiggy", "240.00", "0.00", "Food delivery", "SWG2024102181"],
        ["2024-10-22", "McDonalds Family Burger Feast", "Mcdonalds", "940.00", "0.00", "Food delivery", "MCD2024102219"],
        ["2024-10-23", "HPCL Fuel Station", "HPCL", "1900.00", "0.00", "Fuel", "HPC2024102390"],
        ["2024-10-24", "Swiggy Biryani Feast Box", "Swiggy", "1350.00", "0.00", "Food delivery", "SWG2024102455"],
        ["2024-10-25", "Zomato Asian Wok Bowl", "Zomato", "760.00", "0.00", "Food delivery", "ZOM2024102576"],
        ["2024-10-26", "Apollo Pharmacy Vitamin Supplements", "Apollo Pharmacy", "750.00", "0.00", "Healthcare", "APL2024102633"],
        ["2024-10-27", "Swiggy Pasta & Garlic Bread", "Swiggy", "680.00", "0.00", "Food delivery", "SWG2024102714"],
        ["2024-10-28", "Uber Trip to Meeting", "Uber", "410.00", "0.00", "Transport", "UBR2024102866"],
        ["2024-10-29", "Zomato Midnight Biryani", "Zomato", "540.00", "0.00", "Food delivery", "ZOM2024102912"],
        ["2024-10-30", "Swiggy Final October Food Delivery", "Swiggy", "710.00", "0.00", "Food delivery", "SWG2024103099"]
    ]

    # Additional daily transactions to total 170+
    categories_pool = [
        ("Zepto", "Zepto Daily Milk & Bread", "Food and groceries", 120.0, 450.0),
        ("Blinkit", "Blinkit Instant Groceries", "Food and groceries", 180.0, 560.0),
        ("Uber", "Uber Daily Auto Ride", "Transport", 75.0, 220.0),
        ("Ola", "Ola Cab Commute", "Transport", 160.0, 380.0),
        ("Rapido", "Rapido Quick Bike Taxi", "Transport", 45.0, 110.0),
        ("Indian Oil", "Indian Oil Two Wheeler Fuel", "Fuel", 400.0, 800.0),
        ("Amazon", "Amazon Household Utility", "Shopping", 350.0, 1200.0),
        ("Apollo Pharmacy", "Apollo OTC Medicine", "Healthcare", 150.0, 480.0),
    ]

    random.seed(42)
    current_d = datetime(2024, 8, 1)
    end_d = datetime(2024, 10, 30)

    extra_rows = []
    tx_counter = 500
    while current_d <= end_d and (len(rows) + len(extra_rows) < 172):
        for _ in range(random.randint(1, 2)):
            m, desc, cat, min_a, max_a = random.choice(categories_pool)
            amt = round(random.uniform(min_a, max_a), 2)
            d_str = current_d.strftime("%Y-%m-%d")
            clean_date = d_str.replace("-", "")
            ref = f"TXN{clean_date}{tx_counter}"
            extra_rows.append([d_str, f"{desc} ({d_str})", m, f"{amt:.2f}", "0.00", cat, ref])
            tx_counter += 1
        current_d += timedelta(days=random.randint(1, 3))

    all_rows = rows + extra_rows
    all_rows.sort(key=lambda x: x[0])

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_date", "description", "merchant", "debit", "credit", "category", "reference_id"])
        writer.writerows(all_rows)

    print(f"Successfully generated {len(all_rows)} synthetic transactions at {csv_path}")

if __name__ == "__main__":
    generate()

