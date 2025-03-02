import streamlit as st
import plotly.express as px
import pandas as pd
import warnings

warnings.filterwarnings('ignore')
st.set_page_config(page_title="SuperStore!", page_icon=":bar_chart:", layout="wide")
st.title(":bar_chart: Sample SuperStore EDA")

# Upload file
fl = st.file_uploader(":file_folder: Upload a file", type=["csv", "txt", "xlsx", "xls"])

df = None  # Initialize df as None to handle case where file loading fails

# Check if a file is uploaded
if fl is not None:
    filename = fl.name
    st.write(f"Loaded file: {filename}")
    
    try:
        if filename.endswith('.csv'):
            # Read CSV file
            df = pd.read_csv(fl, encoding="ISO-8859-1", on_bad_lines="skip", engine='python')
        elif filename.endswith('.xls'):
            # Read XLS file using xlrd engine
            df = pd.read_excel(fl, engine='xlrd')
        elif filename.endswith('.xlsx'):
            # Read XLSX file using openpyxl engine
            df = pd.read_excel(fl, engine='openpyxl')
        
    except Exception as e:
        st.error(f"Error loading file: {e}")

# Proceed only if df is loaded successfully
if df is not None:
    col1, col2 = st.columns((2))

    df["Order Date"] = pd.to_datetime(df["Order Date"])

    # Getting the min and max date 
    startDate = pd.to_datetime(df["Order Date"]).min()
    endDate = pd.to_datetime(df["Order Date"]).max()

    with col1:
        date1 = pd.to_datetime(st.date_input("Start Date", startDate))

    with col2:
        date2 = pd.to_datetime(st.date_input("End Date", endDate))

    df = df[(df["Order Date"] >= date1) & (df["Order Date"] <= date2)].copy()

    # Show the filtered data (optional)
    #st.write(df.head())

    st.sidebar.header("Choose your filter: ")

    # Sidebar filters: Region, State, City, etc.
    region = st.sidebar.multiselect("Pick your Region", df["Region"].unique())
    if not region:
        df2 = df.copy()
    else:
        df2 = df[df["Region"].isin(region)]

    state = st.sidebar.multiselect("Pick the State", df2["State"].unique())
    if not state:
        df3 = df2.copy()
    else:
        df3 = df2[df2["State"].isin(state)]

    city = st.sidebar.multiselect("Pick the City", df3["City"].unique())
    if not city:
        filtered_df = df3
    else:
        filtered_df = df3[df3["City"].isin(city)]

    # Category-wise sales
    category_df = filtered_df.groupby(by=["Category"], as_index=False)["Sales"].sum()

    with col1:
        st.subheader("Category wise Sales")
        fig = px.bar(category_df, x="Category", y="Sales", text=['${:,.2f}'.format(x) for x in category_df["Sales"]],
                     template="seaborn")
        st.plotly_chart(fig, use_container_width=True, height=200)

    with col2:
        st.subheader("Region wise Sales")
        fig = px.pie(filtered_df, values="Sales", names="Region", hole=0.5)
        fig.update_traces(text=filtered_df["Region"], textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    cl1, cl2 = st.columns((2))
    with cl1:
        with st.expander("Category_ViewData"):
            st.write(category_df.style.background_gradient(cmap="Blues"))
            csv = category_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Data", data=csv, file_name="Category.csv", mime="text/csv",
                               help='Click here to download the data as a CSV file')

    with cl2:
        with st.expander("Region_ViewData"):
            region = filtered_df.groupby(by="Region", as_index=False)["Sales"].sum()
            st.write(region.style.background_gradient(cmap="Oranges"))
            csv = region.to_csv(index=False).encode('utf-8')
            st.download_button("Download Data", data=csv, file_name="Region.csv", mime="text/csv",
                               help='Click here to download the data as a CSV file')

    # Time Series Analysis
    filtered_df["month_year"] = filtered_df["Order Date"].dt.to_period("M")
    st.subheader('Time Series Analysis')

    linechart = pd.DataFrame(filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y : %b"))["Sales"].sum()).reset_index()
    fig2 = px.line(linechart, x="month_year", y="Sales", labels={"Sales": "Amount"}, height=500, width=1000,
                   template="gridon")
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("View Data of TimeSeries:"):
        st.write(linechart.T.style.background_gradient(cmap="Blues"))
        csv = linechart.to_csv(index=False).encode("utf-8")
        st.download_button('Download Data', data=csv, file_name="TimeSeries.csv", mime='text/csv')

    # Hierarchical view of Sales using TreeMap
    st.subheader("Hierarchical view of Sales using TreeMap")
    fig3 = px.treemap(filtered_df, path=["Region", "Category", "Sub-Category"], values="Sales", hover_data=["Sales"],
                      color="Sub-Category")
    fig3.update_layout(width=800, height=650)
    st.plotly_chart(fig3, use_container_width=True)

    # Segment and Category Sales
    chart1, chart2 = st.columns((2))
    with chart1:
        st.subheader('Segment wise Sales')
        fig = px.pie(filtered_df, values="Sales", names="Segment", template="plotly_dark")
        fig.update_traces(text=filtered_df["Segment"], textposition="inside")
        st.plotly_chart(fig, use_container_width=True)

    with chart2:
        st.subheader('Category wise Sales')
        fig = px.pie(filtered_df, values="Sales", names="Category", template="gridon")
        fig.update_traces(text=filtered_df["Category"], textposition="inside")
        st.plotly_chart(fig, use_container_width=True)

    # Month wise Sub-Category Sales Summary
    import plotly.figure_factory as ff
    st.subheader(":point_right: Month wise Sub-Category Sales Summary")
    with st.expander("Summary_Table"):
        df_sample = df[0:5][["Region", "State", "City", "Category", "Sales", "Profit", "Quantity"]]
        fig = ff.create_table(df_sample, colorscale="Cividis")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("Month wise sub-Category Table")
        filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
        sub_category_Year = pd.pivot_table(data=filtered_df, values="Sales", index=["Sub-Category"], columns="month")
        st.write(sub_category_Year.style.background_gradient(cmap="Blues"))

    # Scatter plot between Sales and Profits
    data1 = px.scatter(filtered_df, x="Sales", y="Profit", size="Quantity")
    data1['layout'].update(title="Relationship between Sales and Profits using Scatter Plot.",
                           titlefont=dict(size=20), xaxis=dict(title="Sales", titlefont=dict(size=19)),
                           yaxis=dict(title="Profit", titlefont=dict(size=19)))
    st.plotly_chart(data1, use_container_width=True)

    with st.expander("View Data"):
        st.write(filtered_df.iloc[:500, 1:20:2].style.background_gradient(cmap="Oranges"))

    # Download original DataSet
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button('Download Data', data=csv, file_name="Data.csv", mime="text/csv")
