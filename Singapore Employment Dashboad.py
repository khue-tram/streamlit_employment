import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

#----------------------
#  Set page configuration
#----------------------

st.set_page_config(page_title="Age Group Analysis", page_icon=":bar_chart:", layout="wide")

st.title("📊Singapore Employment Analysis by Service Sectors")

#----------------------
# Load data
#----------------------
datafolder = 'Cleansed Data'
agegroup_file = 'final_gender_data.csv'
return_file = 'Return on FDI.csv'
investment_file = 'investfinal.csv'
ocupation_file = 'Occupation.csv'

if os.path.exists(datafolder):

    #age group data
    df_agegroup = pd.read_csv(f"{datafolder}/{agegroup_file}")

    #occupation data
    df_occupation = pd.read_csv(f"{datafolder}/{ocupation_file}", encoding="ISO-8859-1")
    df_occupation = df_occupation[df_occupation["Occupation"] != "All Occupation Groups"]
    df_occupation.columns = [col.strip() for col in df_occupation.columns]
    numeric_cols = ["Employed_Residents"]
    df_occupation[numeric_cols] = df_occupation[numeric_cols].apply(pd.to_numeric, errors="coerce")
    
    #investment and return data
    return_df = pd.read_csv(f"{datafolder}/{return_file}")
    return_df = return_df.rename(columns={return_df.columns[0]: "Industry"})
    ret_long = return_df.melt(id_vars="Industry", var_name="Year", value_name="Return")
    ret_long["Year"] = ret_long["Year"].astype(int)

    investment_df = pd.read_csv(f"{datafolder}/{investment_file}")
    investment_df = investment_df.rename(columns={investment_df.columns[0]: "Industry"})
    inv_long = investment_df.melt(id_vars="Industry", var_name="Year", value_name="Investment")
    inv_long["Year"] = inv_long["Year"].astype(int)


#----------------------
# Create sidebar filters
#----------------------

st.sidebar.header("Choose your filter:")

#Choosing the year
yearmin = int(2007)
yearmax = int(2024)

startyear, endyear = st.sidebar.slider("Choose the Period of Years:", yearmin, yearmax, (yearmin, yearmax))

print(startyear, endyear)
selected_years = [y for y in range(startyear, endyear + 1)]

# choosing the sectors
unique_sectors = pd.concat([df_agegroup['Service Sectors'],inv_long['Industry'],ret_long['Industry'],df_occupation['Industry']],ignore_index=True).unique()
unique_sectors.sort()

sectors = st.sidebar.multiselect("Choose the Service Sector:", unique_sectors)
if not sectors:
    sectors = unique_sectors.tolist()
print(sectors)

# Apply filters to all data set
df_agegroup = df_agegroup[(df_agegroup['Year'] >= startyear) & (df_agegroup['Year'] <= endyear)]
inv_filtered = inv_long[(inv_long["Year"] >= startyear) & (inv_long["Year"] <= endyear)]
ret_filtered = ret_long[(ret_long["Year"] >= startyear) & (ret_long["Year"] <= endyear)]
df_occupation = df_occupation[(df_occupation['Year'] >= startyear) & (df_occupation['Year'] <= endyear)]

if sectors:
    df_agegroup = df_agegroup[df_agegroup['Service Sectors'].isin(sectors)]
    inv_filtered = inv_filtered[inv_filtered['Industry'].isin(sectors)]
    ret_filtered = ret_filtered[ret_filtered['Industry'].isin(sectors)]
    df_occupation = df_occupation[df_occupation['Industry'].isin(sectors)]

#----------------------
# Setting up the charts
#----------------------

color_map = {
    "Accommodation & Food Services": "#1f77b4",
    "Professional And Administrative & Support": "#ff7f0e",
    "Wholesale & Retail Trade": "#2ca02c",
    "Financial & Insurance Services": "#d62728",
    "Information & Communications": "#17becf",
    "Transportation & Storage": "#9467bd",
    "Real Estate Services": "#8c564b"
}

#----------------------
# Age Group Analysis
#----------------------

st.subheader("💼Age Group Analysis for Selected Sectors")

agegroup = st.multiselect("Select Age Group:", df_agegroup['Age Group'].unique())
if agegroup:
    df_agegroup = df_agegroup[df_agegroup['Age Group'].isin(agegroup)]

col1, col2 = st.columns(2)

