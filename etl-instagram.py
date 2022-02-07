# Esse é um projeto que desenvolvi para onde eu trabalho. Aqui, eu utilizo o Instagram Graph Api para pegar os dados de publicações do Instagram
# que seriam visualizados em um dashboard do Google Data Studio


#Importando as bibliotecas
import requests
import json
import datetime
import pandas as pd
import time
import pygsheets

# DDefine o dicionário de parâmetros. Esses são os utilizados pela API do Instagram para acessar as informações
params = dict()
params['access_token'] = 'xxxxxxxxxxxxx'  # não é um valor real
params['client_id'] = 'yyyyyyyy'  # não é um valor real
params['client_secret'] = 'zzzzzzzzzzzzzz'  # não é um valor real
params['graph_domain'] = 'https://graph.facebook.com'
params['graph_version'] = 'v12.0'
params['endpoint_base'] = params['graph_domain'] + '/' + params['graph_version'] + '/'
params['page_id'] = '0101010101001'  # não é um valor real
params['instagram_account_id'] = '0101010101'  # não é um valor real
params['ig_username'] = 'username'

# Definindo os parametros de endpoint
endpointParams = dict()
endpointParams['input_token'] = params['access_token']
endpointParams['access_token'] = params['access_token']

# Definindo as URLs
url = params['graph_domain'] + '/debug_token'

# Requisição de dados
data = requests.get(url, endpointParams)
access_token_data = json.loads(data.content)

# Define a URL
url = params['endpoint_base'] + 'oauth/access_token'

# Define os parâmetros de Endpoint
endpointParams = dict()
endpointParams['grant_type'] = 'fb_exchange_token'
endpointParams['client_id'] = params['client_id']
endpointParams['client_secret'] = params['client_secret']
endpointParams['fb_exchange_token'] = params['access_token']

# Requisição de dados
data = requests.get(url, endpointParams)
long_lived_token = json.loads(data.content)

# Define a URL para pegar os dados da mídia
url = params['endpoint_base'] + params['instagram_account_id'] + '/media'

# Define os parâmetros de endpoints
endpointParams = dict()
endpointParams[
    'fields'] = 'id,caption,media_type,media_url,permalink,timestamp,username,like_count,comments_count'  #Nesse caso, pega valores como username, contagens de likes e contagem de comentários
endpointParams['access_token'] = params['access_token']

# Requisição de dados
data = requests.get(url, endpointParams)
basic_insight = json.loads(data.content)

df = pd.DataFrame(basic_insight['data'])
df.columns = ['id', 'caption', 'media_Type', 'media_URL', 'permalink','timestamp', 'Username', 'like_count', 'comments']


media_insight = []

# Loop que pega os dados a partir do media_id. Vai pegando cada um dos dados de engajamento, impressões, alcance e quantidade de salvo dos posts
for i in basic_insight['data']:
    params['latest_media_id'] = i['id']

    # Define a URL
    url = params['endpoint_base'] + params['latest_media_id'] + '/insights'

    # Define os parâmetros de endpoints
    endpointParams = dict()
    endpointParams['metric'] = 'engagement,impressions,reach,saved'
    endpointParams['access_token'] = params['access_token']

    # Requisição de dados
    data = requests.get(url, endpointParams)
    json_data_temp = json.loads(data.content)
    media_insight.append(list(json_data_temp['data']))

engagement_list = []
impressions_list = []
reach_list = []
saved_list = []

#Loop para pegar os dados
for insight in media_insight:
    engagement_list.append(insight[0]['values'][0]['value'])
    impressions_list.append(insight[1]['values'][0]['value'])
    reach_list.append(insight[2]['values'][0]['value'])
    saved_list.append(insight[3]['values'][0]['value'])

# Cria o Dataframe
df_media_insight = pd.DataFrame(list(zip(engagement_list, impressions_list, reach_list, saved_list)),
                                columns=['Engagement', 'Impressions', 'Reach', 'Saved'])
df_media_insight.head()
df_sum_media = df_media_insight

df_complete = pd.concat([df, df_media_insight], axis=1)
df_complete['timestamp'] = pd.to_datetime(df_complete['timestamp']).dt.tz_convert(None)

url = params['endpoint_base'] + params['instagram_account_id'] + '/insights'
# Define os parâmetros de endpoints
primeiro_dia_do_ano = datetime.datetime.strptime('01/01/22 00:00:00', '%d/%m/%y %H:%M:%S')
#pega os dados de seguidores
endpointParams = dict()
endpointParams['metric'] = 'follower_count'
endpointParams['period'] = 'day'
endpointParams['since'] = datetime.datetime.utcnow() - datetime.timedelta(1)
endpointParams['until'] = datetime.datetime.utcnow()
endpointParams['access_token'] = params['access_token']
# Requisição de dados
# data = requests.get(url, endpointParams)
audience_insight = json.loads(data.content)

seguidores = (pd.DataFrame(audience_insight['data'][0]['values'])['value'].sum())
#cria o dataframe para adicionar no google sheets
df_2022 = df_complete[
    ((df_complete['timestamp'] > primeiro_dia_do_ano) & (df_complete['timestamp'] < datetime.datetime.utcnow()))].sum(
    axis=0).to_frame().transpose()
incluir = {'Data de Hoje': [datetime.datetime.now()],
           'impressions': [df_2022['Impressions'].sum()],
           'Likes': [df_2022['like_count'].sum()],
           'Reach': [df_2022['Reach'].sum()],
           'Saved': [df_2022['Saved'].sum()],
           'Comments': [df_2022['comments'].sum()],
           'Seguidores ganhos': [seguidores]
           }

df_data_final = pd.DataFrame(incluir)
df_data_final
df_data_final.to_csv('insta.csv')

gc = pygsheets.authorize(service_file='cred2.json')

# Adiciona os dados no google sheets
sh = gc.open('Analytics').sheet1
new_row = [df_data_final['Data de Hoje'][0].strftime("%d/%m/%Y"), str(df_data_final['impressions'][0]),
           str(df_data_final['Likes'][0]), str(df_data_final['Reach'][0]), str(df_data_final['Saved'][0]),
           str(df_data_final['Comments'][0]), str(df_data_final['Seguidores ganhos'][0])]
cells = sh.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
last_row = len(cells)
sh = sh.insert_rows(last_row, number=1, values=new_row)
