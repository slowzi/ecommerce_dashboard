# import all library
from babel.numbers import format_currency
from streamlit_lottie import st_lottie
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns
import pandas as pd
import requests
import babel
import json

# SET PAGE AND THEME
# custom = {'axes.facecolor':'cornflowerblue', "axes.edgecolor": "red", 'figure.facecolor':'cornflowerblue', 'grid.linestyle': 'dashed'}
# rc=custom
sns.set(style='darkgrid')
st.set_page_config(page_title="E-Commerce Dashboard", page_icon=":chart_with_upwards_trend:", layout="wide")

# make to not always load dataset using cache
@st.cache_data
def get_main_data():
    main_data = pd.read_csv("main_data.csv")
    return main_data

main_data = get_main_data()

# sort kolom order_date dan mengubah order_date & delivery_date ke tipe datetime
datetime_columns = ["order_purchase_timestamp"]
main_data.sort_values(by="order_purchase_timestamp", inplace=True)
main_data.reset_index(inplace=True)
 
for column in datetime_columns:
    main_data[column] = pd.to_datetime(main_data[column])

# FUNCTION
# load lottie animation
def load_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# create df from order_purchase_timestamp, order_id & total_price
def create_daily_purchase(df):
    daily_purchase = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "total_price": "sum"
    })
    daily_purchase = daily_purchase.reset_index()
    daily_purchase.rename(columns={
        "order_id": "purchase_count",
        "total_price": "revenue"
    }, inplace=True)
    
    return daily_purchase

# create df for total monthly purchases
def create_monthly_purchase(df):
    monthly_purchase = df.resample(rule='M', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "total_price": "sum"
    })

    monthly_purchase.index = monthly_purchase.index.strftime('%Y-%m')
    monthly_purchase = monthly_purchase.reset_index()

    monthly_purchase.rename(columns = {
        "order_id": "purchase_amount",
        "total_price": "monthly_revenue"
    }, inplace=True)
    
    return monthly_purchase

# create perform product
def create_perform(df):
    product_perform = main_data.groupby(by=["review_score", "product_category_name_english"]).agg({
        "order_id": "nunique",
        "total_price": "sum"
    }).sort_values(by=["order_id", "review_score", "total_price"], ascending=False)

    return product_perform

def create_potential_city(df):
    most_purchases = df.groupby(by="customer_city").agg({
        "order_id": "nunique",
        "total_price": "sum"
    }).sort_values(by="total_price", ascending=False)

    # rename customer_id to customer count
    most_purchases.rename(columns = {
        "order_id": "purchase_amount"
    }, inplace=True)
    
    return most_purchases

def create_rfm(df):
    rfm = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max", 
        "order_id": "nunique", 
        "total_price": "sum" 
    })

    rfm.columns = ["customer_id", "max_date", "frequency", "monetary"] 

    rfm["max_date"] = pd.to_datetime(rfm["max_date"])
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])

    rfm["max_date"] = rfm["max_date"].dt.date 
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm["recency"] = rfm["max_date"].apply(lambda x: (recent_date - x).days)
    rfm.drop("max_date", axis=1, inplace=True)

    return rfm
# END FUNCTION

min_date = main_data["order_purchase_timestamp"].min()
max_date = main_data["order_purchase_timestamp"].max()
 
