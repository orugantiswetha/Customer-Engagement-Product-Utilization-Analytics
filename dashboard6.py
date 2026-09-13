import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="European Bank Customer Retention Analytics",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(
    """
    <style>
    .main {
        padding-top: 1rem;
    }

    [data-testid="stMetric"] {
        background-color: #f7f9fc;
        border: 1px solid #dfe4ea;
        padding: 15px;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.title(" Customer Engagement & Product Utilization Analytics")

st.subheader("Retention Strategy Dashboard")

st.write(
    """
    This dashboard analyzes customer engagement, product utilization,
    financial value, relationship strength, and churn behavior.
    """
)

st.markdown("---")

@st.cache_data
def load_data():

    data = pd.read_csv("European_Bank.csv")

    return data


try:

    df = load_data()

except FileNotFoundError:

    st.error(
        """
         European_Bank.csv was not found.

        Make sure that European_Bank.csv and dashboard2.py
        are inside the same folder.
        """
    )

    st.stop()

df = df.copy()

# Remove completely empty columns
df = df.dropna(axis=1, how="all")

# Remove duplicate records
df = df.drop_duplicates()

required_columns = [
    "CustomerId",
    "Surname",
    "CreditScore",
    "Geography",
    "Gender",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "EstimatedSalary",
    "Exited"
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:

    st.error(
        f" Missing columns: {missing_columns}"
    )

    st.stop()

numeric_columns = [
    "CustomerId",
    "CreditScore",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "EstimatedSalary",
    "Exited"
]


for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

for column in numeric_columns:

    if df[column].isna().sum() > 0:

        df[column] = df[column].fillna(
            df[column].median()
        )

def engagement_profile(row):

    active = row["IsActiveMember"]
    products = row["NumOfProducts"]
    balance = row["Balance"]

    if active == 1 and products >= 2:

        return "Active Engaged"

    elif active == 1 and products == 1:

        return "Active Low-Product"

    elif active == 0 and balance >= 100000:

        return "Inactive High-Balance"

    else:

        return "Inactive Disengaged"


df["EngagementProfile"] = df.apply(
    engagement_profile,
    axis=1
)

max_products = df["NumOfProducts"].max()

if max_products > 0:

    df["ProductDepthIndex"] = (
        df["NumOfProducts"] / max_products
    ) * 100

else:

    df["ProductDepthIndex"] = 0

df["RelationshipStrengthIndex"] = (

    (df["IsActiveMember"] * 40)

    +

    (np.minimum(
        df["NumOfProducts"],
        4
    ) * 15)

    +

    (df["HasCrCard"] * 10)

)


df["RelationshipStrengthIndex"] = (
    df["RelationshipStrengthIndex"]
    .clip(0, 100)
)

def relationship_category(score):

    if score < 25:

        return "Weak"

    elif score < 50:

        return "Moderate"

    elif score < 75:

        return "Strong"

    else:

        return "Very Strong"


df["RelationshipStrength"] = (
    df["RelationshipStrengthIndex"]
    .apply(relationship_category)
)
df["HighValueCustomer"] = (

    (df["Balance"] >= 100000)

    |

    (df["EstimatedSalary"] >= 100000)

)

df["AtRiskPremiumCustomer"] = (
    (df["Balance"] >= 100000)
    &
    (df["IsActiveMember"] == 0)
)


st.sidebar.title(" Dashboard Filters")
geography_options = sorted(
    df["Geography"].dropna().unique()
)


selected_geographies = st.sidebar.multiselect(
    " Geography",
    geography_options,
    default=geography_options
)
gender_options = sorted(
    df["Gender"].dropna().unique()
)


selected_genders = st.sidebar.multiselect(
    " Gender",
    gender_options,
    default=gender_options
)
engagement_options = sorted(
    df["EngagementProfile"].unique()
)


selected_engagement = st.sidebar.multiselect(
    " Engagement Profile",
    engagement_options,
    default=engagement_options
)
min_product = int(
    df["NumOfProducts"].min()
)

max_product = int(
    df["NumOfProducts"].max()
)


selected_products = st.sidebar.slider(
    "🛍️ Number of Products",
    min_product,
    max_product,
    (min_product, max_product)
)
max_balance = float(
    df["Balance"].max()
)


balance_threshold = st.sidebar.slider(
    " Minimum Balance",
    min_value=0.0,
    max_value=max_balance,
    value=0.0,
    step=5000.0
)
max_salary = float(
    df["EstimatedSalary"].max()
)


salary_threshold = st.sidebar.slider(
    " Minimum Salary",
    min_value=0.0,
    max_value=max_salary,
    value=0.0,
    step=5000.0
)


# Customer status

customer_status = st.sidebar.selectbox(
    " Customer Status",
    [
        "All Customers",
        "Retained Customers",
        "Churned Customers"
    ]
)

filtered_df = df[
    (df["Geography"].isin(selected_geographies))

    &

    (df["Gender"].isin(selected_genders))

    &

    (df["EngagementProfile"].isin(selected_engagement))

    &

    (df["NumOfProducts"].between(
        selected_products[0],
        selected_products[1]
    ))

    &

    (df["Balance"] >= balance_threshold)

    &

    (df["EstimatedSalary"] >= salary_threshold)
]

if customer_status == "Retained Customers":

    filtered_df = filtered_df[
        filtered_df["Exited"] == 0
    ]


elif customer_status == "Churned Customers":

    filtered_df = filtered_df[
        filtered_df["Exited"] == 1
    ]

total_customers = len(filtered_df)


if total_customers > 0:

    churn_rate = (
        filtered_df["Exited"].mean() * 100
    )

    retention_rate = (
        100 - churn_rate
    )

    active_rate = (
        filtered_df["IsActiveMember"].mean() * 100
    )

    average_products = (
        filtered_df["NumOfProducts"].mean()
    )

    average_balance = (
        filtered_df["Balance"].mean()
    )

    average_relationship = (
        filtered_df["RelationshipStrengthIndex"].mean()
    )

else:

    churn_rate = 0

    retention_rate = 0

    active_rate = 0

    average_products = 0

    average_balance = 0

    average_relationship = 0

st.header(" Key Performance Indicators")


kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)


with kpi1:

    st.metric(
        " Customers",
        f"{total_customers:,}"
    )


with kpi2:

    st.metric(
        " Churn Rate",
        f"{churn_rate:.2f}%"
    )


with kpi3:

    st.metric(
        " Retention Rate",
        f"{retention_rate:.2f}%"
    )


with kpi4:

    st.metric(
        " Avg Products",
        f"{average_products:.2f}"
    )


with kpi5:

    st.metric(
        " Relationship Score",
        f"{average_relationship:.1f}/100"
    )


st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        " Engagement vs Churn",
        " Product Utilization",
        " High-Value Customers",
        " Retention Strength",
        " Customer Data"
    ]
)

with tab1:

    st.header(
        " Engagement vs Churn Analysis"
    )

    engagement_summary = (
        filtered_df
        .groupby("EngagementProfile")
        .agg(
            Customers=("CustomerId", "count"),
            ChurnRate=("Exited", "mean"),
            AverageBalance=("Balance", "mean")
        )
        .reset_index()
    )


    engagement_summary["ChurnRate"] = (
        engagement_summary["ChurnRate"] * 100
    )


    engagement_summary["RetentionRate"] = (
        100 - engagement_summary["ChurnRate"]
    )

    if len(engagement_summary) > 0:

        fig1 = px.bar(
            engagement_summary,
            x="EngagementProfile",
            y="ChurnRate",
            text_auto=".2f",
            title="Churn Rate by Engagement Profile",
            labels={
                "EngagementProfile":
                    "Engagement Profile",
                "ChurnRate":
                    "Churn Rate (%)"
            }
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    col1, col2 = st.columns(2)


    with col1:
        activity_summary = (
            filtered_df
            .groupby("IsActiveMember")
            .agg(
                Customers=("CustomerId", "count"),
                ChurnRate=("Exited", "mean")
            )
            .reset_index()
        )


        activity_summary["Activity"] = (
            activity_summary["IsActiveMember"]
            .map({
                0: "Inactive",
                1: "Active"
            })
        )


        activity_summary["ChurnRate"] = (
            activity_summary["ChurnRate"] * 100
        )


        if len(activity_summary) > 0:

            fig2 = px.bar(
                activity_summary,
                x="Activity",
                y="ChurnRate",
                text_auto=".2f",
                title="Active vs Inactive Customer Churn",
                labels={
                    "Activity": "Customer Activity",
                    "ChurnRate": "Churn Rate (%)"
                }
            )


            st.plotly_chart(
                fig2,
                use_container_width=True
            )

    with col2:

        geography_summary = (
            filtered_df
            .groupby("Geography")
            .agg(
                Customers=("CustomerId", "count"),
                ChurnRate=("Exited", "mean")
            )
            .reset_index()
        )


        geography_summary["ChurnRate"] = (
            geography_summary["ChurnRate"] * 100
        )


        if len(geography_summary) > 0:

            fig3 = px.bar(
                geography_summary,
                x="Geography",
                y="ChurnRate",
                text_auto=".2f",
                title="Churn Rate by Geography",
                labels={
                    "Geography": "Geography",
                    "ChurnRate": "Churn Rate (%)"
                }
            )


            st.plotly_chart(
                fig3,
                use_container_width=True
            )

    age_summary = (
        filtered_df
        .groupby("Age")
        .agg(
            Customers=("CustomerId", "count"),
            ChurnRate=("Exited", "mean")
        )
        .reset_index()
    )


    age_summary["ChurnRate"] = (
        age_summary["ChurnRate"] * 100
    )


    if len(age_summary) > 0:

        fig4 = px.line(
            age_summary,
            x="Age",
            y="ChurnRate",
            markers=True,
            title="Churn Rate by Customer Age",
            labels={
                "Age": "Customer Age",
                "ChurnRate": "Churn Rate (%)"
            }
        )


        st.plotly_chart(
            fig4,
            use_container_width=True
        )

    st.subheader(
        "Engagement Profile Summary"
    )


    st.dataframe(
        engagement_summary,
        use_container_width=True
    )

with tab2:

    st.header(
        " Product Utilization Analysis"
    )

    product_summary = (
        filtered_df
        .groupby("NumOfProducts")
        .agg(
            Customers=("CustomerId", "count"),
            ChurnRate=("Exited", "mean"),
            AverageBalance=("Balance", "mean")
        )
        .reset_index()
    )


    product_summary["ChurnRate"] = (
        product_summary["ChurnRate"] * 100
    )


    product_summary["RetentionRate"] = (
        100 - product_summary["ChurnRate"]
    )


    col1, col2 = st.columns(2)

    with col1:

        if len(product_summary) > 0:

            fig5 = px.bar(
                product_summary,
                x="NumOfProducts",
                y="ChurnRate",
                text_auto=".2f",
                title="Churn Rate by Number of Products",
                labels={
                    "NumOfProducts":
                        "Number of Products",
                    "ChurnRate":
                        "Churn Rate (%)"
                }
            )


            st.plotly_chart(
                fig5,
                use_container_width=True
            )
    with col2:

        if len(product_summary) > 0:

            fig6 = px.bar(
                product_summary,
                x="NumOfProducts",
                y="Customers",
                text_auto=True,
                title="Customer Distribution by Product Count",
                labels={
                    "NumOfProducts":
                        "Number of Products",
                    "Customers":
                        "Customers"
                }
            )


            st.plotly_chart(
                fig6,
                use_container_width=True
            )

    st.subheader(
        " Product Depth vs Retention"
    )


    st.dataframe(
        product_summary,
        use_container_width=True
    )

    st.subheader(
        " Credit Card Stickiness"
    )


    card_summary = (
        filtered_df
        .groupby("HasCrCard")
        .agg(
            Customers=("CustomerId", "count"),
            ChurnRate=("Exited", "mean")
        )
        .reset_index()
    )


    card_summary["CardOwnership"] = (
        card_summary["HasCrCard"]
        .map({
            0: "No Credit Card",
            1: "Has Credit Card"
        })
    )


    card_summary["ChurnRate"] = (
        card_summary["ChurnRate"] * 100
    )


    if len(card_summary) > 0:

        fig7 = px.bar(
            card_summary,
            x="CardOwnership",
            y="ChurnRate",
            text_auto=".2f",
            title="Credit Card Ownership vs Churn",
            labels={
                "CardOwnership":
                    "Credit Card Ownership",
                "ChurnRate":
                    "Churn Rate (%)"
            }
        )


        st.plotly_chart(
            fig7,
            use_container_width=True
        )
with tab3:

    st.header(
        " High-Value Disengaged Customer Detector"
    )


    # High balance + inactive

    high_value = filtered_df[
        (filtered_df["Balance"] >= 100000)
        &
        (filtered_df["IsActiveMember"] == 0)
    ].copy()


    high_value_count = len(high_value)


    if high_value_count > 0:

        high_value_churned = int(
            high_value["Exited"].sum()
        )

        high_value_churn_rate = (
            high_value["Exited"].mean() * 100
        )

    else:

        high_value_churned = 0

        high_value_churn_rate = 0

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            " High-Balance Disengaged",
            f"{high_value_count:,}"
        )


    with col2:

        st.metric(
            " Already Churned",
            f"{high_value_churned:,}"
        )


    with col3:

        st.metric(
            " Churn Rate",
            f"{high_value_churn_rate:.2f}%"
        )

    if high_value_count > 0:

        high_value["RiskStatus"] = np.where(
            high_value["Exited"] == 1,
            " Churned",
            " At Risk"
        )


        display_columns = [
            "CustomerId",
            "Surname",
            "Geography",
            "Gender",
            "Age",
            "Balance",
            "EstimatedSalary",
            "NumOfProducts",
            "HasCrCard",
            "IsActiveMember",
            "Exited",
            "RiskStatus"
        ]


        st.subheader(
            " Customers Requiring Attention"
        )


        st.dataframe(
            high_value[
                display_columns
            ].sort_values(
                "Balance",
                ascending=False
            ),
            use_container_width=True
        )

        fig8 = px.scatter(
            high_value,
            x="Balance",
            y="EstimatedSalary",
            size="NumOfProducts",
            color="Exited",
            hover_data=[
                "CustomerId",
                "Surname",
                "Geography",
                "Age"
            ],
            title="High-Value Disengaged Customers",
            labels={
                "Balance":
                    "Account Balance",
                "EstimatedSalary":
                    "Estimated Salary",
                "Exited":
                    "Churn Status"
            }
        )


        st.plotly_chart(
            fig8,
            use_container_width=True
        )


    else:

        st.success(
            "No high-value disengaged customers "
            "match the selected filters."
        )

with tab4:

    st.header(
        " Retention Strength Assessment"
    )


    strength_summary = (
        filtered_df
        .groupby("RelationshipStrength")
        .agg(
            Customers=("CustomerId", "count"),
            ChurnRate=("Exited", "mean"),
            AverageProducts=("NumOfProducts", "mean"),
            AverageBalance=("Balance", "mean")
        )
        .reset_index()
    )


    strength_summary["ChurnRate"] = (
        strength_summary["ChurnRate"] * 100
    )


    strength_summary["RetentionRate"] = (
        100 - strength_summary["ChurnRate"]
    )

    strength_order = [
        "Weak",
        "Moderate",
        "Strong",
        "Very Strong"
    ]


    strength_summary["RelationshipStrength"] = pd.Categorical(
        strength_summary["RelationshipStrength"],
        categories=strength_order,
        ordered=True
    )


    strength_summary = (
        strength_summary
        .sort_values("RelationshipStrength")
    )
    if len(strength_summary) > 0:

        fig9 = px.bar(
            strength_summary,
            x="RelationshipStrength",
            y="ChurnRate",
            text_auto=".2f",
            title="Churn Rate by Relationship Strength",
            labels={
                "RelationshipStrength":
                    "Relationship Strength",
                "ChurnRate":
                    "Churn Rate (%)"
            }
        )


        st.plotly_chart(
            fig9,
            use_container_width=True
        )

    if len(filtered_df) > 0:

        st.subheader(
            "Relationship Strength Score Distribution"
        )


        fig10 = px.histogram(
            filtered_df,
            x="RelationshipStrengthIndex",
            nbins=20,
            title="Distribution of Relationship Strength Scores",
            labels={
                "RelationshipStrengthIndex":
                    "Relationship Strength Score"
            }
        )


        st.plotly_chart(
            fig10,
            use_container_width=True
        )

    st.subheader(
        "Relationship Strength Summary"
    )


    st.dataframe(
        strength_summary,
        use_container_width=True
    )

    st.subheader(
        " Retention Recommendations"
    )


    if churn_rate >= 20:

        st.error(
            """
             **High churn detected**

            The bank should prioritize targeted retention campaigns,
            personalized offers, and proactive customer engagement.
            """
        )

    elif churn_rate >= 10:

        st.warning(
            """
             **Moderate churn detected**

            Focus on improving engagement and increasing product
            adoption among vulnerable customer segments.
            """
        )

    else:

        st.success(
            """
             **Low churn detected**

            Continue strengthening customer relationships and
            monitoring disengaged customers.
            """
        )


    if active_rate < 60:

        st.warning(
            """
             **Low customer engagement**

            Consider digital engagement campaigns, personalized
            communication, loyalty programs, and targeted offers.
            """
        )


    if average_products < 2:

        st.warning(
            """
             **Low product depth**

            Cross-sell relevant banking products to increase
            relationship depth and customer stickiness.
            """
        )


    if high_value_count > 0:

        st.warning(
            f"""
             **{high_value_count:,} high-balance disengaged customers detected**

            These customers should be prioritized for proactive
            retention communication.
            """
        )

with tab5:

    st.header(
        " Customer Data Explorer"
    )


    st.write(
        f"Showing **{len(filtered_df):,}** customers "
        "based on the selected filters."
    )

    search_customer = st.text_input(
        " Search by Customer ID or Surname"
    )


    display_data = filtered_df.copy()


    if search_customer:

        search_value = search_customer.lower()


        display_data = display_data[
            display_data["CustomerId"]
            .astype(str)
            .str.contains(
                search_value,
                case=False,
                na=False
            )

            |

            display_data["Surname"]
            .astype(str)
            .str.lower()
            .str.contains(
                search_value,
                case=False,
                na=False
            )
        ]

    st.dataframe(
        display_data,
        use_container_width=True,
        height=500
    )

    csv_data = display_data.to_csv(
        index=False
    )


    st.download_button(
        label=" Download Filtered Customer Data",
        data=csv_data,
        file_name="filtered_customer_data.csv",
        mime="text/csv"
    )

st.markdown("---")


with st.expander(
    " Data Quality & Dataset Information"
):

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Rows",
            f"{len(df):,}"
        )


    with col2:

        st.metric(
            "Columns",
            f"{len(df.columns):,}"
        )


    with col3:

        st.metric(
            "Duplicates",
            f"{df.duplicated().sum():,}"
        )


    with col4:

        st.metric(
            "Missing Values",
            f"{df.isnull().sum().sum():,}"
        )


    st.subheader(
        "Dataset Columns"
    )


    column_information = pd.DataFrame({

        "Column": df.columns,

        "Data Type": [
            str(df[column].dtype)
            for column in df.columns
        ],

        "Missing Values": [
            int(df[column].isnull().sum())
            for column in df.columns
        ],

        "Unique Values": [
            int(df[column].nunique())
            for column in df.columns
        ]

    })


    st.dataframe(
        column_information,
        use_container_width=True
    )

st.markdown("---")

st.caption(
    "🏦 European Bank | Customer Engagement & Product "
    "Utilization Analytics | Retention Strategy"
)
