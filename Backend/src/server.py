# Import notweniger Bibliotheken / AbhÃ¤ngigkeiten / Module
from flask import Flask, request
import pandas as pd
import json
from collections import Counter

# Instanz eines Python-Webservers
app = Flask(__name__)

# Route hinzufÃ¼gen, die aufrufbar ist unter /info
@app.route('/info')
def info():
    
  return 'Server is running'

#berechnet den absoluten und den relativen Verlauf aus den einzelnen Tagen für das jeweilige Land, welches als 
#Parameter über den request übergeben wurde.
#wandelt anschließend die Daten in ein JSON Object um.
@app.route('/showPlot')
def showPlot():
    country = request.args.get('country')
    df = pd.read_csv('https://opendata.ecdc.europa.eu/covid19/casedistribution/csv')
    data = df.set_index('countriesAndTerritories', drop = True).loc[country,'dateRep':'popData2018']
    data = data.reset_index()
    total_cases = []
    relative_cases = []
    total_deaths =[]
    relative_deaths = []
    max_index = len(data)
    cases = 0
    deaths = 0
    for i in range(max_index):
        
        cases += data.loc[max_index-i-1, 'cases']
        relative = cases/data.loc[max_index-i-1, 'popData2018']*100
        relative_cases.insert(0, relative)
        deaths += data.loc[max_index-i-1, 'deaths']
        relative = deaths/cases*100
        relative_deaths.insert(0,relative)
        total_cases.insert(0,cases)
        total_deaths.insert(0,deaths)
            
    
    data['total_cases'] = total_cases 
    data['total_deaths'] = total_deaths      
    data['cases_relative_to_pop'] = relative_cases
    data['deathrate'] = relative_deaths
    data = data.drop(['countriesAndTerritories','day','month','year', 'geoId', 'countryterritoryCode', 'popData2018'], axis = 1)
    json_object = data.to_json(orient = 'index')
    return json_object

#Gibt die Daten zu den einzelnen Tagen, sprich den täglichen Anstieg, absolut und relativ zurück.
#speichert zunächst die Daten in einem Dictionary und wandelt dieses schließlich in ein JSON Object um.
#Ob Todeszahlen oder Fallzahlen ermittelt werden sollen wird über den Parameter "cod" angegeben.
@app.route('/dailyIncrease')
def dailyIncrease():
    country = request.args.get('country')
    cases_or_deaths = request.args.get('cod')
    df = pd.read_csv('https://opendata.ecdc.europa.eu/covid19/casedistribution/csv')
    data = df.set_index('countriesAndTerritories', drop = True).loc[country,'dateRep':'popData2018']
    data = data.reset_index()
    total_dic = {}
    relative_dic = {}
    max_index = len(data)
    dictionary ={}
    for i in range(max_index):
        
        deaths = data.loc[max_index-i-1, 'deaths']
        cases = data.loc[max_index-i-1, 'cases']
        date = data.loc[max_index-i-1, 'dateRep']
        if i>0:
            cases_yesterday = data.loc[max_index-i, 'cases']
            deaths_yesterday = data.loc[max_index-i, 'deaths']
            if cases_or_deaths == 'cases':
                if cases_yesterday !=0:
                    relative = (cases/cases_yesterday-1)*100
                    relative_dic[date] = float(relative)
            else:
                if deaths_yesterday != 0:
                    relative = (deaths/deaths_yesterday-1)*100
                    relative_dic[date] = float(relative)
        
        if cases_or_deaths == 'cases' and cases != 0:
            total_dic[date] = int(cases)
        elif cases_or_deaths =='deaths' and deaths != 0:
            total_dic[date] = int(deaths)
            
    dictionary['total'] = total_dic
    dictionary['relative'] = relative_dic
    json_object = json.dumps(dictionary)
    return json_object