# SIDEBAR
with st.sidebar:
    hello = load_url("https://lottie.host/68c85353-1063-4a00-8bbf-1d50aa1f6523/sameECNrU5.json")
    st_lottie(hello, key="hello")
    st.markdown("---")
    st.header("Set date filter: ", divider="rainbow")
    
    start_date, end_date = st.date_input(
        label='Time Span',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# menampilkan df sesuai dengan filter tanggal di sidebar
all_data = main_data[(main_data["order_purchase_timestamp"] >= str(start_date)) & 
                 (main_data["order_purchase_timestamp"] <= str(end_date))]

# Create dataframe
daily_purchase = create_daily_purchase(all_data)
monthly_purchase = create_monthly_purchase(all_data)
perform_product = create_perform(all_data)
potential_city = create_potential_city(all_data)
rfm = create_rfm(all_data)

# MAIN PAGE
# make header
st.header(':white_flower: :rainbow[E-Commerce dataset Dashboard] :date:')
df = main_data[main_data.order_status.isin(['delivered'])]
with st.expander('_Dataset Preview_'):
    st.dataframe(df)
st.markdown('---')

# make daily order 
st.subheader('Daily Purchase')
 
col1, col2, col3 = st.columns(3)
 
with col1:
    total_revenue = format_currency(daily_purchase.revenue.sum() / 1000000, "USD", locale='es_CO') 
    st.metric("_Total Revenue in million_", value=total_revenue)
 
with col2:
    total_purchase = daily_purchase.purchase_count.sum()
    st.metric("_Total purchase_", value=total_purchase)

with col3:
    avg_rating = round(main_data['review_score'].mean(), 1)
    st.metric("_Average Rating_", value=avg_rating)

st.markdown("---")

# make total purchase
st.subheader("Total Purchases from 2016 to 2018 per Month :chart_with_upwards_trend:")
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    monthly_purchase["order_purchase_timestamp"],
    monthly_purchase["purchase_amount"],
    marker='o', 
    linewidth=2,
    color="limegreen"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15, labelrotation = 90)
# fig.update_layout(showlegend=False, paper_bgcolor = 'rgba(0, 0, 0, 0)', plot_bgcolor = 'rgba(0, 0, 0, 0)' )
st.pyplot(fig)
st.markdown('---')

# make best and worst performance product
st.subheader("Best & Worst Performing Product :dart:") 
fig, ax = plt.subplots(nrows=1, ncols=2,figsize=(26, 6))

# color list 
colors = ["limegreen", "lightgrey", "lightgrey", "lightgrey", "lightgrey"]
color2 = ["lightcoral", "lightgrey", "lightgrey", "lightgrey", "lightgrey"]

# make barplot for ax 0 / for best product
sns.barplot(x="order_id", y="product_category_name_english", data=perform_product.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Best Performing Product", loc="center", fontsize=15)
ax[0].tick_params(axis='y', labelsize=12)

# make barplot for ax 1 / for worst product
sns.barplot(x="order_id", y="product_category_name_english", data=perform_product.tail(5), palette=color2, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=15)
ax[1].tick_params(axis='y', labelsize=12)
 
st.pyplot(fig)
st.markdown("---")

# make most potential city
st.subheader("Most Potential City by Amount Purchases :signal_strength:")
fig, ax = plt.subplots(figsize=(16, 8))
sns.barplot(
    x = "purchase_amount",
    y = "customer_city",
    data = potential_city.head(5),
    palette = colors
)

ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)
st.markdown('---')

# make rfm analysis
st.subheader('Customer Based on RFM Parameters (_customer_id_) :chart:')
 
col1, col2, col3 = st.columns(3)
 
with col1:
    avg_recency = round(rfm.recency.mean(), 1)
    st.metric("_Average Recency (days)_", value=avg_recency)
 
with col2:
    avg_frequency = round(rfm.frequency.mean(), 2)
    st.metric("_Average Frequency_", value=avg_frequency)
 
with col3:
    avg_monetary = format_currency(rfm.monetary.mean(), "USD", locale='es_CO') 
    st.metric("_Average Monetary_", value=avg_monetary)

fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(15, 20))

colors = ["limegreen", "lightgrey", "lightgrey", "lightgrey", "lightgrey"]

# make barplot recency
sns.barplot(y="customer_id", x="recency", data=rfm.head(5).sort_values(by="recency", ascending=False), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].tick_params(axis ='x', labelsize=15)

# make barplot frequency
sns.barplot(y="customer_id", x="frequency", data=rfm.head(5).sort_values(by="frequency", ascending=False), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=18)
ax[1].tick_params(axis='x', labelsize=15)

# make barplot monetary
sns.barplot(y="customer_id", x="monetary", data=rfm.head(5).sort_values(by="monetary", ascending=False), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=18)
ax[2].tick_params(axis='x', labelsize=15)

st.pyplot(fig)

st.markdown('---')
st.caption('Create by Dimas with :sparkling_heart:')

# STYLING PAGE
hide_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            #the-header {text-align: center}
            </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)
