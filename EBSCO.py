# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 21:16:06 2021

@author: eschares
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import altair as alt
import streamlit_analytics

st.set_page_config(page_title='EBSCO', layout='centered', initial_sidebar_state="expanded")

streamlit_analytics.start_tracking()

st.image('EBSCO_logo.png')
st.sidebar.write("*Summer 2021*")

with st.beta_expander("How to use:"):
    st.write("By default, a fake dataset is preloaded since this has to be deployed publicly.")
    st.write("To analyze the actual data, login to Box, download the file at https://iastate.box.com/s/7y5hea3rzkfvihvtquh3rnv5m5oofg4n, then upload it using the button in left sidebar")



#Initialize with a hardcoded dataset
file = filename = "EBSCO 2022 renewal - No_T&F_or_SAGE_orNA0usage - test.csv"
#file = filename = "EBSCO 2022 renewal - No_T&F_or_SAGE_orNA0usage.csv"

uploaded_file = st.sidebar.file_uploader('To analyze the actual data, download file at https://iastate.box.com/s/7y5hea3rzkfvihvtquh3rnv5m5oofg4n and upload here to analyze:', type='csv')
if uploaded_file is not None:
    file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
    #st.write(file_details)
    
    file = uploaded_file
    filename = uploaded_file.name

na_vals = ['#VALUE!', '#DIV/0!']    #define missing data to be NaN (not a number)

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_data(file):
    st.write("New file loaded")
    return pd.read_csv(file, sep=',', encoding='utf-8')#, na_values=na_vals)  #Process the data in cached way to speed up processing

st.header('Analyzing file "' + filename + '"')

df = load_data(file)

#==== Pre-process data ====
#force 'Decision' column to be a string, not Bool and all uppercase
df['Decision'] = df['Decision'].astype(str)
df['Decision'] = df['Decision'].str.upper()


sidebar_modifier_slot = st.sidebar.empty()
my_slot1 = st.empty()   #save this spot to fill in later for how many rows get selected with the filter


# Sliders and filter
st.sidebar.subheader("**Filters**")
price_slider = st.sidebar.slider('Price ($) between:', min_value=0, max_value=int(max(df['Total Cost'])), value=(0,int(max(df['Total Cost']))))
downloads_slider = st.sidebar.slider('2020 total item requests (equivalent to COUNTER4 for 2019) between (0 uses removed):', min_value=0, max_value=int(max(df['2020 total item requests (equivalent to COUNTER 4 for 2019)'])), value=(0,int(max(df['2020 total item requests (equivalent to COUNTER 4 for 2019)']))), help='Average per year over the next five years')
cpu_slider = st.sidebar.slider('Cost per Use 2020 between:', min_value=0.0, max_value=max(df['CPU_2020']), value=(0.0,max(df['CPU_2020'])), help='CPU Rank ranges from 0 to max number of journals in the dataset')
#filter_1figr = st.sidebar.slider('1figr Tier (where available):', min_value=0, max_value=int(max(df['1figr Tier'])), value=(0, int(max(df['1figr Tier']))),help='Based on the 2018 1Science report, tiers carried over to here')
subscribed_filter = st.sidebar.radio('Decision status:',['Show All', 'KEEP', 'CANCEL', 'MAYBE', 'NotANumber'], help='Filter based on the current Decision status')


subscribed_filter_flag = 0
if subscribed_filter == "NotANumber":
    subscribed_filter = "NAN"
if subscribed_filter != 'Show All':
    subscribed_filter_flag = 1

#could also use between: (df['cpu_rank'].between(cpu_slider[0], cpu_slider[1]))
filt = ( (df['2020 total item requests (equivalent to COUNTER 4 for 2019)'] >= downloads_slider[0]) & (df['2020 total item requests (equivalent to COUNTER 4 for 2019)'] <= downloads_slider[1]) &
        (df['Total Cost'] >= price_slider[0]) & (df['Total Cost'] <= price_slider[1]) &
        (df['CPU_2020'] >= cpu_slider[0]) & (df['CPU_2020'] <= cpu_slider[1]) #&
        #(df['1figr Tier'] >= filter_1figr[0]) & (df['1figr Tier'] <= filter_1figr[1])   #104 have 1figr Tier of N/A, can't use it
        )
#st.write("filt is ",filt)


if subscribed_filter_flag:      #add another filter part, have to do it this way so Subscribed=ALL works
    filt2 = (df['Decision'] == subscribed_filter)
    st.write(filt2, subscribed_filter)
    filt = filt & filt2

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(df[filt])
    
my_slot2 = st.empty()   #save this spot to fill in later with the summary table of counts and sum$ by Subscribed

#Report the number of journals the filter selected
selected_jnls = str(df[filt].shape[0])
total_jnls = str(df.shape[0])
cost_sum = df[filt]['Total Cost'].sum()  #cost of selected journals
currency_string = "${:,.0f}".format(cost_sum)   #format with $, commas, and no decimal points
my_slot1.subheader(selected_jnls + ' rows selected out of ' + total_jnls + ' rows, costing a total of ' + currency_string)


