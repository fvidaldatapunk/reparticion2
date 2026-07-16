
from supabase import create_client
from dotenv import load_dotenv
import plotly.express as px
import os
import pandas as pd
import yfinance as yf
import streamlit as st





load_dotenv()


url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

supabase = create_client(url,key)

db_reparticion = supabase.table('reparticion').select('*').execute()

df_entregas = pd.DataFrame(db_reparticion.data)
pd.set_option('display.float_format','{:.2f}'.format)

df_entregas['data'] = pd.to_datetime(df_entregas['data'])
df_entregas['Mês'] = df_entregas['data'].dt.month_name()
df_entregas['Ano'] = df_entregas['data'].dt.year
df_entregas['quincena'] = df_entregas['data'].apply(lambda x: 1 if x.day <=15 else 2)
df_entregas['Data format'] = df_entregas['data'].dt.strftime("%d/%m/%Y")

df_entregas = df_entregas.fillna(0)
df_entregas['paack'] = df_entregas['paack'].astype(int)
df_entregas['ecoscouting'] = df_entregas['ecoscouting'].astype(int)


euro = yf.Ticker('EURBRL=X')
conveu = euro.history(period='1d')['Close'].iloc[-1]

valor_paack = float(0.80)
valor_ecoscouting = float(0.60)

df_entregas['Total € Paack'] = (df_entregas['paack']*valor_paack)
df_entregas['Total € Ecoscouting'] = (df_entregas['ecoscouting']*valor_ecoscouting)
df_entregas['total_euro'] = (df_entregas['Total € Paack'] + df_entregas['Total € Ecoscouting']).round(2)
df_entregas['Total Conv R$'] = (df_entregas['total_euro']*conveu).round(2)


#visão consolidado mês
consolidado = (df_entregas.groupby('Mês').agg(
    Qtdias = ('data', 'count'),
    paack = ('paack','sum'),
    total_eu_Paack = ('Total € Paack','sum'),
    ecoscouting = ('ecoscouting','sum'),
    total_eu_Ecoscouting = ('Total € Ecoscouting','sum'),
    total_euro = ('total_euro','sum'),
    total_conv = ('Total Conv R$','sum')
    
)
               ).reset_index()


pri_quinzena = df_entregas['data']<pd.to_datetime('2026-05-16')

#visão por quinzena
df_quincena = (df_entregas.groupby(['quincena','Mês']).agg(
    Qtdias = ('data', 'count'),
    paack = ('paack','sum'),
    total_eu_Paack = ('Total € Paack','sum'),
    ecoscouting = ('ecoscouting','sum'),
    total_eu_Ecoscouting = ('Total € Ecoscouting','sum'),
    total_euro = ('total_euro','sum'),
    total_conv = ('Total Conv R$','sum')
)).reset_index().sort_values('Mês')


#visão diária

diaria = (df_entregas[[
        'Data format',
        'paack',
        'Total € Paack',
        'ecoscouting',
        'Total € Ecoscouting',
        'total_euro',
        'Total Conv R$'
]]).reset_index(drop=True)

st.title('Dashboard Repartos') 

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

col1.metric('Dias',f'{df_entregas['data'].count()}')
col2.metric('Paack',f'{df_entregas['paack'].sum()}')
col3.metric('ecoscouting',f'{df_entregas['ecoscouting'].sum()}')
col4.metric('Total € Paack',f'{df_entregas['Total € Paack'].sum():.2f}')
col5.metric('Total € Ecoscouting',f'{df_entregas['Total € Ecoscouting'].sum():.2f}')
col6.metric('Total Euro',f'{df_entregas['total_euro'].sum():.2f}')
col7.metric('Total Conv R$',f'{df_entregas['Total Conv R$'].sum():.2f}')

graf = px.line(diaria, x='Data format', y=['Total € Paack','Total € Ecoscouting'],
               title='Arrecadação por dia',labels={'Data format':'Data','value':'Total EU'})

graf.update_layout(legend=dict(title_text='',orientation='h', yanchor ='bottom',y=-0.5, xanchor='center',x=0.5))
graf.update_traces(mode='lines+markers')

graf2 = px.line(diaria, x='Data format', y=['paack','ecoscouting'],
               title='Qtd Pacotes',labels={'Data format':'Data','value':'Total'})

graf2.update_layout(legend=dict(title_text='',orientation='h', yanchor ='bottom',y=-0.5, xanchor='center',x=0.5))
graf2.update_traces(mode='lines+markers')

st.set_page_config(layout="wide")
st.header('Consolidado')
st.dataframe(consolidado.reset_index(drop=True),hide_index=True)

st.header('Quincena')
st.dataframe(df_quincena.reset_index(drop=True),hide_index=True)

st.header('Vision Diária')
st.dataframe(diaria,hide_index=True)

st.plotly_chart(graf2)
st.plotly_chart(graf)