#Draw the population pyramid
with col1:
    bar_agegroup = (
        df_agegroup.groupby(['Age Group', 'Gender','Year'])['No. of employed']
        .sum()
        .reset_index()  
    ) 
    bar_agegroup = (
        bar_agegroup.groupby(['Age Group', 'Gender'])['No. of employed']
        .mean()
        .reset_index()
        .rename(columns={'No. of employed': 'Average No. of employed'})  
    ) 
    bar_agegroup.loc[bar_agegroup['Gender'] == 'Male', 'Average No. of employed'] *= -1
    bar_agegroup['abs_value'] = bar_agegroup['Average No. of employed'].abs()

    fig_pyramid = px.bar(bar_agegroup,
                         x='Average No. of employed',
                         y='Age Group',
                         color='Gender',
                         barmode='relative',
                         orientation='h',
                         text='abs_value',
                         title=f'Average Employed Residents Pyramid Across {startyear} to {endyear}')
    
    fig_pyramid.update_traces(
        hovertemplate='Age Group: %{y}<br>Gender: %{customdata[0]}<br>Average No. of Employed: %{customdata[1]:,.2f}',
        customdata=np.stack((bar_agegroup['Gender'], bar_agegroup['abs_value']), axis=-1),  
        texttemplate='%{text:.2f}', textposition='inside', insidetextanchor='middle')
    
    fig_pyramid.update_layout(
        hoverlabel=dict(font_size=12, font_family="Arial"),
        xaxis_title='Average No. of Employed Residents (in thousands)', 
        yaxis_title='Age Group',
        title=dict(
            x = 0.5,
            xanchor='center',
            font=dict(size=18)
        ),
        legend=dict(orientation="h", 
                    yanchor="bottom", 
                    y=1.02, 
                    xanchor="center", 
                    x=0.5, 
                    traceorder="reversed", 
                    title_text=" "),
        height=600,
        bargap=0.1,)
    
    fig_pyramid.update_xaxes(tickvals=[-40000, -20000, 0, 20000, 40000],
                             ticktext=[40000, 20000, 0, 20000, 40000])
    st.plotly_chart(fig_pyramid, use_container_width=True)

# Plotting the line chart
with col2:
    line_agegroup = (
        df_agegroup.groupby(['Year', 'Age Group'])['No. of employed']
        .sum()
        .reset_index()
    )

    fig_line = px.line(line_agegroup, 
                       x='Year',
                       y='No. of employed',
                       color='Age Group',
                       title=f'Trend of Employed Residents by Age Group Over {startyear} to {endyear}',)
    fig_line.update_traces(
        hovertemplate=(
            "Age Group: %{fullData.name}<br>"
            "Year: %{x}<br>"
            "No. of employed: %{y:,.2f}<extra></extra>"
        ),
        mode='markers+lines')
    fig_line.update_layout(
        xaxis_title='Years',
        yaxis_title='Number of Employed Residents (in thousands)',
        hovermode='x unified',
        legend_title='Age Group',
        title=dict(
            x = 0.5,
            xanchor='center',
            font=dict(size=18)
        ),
        hoverlabel=dict(font_size=12, font_family="Arial"),
        height=600        
    )
    fig_line.update_traces(mode='markers+lines')
    fig_line.update_yaxes(tickformat=",.0f")
    st.plotly_chart(fig_line, use_container_width=True)

# -------------------------
# Occupation Analysis
# -------------------------

#Plotting the Employment Trend Over Tinme by Occupation
st.subheader("📈 Employment Trend Over Time")

filtered_df = (
    df_occupation.groupby(["Year", "Occupation"], as_index=False)["Employed_Residents"]
    .sum()
)