#set up the color maps on 'subscribed'
subscribed_colorscale = alt.Scale(domain = ['KEEP', 'CANCEL', 'MAYBE', ' ', 'NAN'],
                                  range = ['blue', 'red', 'green', 'lightgray', 'black'])


#Put Modifier down here after the filt definition so only those titles that meet the filt show up, but put into empty slot further up the sidebar for flow
with sidebar_modifier_slot:
    with st.beta_expander("Change a journal's Subscribed status:"):
        filtered_titles_df = df.loc[filt]['Title Name']      #make a new df with only the valid titles
        #then give those valid titles as choices in the Modifier, was causing problems when trying to offer them through a filter, kept trying to use the index but wouldn't be there anymore
        selected_titles = st.multiselect('Journal Name:', pd.Series(filtered_titles_df.reset_index(drop=True)), help='Displayed in order provided by the underlying datafile')
        #st.write(selected_titles)
    
        col1, col2 = st.beta_columns([2,1])
    
        with col1:
            radiovalue = st.radio("Change 'Decision' status to:", ['KEEP', 'MAYBE', 'CANCEL', '(blank)'])
            if radiovalue == "(blank)":
                radiovalue = "NAN"
                #write(radiovalue)
        with col2:
            st.write(" ")       #Move the Commit button down vertically
            st.write(" ")       #I'm sure there's a smarter way to do this, but oh well
            if st.button('Commit change!'):
                for title in selected_titles:
                    title_filter = (df['Title Name'] == title)
                    df.loc[title_filter, 'Decision'] = radiovalue



### Summary dataframe created to show count and sum$ by Subscribed status
summary_df = df[filt].groupby('Decision', dropna=False)['Total Cost'].agg(['count','sum'])
summary_df['sum'] = summary_df['sum'].apply(lambda x: "${0:,.0f}".format(x))
#now formatted as a string (f)
#leading dollar sign, add commas, round result to 0 decimal places
my_slot2.write(summary_df.sort_index(ascending=False))  #display in order of TRUE, MAYBE, FALSE, blank




########  Charts start here  ########
st.subheader('Start by looking at the overall usage')
# CPU_2020 vs. Cost (x)
CPU_2020 = alt.Chart(df[filt]).mark_circle(size=75, opacity=0.5).encode(
    alt.X('Total Cost:Q', axis=alt.Axis(format='$,.2r'), scale=alt.Scale(clamp=True)),
    alt.Y('CPU_2020:Q', title='Cost per Use 2020'), #scale=alt.Scale(type='log')
    color=alt.Color('Decision:N', scale=subscribed_colorscale),   #Nominal data type
    #color=alt.condition(selection1, alt.Color('Decision:N', scale=subscribed_colorscale), alt.value('lightgray')),   #Nominal data type
    tooltip=['Title Name','Format', 'Total Cost', 'CPU_2020', '2020 total item requests (equivalent to COUNTER 4 for 2019)', 'Package or package title', '1figr Tier', 'Decision', 'Usage Stats Notes'],
    ).interactive().properties(
        height=500,
        title={
            "text": ["CPU_2020 vs. Cost, color-coded by Decision status"],
            "subtitle": ["Graph supports pan, zoom, and live-updates from changes in filters on left sidebar"],
            "color": "black",
            "subtitleColor": "gray"
        }
        )#.add_selection(selection1)
st.altair_chart(CPU_2020, use_container_width=True)

selection1 = alt.selection_multi(fields=['Package or package title'], bind='legend')
CPU_2020_2 = alt.Chart(df[filt]).mark_circle(size=75, opacity=0.5).encode(
    alt.X('Total Cost:Q', axis=alt.Axis(format='$,.2r'), scale=alt.Scale(clamp=True)),
    alt.Y('CPU_2020:Q', title='Cost per Use 2020'), #scale=alt.Scale(type='log')
    #color=alt.Color('Package or package title:N'),   #Nominal data type
    color=alt.condition(selection1, alt.Color('Package or package title:N'), alt.value('lightgray')),   #Nominal data type
    tooltip=['Title Name','Format', 'Total Cost', 'CPU_2020', '2020 total item requests (equivalent to COUNTER 4 for 2019)', 'Package or package title', '1figr Tier', 'Decision', 'Usage Stats Notes'],
    ).interactive().properties(
        height=500,
        title={
            "text": ["CPU_2020 vs. Cost, color-coded by Package yes/no"],
            "subtitle": ["Same graph as above, but now by Package, clickable legend"],
            "color": "black",
            "subtitleColor": "gray"
        }
        ).add_selection(selection1)
st.altair_chart(CPU_2020_2, use_container_width=True)

