import streamlit as st
import mysql.connector
import pandas as pd

# ----------------- Page Config -----------------
st.set_page_config(page_title="Uber Eats Bangalore DSS", layout="wide")
st.title("Uber Eats Bangalore - Restaurant Intelligence & Decision Support System")

# ----------------- Database Connection -----------------
conn = mysql.connector.connect(
    port="3307",
    user="root",
    password="",
    database="uber_eats_bangalore"
)
cursor = conn.cursor()

# ----------------- Sidebar Navigation -----------------
page = st.sidebar.selectbox("Select Page", ["Dashboard", "Business Questions"])

# ----------------- Dashboard Page -----------------
if page == "Dashboard":
    st.header("Dynamic Restaurant Explorer")
    
    col1, col2 = st.columns(2)
    with col1:
        location = st.multiselect("Select Location(s)", options=pd.read_sql("SELECT DISTINCT location FROM restaurants", conn)['location'].tolist())
    with col2:
        price_seg = st.selectbox("Price Segment", ["All", "Low", "Mid", "Premium", "Ultra-Premium"])
    
    min_rating = st.slider("Minimum Rating", 0.0, 5.0, 3.5)
    
    # Build dynamic query
    query = "SELECT restaurant_name, location, rate, approx_cost_for_two, price_segment FROM restaurants WHERE 1=1"
    params = []
    
    if location:
        query += " AND location IN (" + ",".join(["%s"]*len(location)) + ")"
        params.extend(location)
    if price_seg != "All":
        query += " AND price_segment = %s"
        params.append(price_seg)
    query += " AND rate >= %s"
    params.append(min_rating)
    
    df = pd.read_sql(query, conn, params=params)
    st.dataframe(df, use_container_width=True, hide_index=True)

# ----------------- Business Questions Page -----------------
else:
    st.header("Key Business Questions (Tabular Insights)")
    
    questions = {
        "1. Which locations have the highest average ratings?": """
            SELECT location, ROUND(AVG(rate), 2) AS avg_rating, COUNT(*) AS num_restaurants
            FROM restaurants GROUP BY location HAVING COUNT(*) >= 5
            ORDER BY avg_rating DESC LIMIT 10;
        """,
        "2. Which locations are over-saturated?": """
            SELECT location, COUNT(*) AS restaurant_count, ROUND(AVG(rate), 2) AS avg_rating
            FROM restaurants GROUP BY location
            HAVING COUNT(*) > (SELECT AVG(cnt)*1.5 FROM (SELECT COUNT(*) cnt FROM restaurants GROUP BY location) t)
            ORDER BY restaurant_count DESC LIMIT 10;
        """,
        "3. Does online ordering improve ratings?": """
            SELECT CASE WHEN online_order=1 THEN 'With Online Order' ELSE 'Without' END AS feature,
                   ROUND(AVG(rate),2) AS avg_rating, COUNT(*) AS count
            FROM restaurants GROUP BY online_order;
        """,
        "4. Does table booking improve ratings?": """
            SELECT CASE WHEN book_table=1 THEN 'With Table Booking' ELSE 'Without' END AS feature,
                   ROUND(AVG(rate),2) AS avg_rating, COUNT(*) AS count
            FROM restaurants GROUP BY book_table;
        """,
        "5. Best price segment for customer satisfaction?": """
            SELECT price_segment, ROUND(AVG(rate),2) AS avg_rating, COUNT(*) AS count
            FROM restaurants GROUP BY price_segment ORDER BY avg_rating DESC;
        """,
        "6. Most common cuisines in Bangalore": """
            SELECT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(cuisines,',',n.n),',',-1)) AS cuisine,
                   COUNT(*) AS num_restaurants
            FROM restaurants JOIN (SELECT 1 n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) n
            GROUP BY cuisine ORDER BY num_restaurants DESC LIMIT 10;
        """,
        "7. Revenue by Location (Orders data)": """
            SELECT r.location, ROUND(SUM(o.order_value),2) AS total_revenue, COUNT(*) AS total_orders
            FROM orders o JOIN restaurants r ON o.restaurant_name = r.restaurant_name
            GROUP BY r.location ORDER BY total_revenue DESC LIMIT 10;
        """,
        "8. Top Restaurants by Revenue": """
            SELECT restaurant_name, ROUND(SUM(order_value),2) AS total_revenue, COUNT(*) AS num_orders
            FROM orders GROUP BY restaurant_name ORDER BY total_revenue DESC LIMIT 10;
        """,
        "9. Payment Method Analysis": """
            SELECT payment_method, ROUND(AVG(order_value),2) AS avg_order_value, COUNT(*) AS num_orders
            FROM orders GROUP BY payment_method;
        """,
        "10. High Performing Restaurants (Rating + Revenue)": """
            SELECT r.restaurant_name, r.location, ROUND(AVG(r.rate),2) AS avg_rating, 
                   ROUND(SUM(o.order_value),2) AS total_revenue
            FROM restaurants r JOIN orders o ON r.restaurant_name = o.restaurant_name
            GROUP BY r.restaurant_name, r.location HAVING avg_rating >= 4.0
            ORDER BY total_revenue DESC LIMIT 10;
        """
    }
    
    selected_q = st.selectbox("Choose a Business Question", list(questions.keys()))
    
    cursor.execute(questions[selected_q])
    result = cursor.fetchall()
    cols = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(result, columns=cols)
    st.dataframe(df, use_container_width=True, hide_index=True)

st.sidebar.success("Project Complete! All data in MySQL + Streamlit DSS Ready")