if not filtered_df.empty:
    fig_trend = px.line(
        filtered_df,
        x="Year",
        y="Employed_Residents",
        color="Occupation",
        markers=True,
        title=f"Employment Trends for Selected Industries ({startyear}–{endyear})"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.warning("⚠️ No data available for the selected filters.")

# Plotting the Treemap for Occupation Analysis

df_avg = (
    df_occupation.groupby(["Industry", "Occupation"], as_index=False)["Employed_Residents"]
    .mean()
    .rename(columns={"Employed_Residents": "Avg_Employed_Residents"})
)

# Compute share (%)
total = df_avg["Avg_Employed_Residents"].sum()
df_avg["Share"] = df_avg["Avg_Employed_Residents"] / total * 100

# Format data for display
df_avg["Avg_Formatted"] = df_avg["Avg_Employed_Residents"].apply(lambda x: f"{x:,.2f}")
df_avg["Share_Formatted"] = df_avg["Share"].apply(lambda x: f"{x:.2f}%")

fig3 = px.treemap(
    df_avg,
    path=["Industry", "Occupation"],
    values="Avg_Employed_Residents",
    hover_data={
        "Avg_Employed_Residents": ":,.2f",
        "Share": ":.2f",
    },
    color="Occupation",
    title= f"Hierarchical View of Residents Employed by Occupation for Selected Year Range: {startyear} - {endyear}"
)

fig3.update_traces(
    text=df_avg.apply(
        lambda row: f"Avg: {row['Avg_Employed_Residents']:,.2f}\nShare: {row['Share']:.2f}%",
        axis=1
    ),
    textposition='middle center',
    hovertemplate=(
        '<b>%{label}</b><br>'
        'Avg Employed Residents: %{customdata[0]:,.2f}<br>'
        'Share: %{customdata[1]:.2f}%<extra></extra>'
    ),
    texttemplate=(
        '<b>%{label}</b><br>'
        'Avg: %{customdata[0]:,.2f}<br>'
        'Share: %{customdata[1]:.2f}%'
    ),
)

fig3.update_layout(
    width=800,
    height=650,
    font=dict(size=12)
)

st.plotly_chart(fig3, use_container_width=True)

# -----------------------
# Investment and Return Analysis
# -----------------------
st.subheader("💰Investment and Return Analysis for Selected Sectors")

col1, col2 = st.columns(2)

# Left Column: Investment
with col1:
    if len(selected_years) == 1:
        fig_inv = px.bar(
            inv_filtered,
            x="Industry",
            y="Investment",
            color="Industry",
            text="Investment",
            height=400,
            title=f"Investment in {selected_years[0]}"
        )
        fig_inv.update_xaxes(dtick=1, tickformat="d")
        fig_inv.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    else:
        fig_inv = px.line(
            inv_filtered,
            x="Year",
            y="Investment",
            color="Industry",
            markers=True,
            title="Investment Over Years",
            height=400
        )
        fig_inv.update_xaxes(dtick=1, tickformat="d")
    fig_inv.update_layout(
        title=dict(
            x = 0.5,
            xanchor='center',
            font=dict(size=18)
        )
    )
    st.plotly_chart(fig_inv, use_container_width=True)

# Right Column: Returns
with col2:
    if len(selected_years) == 1:
        fig_ret = px.bar(
            ret_filtered,
            x="Industry",
            y="Return",
            color="Industry",
            text="Return",
            height=400,
            title=f"Return in {selected_years[0]}"
        )
        fig_ret.update_xaxes(dtick=1, tickformat="d")
        fig_ret.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    else:
        fig_ret = px.line(
            ret_filtered,
            x="Year",
            y="Return",
            color="Industry",
            markers=True,
            title="Returns Over Years",
            height=400
        )
        fig_ret.update_xaxes(dtick=1, tickformat="d")
        fig_ret.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="0% baseline")
    fig_ret.update_layout(
        title=dict(
            x = 0.5,
            xanchor='center',
            font=dict(size=18)
        )
    )
    st.plotly_chart(fig_ret, use_container_width=True)

# ===================================
# Bottom: Combined Chart (Investment + Return)
# ===================================
combined_df = pd.merge(inv_filtered, ret_filtered, on=["Industry", "Year"])

fig_combined = go.Figure()

# Add Investment (Bar, Left Y-axis)
for industry in sectors:
    industry_data = combined_df[combined_df["Industry"] == industry]
    fig_combined.add_trace(
        go.Bar(
            x=industry_data["Year"],
            y=industry_data["Investment"],
            name=f"{industry} Investment",
            yaxis="y1"
        )
    )

# Add Return (Line, Right Y-axis)
for industry in sectors:
    industry_data = combined_df[combined_df["Industry"] == industry]
    fig_combined.add_trace(
        go.Scatter(
            x=industry_data["Year"],
            y=industry_data["Return"],
            mode="lines+markers",
            name=f"{industry} Return",
            yaxis="y2"
        )
    )

# Layout for dual axis
fig_combined.update_layout(
    height=600,
    xaxis=dict(title="Year", dtick=1),
    yaxis=dict(title="Investment Amount", side="left"),
    yaxis2=dict(title="Return (%)", overlaying="y", side="right"),
    barmode="group",
    title="Investment vs Return"
)
fig_combined.update_layout(
        title=dict(
            x = 0.5,
            xanchor='center',
            font=dict(size=18)
        ),
        legend=dict(orientation="h",
                    yanchor="bottom", 
                    y=-0.8, 
                    xanchor="center", 
                    x=0.5, 
                    traceorder="normal", 
                    title_text=" "),
    )
st.plotly_chart(fig_combined, use_container_width=True)