selection2 = alt.selection_multi(fields=['Package or package title'], bind='legend')
usage_2019_vs_2020 = alt.Chart(df[filt]).mark_circle(size=75, opacity=0.5).encode(
    alt.X('2020 total item requests (equivalent to COUNTER 4 for 2019):Q'),
    alt.Y('2019 total item requests (COUNTER 4):Q'),
    #color=alt.Color('Package or package title:N'),   #Nominal data type
    color=alt.condition(selection2, alt.Color('Package or package title:N'), alt.value('lightgray')),   #Nominal data type
    tooltip=['Title Name','Format', 'Total Cost', 'CPU_2020', '2020 total item requests (equivalent to COUNTER 4 for 2019)','2019 total item requests (COUNTER 4)', 'Package or package title', '1figr Tier', 'Decision', 'Usage Stats Notes']
    ).interactive().properties(
        height=500,
        title={
            "text": ["Usage comparison, 2020 vs. 2019 with 1:1 trendline"],
            "subtitle": ["Is 2020 usage an anomoly? How did it fare in 2019? Clickable legend","Looks like usage was greater in 2019 (more vertical) for most cases"],
            "color": "black",
            "subtitleColor": "gray"
        }
        ).add_selection(selection2)

line = pd.DataFrame({       #create fake df so line can get drawn
    'line_x': [0,14000],
    'line_y': [0,14000],
    })

line_plot = alt.Chart(line).mark_line(opacity=0.3).encode(      #draw fake line plot
    x='line_x',
    y='line_y'
    )

st.altair_chart(usage_2019_vs_2020 + line_plot, use_container_width=True)



st.subheader("Bring in 1figr Tiers from 2018")
figr_Tier_hist = alt.Chart(df[filt].reset_index()).mark_bar().encode(
    alt.X('1figr Tier:O'),
    alt.Y('count()'),
    alt.Detail('index:Q'),
    tooltip=['1figr Tier', 'Title Name', 'CPU_2020'],
    color=alt.Color('Decision:N', scale=subscribed_colorscale)   #Nominal data type
).interactive().properties(
    height=400,
        title={
            "text": ["Histogram of 1figr Tiers"],
            "subtitle": ["Titles stacked by Tier", "NaN and 0 mean Tier was not available for that title"],
            "color": "black",
            "subtitleColor": "gray"
        }
    )
    
text = alt.Chart(df).mark_text(dx=-1, dy=-10, color='black').encode(
    alt.X('1figr Tier:O'),
    alt.Y('count()'),
    #detail=('subscribed'),
    text=alt.Text('count()')
)
#st.altair_chart(figr_Tier_hist, use_container_width=True)
st.altair_chart(figr_Tier_hist + text, use_container_width=True)



#selection1 = alt.selection_multi(fields=['1figr Tier'], bind='legend')
CPU_2020_with_1figrTier = alt.Chart(df[filt]).mark_circle(size=75, opacity=0.5).encode(
    alt.X('Total Cost:Q', axis=alt.Axis(format='$,.2r'), scale=alt.Scale(clamp=True)),
    alt.Y('CPU_2020:Q', title='Cost per Use 2020'), #scale=alt.Scale(type='log')
    color=alt.Color('Decision:N', scale=subscribed_colorscale),   #Nominal data type
    #shape=alt.Shape('1figr Tier:O'),
    #color=alt.condition(selection1, alt.Color('1figr Tier:N'), alt.value('lightgray')),   #Nominal data type
    #row='1figr Tier',
    column=alt.Column('1figr Tier:O', bin=alt.Bin(minstep=5)),
    tooltip=['Title Name','Format','1figr Tier','2020 total item requests (equivalent to COUNTER 4 for 2019)', 'Total Cost', 'CPU_2020', 'Decision'],
    ).interactive().properties(
        height=150,
        width=300,
        title={
            "text": ["CPU_2020 vs. Cost, color-coded by 1figr Tier (where available)"],
            "subtitle": ["Clickable legend, hold shift to select more than one 1figr Tier"],
            "color": "black",
            "subtitleColor": "gray"
        }
        )#.facet(row=alt.Row('1figr Tier:N'))#, sort=['1','2','4','5']))#.add_selection(selection1)
        
# st.altair_chart(
#     alt.vconcat(
#         CPU_2020_with_1figrTier.encode(color="1figr:Q"),
#         CPU_2020_with_1figrTier.encode(color="1figr:N"),
#         CPU_2020_with_1figrTier.encode(color="1figr:O")
#     )
# )
st.altair_chart(CPU_2020_with_1figrTier)#, use_container_width=True)










##### Footer in sidebar #####
#html_string = "<p style=font-size:13px>Created by Eric Schares, Iowa State University <br />If you found this useful, or have suggestions or other feedback, please email eschares@iastate.edu</p>"
#st.sidebar.markdown(html_string, unsafe_allow_html=True)

streamlit_analytics.stop_tracking(unsafe_password="testtesttest")

# Analytics code
components.html(
    """
<html>
<body>
<script>var clicky_site_ids = clicky_site_ids || []; clicky_site_ids.push(101315881);</script>
<script async src="//static.getclicky.com/js"></script>
<noscript><p><img alt="Clicky" width="1" height="1" src="//in.getclicky.com/101315881ns.gif" /></p></noscript>
</body>
</html>
    """
)


components.html(
"""
<a title="Web Analytics" href="https://statcounter.com/" target="_blank"><img src="https://c.statcounter.com/12526873/0/c525cd17/1/" alt="Web Analytics" ></a>
"""
)