#Täglicher Anstieg für den ganzen Kontinent
@app.route('/dailyIncreaseCont')
def dailyIncreaseCont():
    df = pd.read_csv('https://opendata.ecdc.europa.eu/covid19/casedistribution/csv')
    continent = request.args.get('continent')
    cases_or_deaths = request.args.get('cod')
    data = df.set_index('continentExp', drop = True).loc[continent]
    data['dateRep'] = pd.to_datetime(data['dateRep'], format= '%d/%m/%Y')
    data = data.reset_index()
    current_date = ''
    dates = []
    for index, row in data.iterrows():
        if row['dateRep'] != current_date and not row['dateRep'] in dates:
            current_date = row['dateRep']
            dates.append(current_date)
            
    dates.sort() 
    data = data.set_index('dateRep',drop = True)
    dictionary = {}
    totaldic = {}
    reldic = {}
    cases = 0
    deaths = 0
    cases_yesterday = 0
    deaths_yesterday = 0
    
    for date in dates:
        subdata = data.loc[date]
        key = str(date.day) + '/' + str(date.month) + '/' + str(date.year)
        if isinstance(subdata, pd.DataFrame):
            if cases_or_deaths == 'cases':
                cases= subdata['cases'].sum()
                if cases_yesterday != 0:
                    relative = (cases/cases_yesterday-1)*100
                    reldic[key] = float(relative)
                if cases != 0:
                    totaldic[key] = int(cases)
            else:
                deaths = subdata['deaths'].sum()
                if deaths_yesterday != 0:
                    relative = (deaths/deaths_yesterday-1)*100
                    reldic[key] = float(relative)
                if deaths != 0:
                    totaldic[key] = int(deaths)
        #in manchen Fällen gibt es zum aktuellen Datum nur einen Eintrag, sprich subdata muss als Series behandelt werden und nicht als Dataframe
        else:
            for index, row in subdata.items():
                if index == 'cases' and cases_or_deaths == 'cases':
                    cases = row
                    if cases_yesterday != 0:
                        relative = (cases/cases_yesterday-1)*100
                        reldic[key] = float(relative)
                    if cases != 0:
                        totaldic[key] = int(cases)
                elif index == 'deaths' and cases_or_deaths == 'deaths':
                    deaths = subdata['deaths'].sum()
                    if deaths_yesterday != 0:
                        relative = (deaths/deaths_yesterday-1)*100
                        reldic[key] = float(relative)
                    if deaths != 0:
                        totaldic[key] = int(deaths)
                        
        cases_yesterday = cases
        deaths_yesterday = deaths
                    
    dictionary['total'] = totaldic
    dictionary['relative'] = reldic
    json_object = json.dumps(dictionary)
    return json_object       
                
#Ermittelt die top 10 Länder der Erde relativ und absolut. 
@app.route('/topTenWorld')
def top_ten_world():
    data = pd.read_csv('https://opendata.ecdc.europa.eu/covid19/casedistribution/csv')
    cases_or_deaths = request.args.get('cod')
    current_country = ''
    dictionary = {}
    for index, row in data.iterrows():
        if row['countriesAndTerritories'] != current_country:
            current_country = row['countriesAndTerritories']
            total_cases = []
            subdata = data.set_index('countriesAndTerritories', drop = True).loc[current_country]
            subdata = subdata.reset_index()
            max_index = len(subdata)
            cases = 0
            deaths = 0
            total_deaths = []
            deathrates = []
            relative_cases = []
            subdict = {}
            for i in range(max_index):
                cases += subdata.loc[max_index-i-1, 'cases']
                deaths += subdata.loc[max_index-i-1, 'deaths']
                if cases == 0:
                    deathrate = 0
                else:
                    deathrate = deaths/cases*100
                deathrates.insert(0, deathrate)
                if not pd.isna(subdata.loc[max_index-i-1, 'popData2018']):
                    relative = cases/subdata.loc[max_index-i-1, 'popData2018']*100
                    relative_cases.insert(0, relative)
                else:
                    relative_cases.insert(0, 0)
                    
                total_cases.insert(0,cases)
                total_deaths.insert(0, deaths)
            
            if(cases_or_deaths == 'cases'):
                subdict['total'] = total_cases[0]
                subdict['relative'] = relative_cases[0]
            else:
                subdict['total'] = total_deaths[0]
                subdict['relative'] = deathrates[0]
            
            dictionary[current_country] = subdict
      
    
    relative = {} 
    total = {}
    for key, dictionaries in dictionary.items():
        relative[key] = float(dictionaries['relative'])
        total[key] = int(dictionaries['total'])
  
    t = Counter(total)
    r = Counter(relative)
    # Die 10 höchsten Werte ermitteln
    high_total = t.most_common(10)  
    high_relative = r.most_common(10)    

    d = {}
    relative = {} 
    total = {}
    for i in high_total:
        total[i[0]] = i[1]
    for i in high_relative:
        relative[i[0]] = i[1]
    d['total'] = total
    d['relative'] = relative
    
    json_object = json.dumps(d)
    return json_object

