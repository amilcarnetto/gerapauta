#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  3 23:07:31 2021

@author: developer
"""
import asyncio, aiohttp, time, requests, json, datetime, pymsteams, sys

import pandas as pd

start_time = time.time()



BASE_URL_OJCS = 'https://pje.trt6.jus.br/pje-consulta-api/api/orgaosjulgadores?somenteOJCs=true'
BASE_URL_PROCESSOS = 'https://pje.trt6.jus.br/pje-consulta-api/api/audiencias?pagina=1&tamanhoPagina=500&ordenacaoColuna=undefined&ordenacaoCrescente=undefined&idOj='

ua_firefox = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'

headers_1grau = {'x-grau-instancia':'1','User-Agent': ua_firefox}
headers_2grau = {'x-grau-instancia':'2','User-Agent': ua_firefox}


# busca todos os OJs
lista_ojs_1grau = {str(x['id']):x['descricao'] for x in json.loads(requests.get(BASE_URL_OJCS, headers={'x-grau-instancia':'1'}).text)}
lista_ojs_2grau = {str(x['id']):x['descricao'] for x in json.loads(requests.get(BASE_URL_OJCS, headers={'x-grau-instancia':'2'}).text)}

resp_ojs = {}

# busca uma determinada semana (partindo de uma data, prerencialmente segunda-feira)
def define_semana(data):
    
    dia = pd.date_range(start=datetime.datetime.strptime(data,'%d/%m/%Y'), periods=5, freq='B')
      
    # generate urls

    urls_1grau = [BASE_URL_PROCESSOS + oj + '&data=' + str(data.date()) for oj in lista_ojs_1grau for data in dia]
    urls_2grau = [BASE_URL_PROCESSOS + oj + '&data=' + str(data.date()) for oj in lista_ojs_2grau for data in dia]

    return(urls_1grau,urls_2grau)
   
    
async def fetch(session, url, grade):
    async with session.get(url) as response:
        resp = await response.json()
        # commente para não sair no relatorio
        # print('Objeto é:', resp.__class__)
        # print('Tamanho é:', len(resp))
        # print('resp.keys() é:', resp.keys())
        # print('OJ é:', lista_ojs_2grau[url.replace(BASE_URL_PROCESSOS,'').split('&')[0]])
        if len(resp) == 5:
            if grade == 1:
                resp['resultado'].append(lista_ojs_1grau[url.replace(BASE_URL_PROCESSOS,'').split('&')[0]])
            else:
                resp['resultado'].append(lista_ojs_2grau[url.replace(BASE_URL_PROCESSOS,'').split('&')[0]])
        return resp


async def fetchall(data,headers):

    pautas_completas = []
    pautas_report = []

    lista_urls_1grau, lista_urls_2grau = define_semana(data)
        
    if headers == 1:
        async with aiohttp.ClientSession(headers=headers_1grau) as session:
    
            tasks = []
            for url in lista_urls_1grau:
                tasks.append(asyncio.ensure_future(fetch(session, url,1)))
    
            pautas = await asyncio.gather(*tasks)
            for pauta in pautas:
                # print('encontrados', len(pauta), 'processos nesta pauta')
                if len(pauta) == 5:
                    pautas_completas.append(pauta['resultado'])
    
    elif headers == 2:
        async with aiohttp.ClientSession(headers=headers_2grau) as session:
    
            tasks = []
            for url in lista_urls_2grau:
                tasks.append(asyncio.ensure_future(fetch(session, url,2)))
    
            pautas = await asyncio.gather(*tasks)
            for pauta in pautas:
                if len(pauta) == 5:
                    pautas_completas.append(pauta['resultado'])
    
    semana = pd.date_range(start=datetime.datetime.strptime(data,'%d/%m/%Y'), periods=5, freq='B')                
    title = str('<h3><p>Buscando pautas do ' + str(headers) + 'º Grau - semana de ' + semana[0].to_pydatetime().strftime('%d/%m/%Y') +  \
        ' a ' +  semana[4].to_pydatetime().strftime('%d/%m/%Y') +  '</h3></p>\n')

    # print(title)
    pautas_report.append(title)

    for pauta in pautas_completas:
        oj = pauta[-1]

        for k in range(len(pauta)-1):
            pautatmp = pauta[k]
            
            
            try:
                if len(pautatmp['poloAtivo']) == 1 and (pautatmp['resumoPoloAtivo'] == 'M. P. T.'):
                        rep = str(oj +  ' Processo ' +  pautatmp['classeProcesso'] + ' ' + pautatmp['numeroProcesso'] + ' Data: ' + \
                            datetime.datetime.strptime(str(pautatmp['data'][:10]), "%Y-%m-%d").strftime('%d/%m/%Y') + \
                            ' Ativo ' + pautatmp['poloAtivo'][0]['nome'].strip() +  ' Passivo ' + pautatmp['poloPassivo'][0]['nome'].strip() + '</p>\n')
                        pautas_report.append('<p>' + str(len(pautas_report)) + ' - ' + rep)
                
                elif len(pautatmp['poloAtivo']) > 1:
                    for k in range(len(pautatmp['poloAtivo'])):
                        if (pautatmp['poloAtivo'][k]['nome'] == 'MINISTÉRIO PÚBLICO DO TRABALHO'):
                            rep = str(oj +  ' Processo ' +  pautatmp['classeProcesso'] + ' ' + pautatmp['numeroProcesso'] +  ' Data: ' + \
                                datetime.datetime.strptime(str(pautatmp['data'][:10]), "%Y-%m-%d").strftime('%d/%m/%Y') +  \
                                ' Ativo ' + pautatmp['poloAtivo'][k]['nome'].strip() + ' Passivo ' + pautatmp['poloPassivo'][k]['nome'].strip() + '</p>\n')
                            pautas_report.append('<p>' + str(len(pautas_report)) + ' - ' + rep)
                
                elif len(pautatmp['poloPassivo']) == 1 and pautatmp['resumoPoloPassivo'] == 'M. P. T.':
                        rep = str(oj +  ' Processo ' +  pautatmp['classeProcesso'] + ' ' + pautatmp['numeroProcesso'] + ' Data: ' + \
                            datetime.datetime.strptime(str(pautatmp['data'][:10]), "%Y-%m-%d").strftime('%d/%m/%Y') + \
                            ' Ativo ' + pautatmp['poloAtivo'][0]['nome'].strip() +  ' Passivo ' + pautatmp['poloPassivo'][0]['nome'].strip() + '</p>\n')
                        pautas_report.append('<p>' + str(len(pautas_report)) + ' - ' + rep)

                elif len(pautatmp['poloPassivo']) > 1:
                    for k in range(len(pautatmp['poloPassivo'])):
                        if (pautatmp['poloPassivo'][k]['nome'] == 'MINISTÉRIO PÚBLICO DO TRABALHO'):
                            rep = str(oj +  ' Processo ' +  pautatmp['classeProcesso'] + ' ' + pautatmp['numeroProcesso'] +  ' Data: ' + \
                                datetime.datetime.strptime(str(pautatmp['data'][:10]), "%Y-%m-%d").strftime('%d/%m/%Y') +  \
                                ' Ativo ' + pautatmp['poloAtivo'][k]['nome'].strip() + ' Passivo ' + pautatmp['poloPassivo'][k]['nome'].strip() + '</p>\n')
                            pautas_report.append('<p>' + str(len(pautas_report)) + ' - ' + rep)
            except:
                pass


               
    return tasks, pautas_completas, pautas_report


def main():

    data = sys.argv[1]

    tasks1, pautas1, pautas1_report = asyncio.run(fetchall(data,1))
    tasks2, pautas2, pautas2_report = asyncio.run(fetchall(data,2))

    message_pautas  = ''

    message_pautas = message_pautas.join(pautas1_report + pautas2_report)

    print(message_pautas)

    message_detalhar = ''


    for k in range(1,len(pautas2_report)):
        pauta_tmp = pautas2_report[k].split(' ')
        message_detalhar += '<p> Detalhar Processo ' + pauta_tmp[5] + ' ' + pauta_tmp[6] + '</p>\n'

    print(message_detalhar)


    print("--- %s seconds ---" % (time.time() - start_time))
    


if __name__ == '__main__':
    main()