#ermittelt die top 10 Länder eines Kontinents, der via Parameter übermittelt wird.
@app.route('/topTen')
def top_ten():
    df = pd.read_csv('https://opendata.ecdc.europa.eu/covid19/casedistribution/csv')
    continent = request.args.get('continent')
    cases_or_deaths = request.args.get('cod')
    data = df.set_index('continentExp', drop = True).loc[continent]
    current_country = ''
    dictionary = {}
    for index, row in data.iterrows():
        if row['countriesAndTerritories'] != current_country:
            current_country = row['countriesAndTerritories']
            total_cases = []
            subdata = data.set_index('countriesAndTerritories', drop = True).loc[current_country]
            subdata = subdata.reset_index()
            max_index = len(subdata)
            cases = 0
            deaths = 0
            total_deaths = []
            deathrates = []
            relative_cases = []
            subdict = {}
            for i in range(max_index):
                cases += subdata.loc[max_index-i-1, 'cases']
                deaths += subdata.loc[max_index-i-1, 'deaths']
                if cases == 0:
                    deathrate = 0
                else:
                    deathrate = deaths/cases*100
                deathrates.insert(0, deathrate)
                if not pd.isna(subdata.loc[max_index-i-1, 'popData2018']):
                    relative = cases/subdata.loc[max_index-i-1, 'popData2018']*100
                    relative_cases.insert(0, relative)
                else:
                    relative_cases.insert(0, 0)
                    
                total_cases.insert(0,cases)
                total_deaths.insert(0, deaths)
            
            if(cases_or_deaths == 'cases'):
                subdict['total'] = total_cases[0]
                subdict['relative'] = relative_cases[0]
            else:
                subdict['total'] = total_deaths[0]
                subdict['relative'] = deathrates[0]
            
            dictionary[current_country] = subdict
      
    
    relative = {} 
    total = {}
    for key, dictionaries in dictionary.items():
        relative[key] = float(dictionaries['relative'])
        total[key] = int(dictionaries['total'])
  
    t = Counter(total)
    r = Counter(relative)
    # 10 höchsten Werte ermitteln 
    high_total = t.most_common(10)  
    high_relative = r.most_common(10)    

    d = {}
    relative = {} 
    total = {}
    for i in high_total:
        total[i[0]] = i[1]
    for i in high_relative:
        relative[i[0]] = i[1]
    d['total'] = total
    d['relative'] = relative
    
    json_object = json.dumps(d)
    return json_object

#Ermittelt die Verlaufszahlen für einen ganzen Kontinent, ordnet den Gesamtwert dem jeweiligen Datum zu.
@app.route('/continentalProgress')
def continentalProgress():
    df = pd.read_csv('https://opendata.ecdc.europa.eu/covid19/casedistribution/csv')
    continent = request.args.get('continent')
    cases_or_deaths = request.args.get('cod')
    data = df.set_index('continentExp', drop = True).loc[continent]
    data['dateRep'] = pd.to_datetime(data['dateRep'], format= '%d/%m/%Y')
    data = data.reset_index()
    current_date = ''
    total_continent = 0
    total_cases = 0
    dates = []
    for index, row in data.iterrows():
        if row['dateRep'] != current_date and not row['dateRep'] in dates:
            current_date = row['dateRep']
            dates.append(current_date)
            
    dates.sort() 
    data = data.set_index('dateRep',drop = True)
    dictionary = {}
    totaldic = {}
    reldic = {}
    
                
    for date in dates:
        continent_population = 0
        subdata = data.loc[date]
        if isinstance(subdata, pd.DataFrame):
            for index, row in subdata.iterrows():
                if not pd.isna(row['popData2018']):
                    continent_population += row['popData2018']
            total_cases += subdata['cases'].sum()
            if cases_or_deaths == 'cases':
                total_continent = total_cases      
                relative_continent = total_continent/continent_population*100
            else:
                total_continent += subdata['deaths'].sum()
                if total_cases == 0:
                    relative_continent = 0
                else:
                    relative_continent = total_continent/total_cases*100
                
            key = str(date.day) + '/' + str(date.month) + '/' + str(date.year)
            reldic[key] = float(relative_continent)
            totaldic[key] = int(total_continent)
        else:
            for index, row in subdata.items():
                if index == 'popData2018':
                    if not pd.isna(row):
                        continent_population += row
                elif index == 'cases':
                    total_cases += row
                    if cases_or_deaths == 'cases':
                        total_continent = total_cases
                elif index == 'deaths' and cases_or_deaths == 'deaths':
                    total_continent += row
            
            if cases_or_deaths == 'cases': 
                relative_continent = total_continent/continent_population*100
            else:
                if total_cases == 0:
                    relative_continent = 0
                else:
                    relative_continent = total_continent/total_cases*100
            key = str(date.day) + '/' + str(date.month) + '/' + str(date.year)
            reldic[key] = float(relative_continent)
            totaldic[key] = int(total_continent)
        
    dictionary['total'] = totaldic
    dictionary['relative'] = reldic
            
    json_object = json.dumps(dictionary)
    return json_object

#Ermittelt die top 10 Kontinente
@app.route('/topContinents')        
def topContinents():
    df = pd.read_csv('https://opendata.ecdc.europa.eu/covid19/casedistribution/csv')
    cases_or_deaths = request.args.get('cod')
    df = df.set_index('continentExp', drop = True)   
    continents = []    
    dictionary = {}
    
    for index, row in df.iterrows():
        if index not in continents:
            continents.append(index)
    
    for continent in continents:
        data = df.loc[continent]
        subdict = {}
        current_country = ''
        pop_list = []
        
        for index, row in data.iterrows():
            if row['countriesAndTerritories'] != current_country and not pd.isna(row['popData2018']):
                current_country = row['countriesAndTerritories']
                pop_list.append(row['popData2018'])
                
        if cases_or_deaths == 'cases':
            subdict['total'] =int(data['cases'].sum())
            subdict['relative'] = float(data['cases'].sum()/sum(pop_list)*100)
        else:
            subdict['total'] = int(data['deaths'].sum())
            subdict['relative']= float(data['deaths'].sum()/data['cases'].sum()*100)
        
            
        dictionary[continent] = subdict
        
    relative = {} 
    total = {}
    for key, dictionaries in dictionary.items():
        relative[key] = float(dictionaries['relative'])
        total[key] = int(dictionaries['total'])
  
    t = Counter(total)
    r = Counter(relative)
    # die 10 höchsten Werte ermitteln
    high_total = t.most_common(10)  
    high_relative = r.most_common(10)    

    d = {}
    relative = {} 
    total = {}
    for i in high_total:
        total[i[0]] = i[1]
    for i in high_relative:
        relative[i[0]] = i[1]
    d['total'] = total
    d['relative'] = relative
    
    json_object = json.dumps(d)
    return json_object

# Start des Python-Webservers, mit Port 4000
app.run(host='0.0.0.0', port=4000)