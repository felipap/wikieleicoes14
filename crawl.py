#!/usr/bin/env python3
# -*- encoding ut8 -*-
"""
Crawler para colher informações sobre os candidatos no site do TSE.
"""

import urllib.request
import urllib.parse

from bs4 import BeautifulSoup

BASE_URL = 'http://divulgacand2014.tse.jus.br'
FORM_URL = 'http://divulgacand2014.tse.jus.br/divulga-cand-2014/eleicao/2014/UF/%s/candidatos/cargo/%d'

URLS = {
	'presidente': FORM_URL % ('BR', 1),
	'vicepresidente': FORM_URL % ('BR', 2),
	'governador': lambda state: FORM_URL % (state, 3),
	'vicegovernador': lambda state: FORM_URL % (state, 4),
	'senador': lambda state: FORM_URL % (state, 5),
	'deputado_federal': lambda state: FORM_URL % (state, 6),
	'deputado_estadual': lambda state: FORM_URL % (state, 7),
}

def get_html(url: str):
	file = urllib.request.urlopen(url)
	return file.read()

def deserialize_valor(valor: str):
	import re
	match = re.search("R\$ (\d{,3}(?:\.\d{3})*),(\d{2})", valor)
	full = match.group(1)
	decimal = match.group(2)
	return float(full.replace('.', ''))+int(decimal)/100

def serialize_valor(valor: float):
	s = "R$ {0:,}".format(valor)
	# Hack to switch collons and dots in notation
	return s.replace(',','-').replace('.',',').replace('-','.')

def parseCandidatePage(soup: BeautifulSoup):
	assert isinstance(soup, BeautifulSoup), "Argument supplied isn't a BeautifulSoup object."
	table = soup.find('table', 'table table-condensed table-striped')

	def getTableItem (table, row, col):
		return table.select('tr:nth-of-type(%d) td:nth-of-type(%d)' % (row, col))[0]

	candidate = {
		'nomeUrna': 	getTableItem(table.tbody, 1, 1).get_text(),
		'numeroUrna': 	getTableItem(table.tbody, 1, 2).get_text(),
		'nomeCompleto': getTableItem(table.tbody, 2, 1).get_text(),
		'genero': 		getTableItem(table.tbody, 2, 2).get_text(),
		'nascimento':	getTableItem(table.tbody, 3, 1).get_text(),
		'estadoCivil':	getTableItem(table.tbody, 3, 2).get_text(),
		'raca':			getTableItem(table.tbody, 4, 1).get_text(),
		'nacionalidade':getTableItem(table.tbody, 5, 1).get_text(),
		'naturalidade':	getTableItem(table.tbody, 5, 2).get_text(),
		'escolaridade': getTableItem(table.tbody, 6, 1).get_text(),
		'ocupacao':		getTableItem(table.tbody, 6, 2).get_text(),
		'enderecoWeb':	getTableItem(table.tbody, 7, 1).get_text(),
		'partido':		getTableItem(table.tbody, 8, 1).get_text(),
		'coligacao':	getTableItem(table.tbody, 9, 1).get_text(),
		'composicaoColigacao':getTableItem(table.tbody, 10, 1).get_text(),
		'numeroProcesso':	getTableItem(table.tbody, 11, 1).get_text(),
		'numeroProtocolo':	getTableItem(table.tbody, 11, 2).get_text(),
		'cnpj':			getTableItem(table.tbody, 12, 1).get_text(),
		'limiteGastos':	getTableItem(table.tbody, 12, 2).get_text(),
	}

	# Parse table of assets
	tableBens = soup.find(id='tab-bens')
	# Check also for no assets (= no tr > td)
	if tableBens and tableBens.tbody.select('tr td'):
		candidate['bens'] = []
		total = 0
		for row in tableBens.tbody.find_all('tr'):
			cols = row.find_all('td')
			item = {
				'nome': cols[0].get_text(),
				'valor': cols[1].get_text(),
			}
			candidate['bens'].append(item)
			total += deserialize_valor(cols[1].get_text())
		candidate['totalBensDeclarados'] = serialize_valor(total)
	
	# Parse table of documents
	tableDocs = soup.find(id='tab-docs')
	# Check also for no assets (= no tr > td)
	if tableDocs and tableDocs.tbody.select('tr td'):
		candidate['docs'] = []
		for row in tableDocs.tbody.find_all('tr'):
			item = {
				'documento': row.find('td').a.get_text(),
				'endereco': urllib.parse.urljoin(BASE_URL, row.find('td').a['href']),
			}
			candidate['docs'].append(item)

	# Parse table of plans
	tableProposals = soup.find(id='tab-propostas')
	# Check also for no assets (= no tr > td)
	if tableProposals and tableProposals.tbody.select('tr td'):
		candidate['propostas'] = []
		for row in tableProposals.tbody.find_all('tr'):
			item = {
				'documento': row.find('td').a.get_text(),
				'endereco': urllib.parse.urljoin(BASE_URL, row.find('td').a['href']),
			}
			candidate['propostas'].append(item)

	# Parse table of previous elections
	tablePrevElections = soup.find(id='tab-el-anteriores')
	# Check also for no assets (= no tr > td)
	if tablePrevElections and tablePrevElections.tbody.select('tr td'):
		candidate['eleicoesAnteriores'] = []
		for row in tablePrevElections.tbody.find_all('tr'):
			cols = row.find_all('td')
			item = {
				'ano': cols[0].get_text(),
				'detalhe': urllib.parse.urljoin(BASE_URL, cols[1].a['href']),
			}
			candidate['eleicoesAnteriores'].append(item)

	tableCorr = soup.find(id='tab-corr')
	if tableCorr and tableCorr.tbody.select('tr td'):
		cols = tableCorr.tbody.tr.find_all('td')
		candidate['suplente'] = {
			'numero': cols[0].get_text(),
			'nome': cols[1].get_text(),
			'endereco': urllib.parse.urljoin(BASE_URL, cols[2].a['href']),
		}

	candidate['meta'] = { 'lastUpdate': soup.find('input', id="dtUltimaAtualizacao")['value'] }

	return candidate

def parseCandidateList(soup: BeautifulSoup):
	assert isinstance(soup, BeautifulSoup), "Argument supplied isn't a BeautifulSoup object."
	table = soup.find(id="tbl-candidatos")
	rows = table.tbody.find_all('tr', 'row-link-cand')

	candidates = {}
	for row in rows:
		candidates[row['id']] = {
			'id': row['id'],
			'url': urllib.parse.urljoin(BASE_URL, row.select('td:nth-of-type(1) a')[0]['href']),
			'nomeCompleto': row.select('td:nth-of-type(2)')[0].get_text(),
			'codigo': row.select('td:nth-of-type(3)')[0].get_text(),
			'status': row.select('td:nth-of-type(4)')[0].get_text(),
			'partido': row.select('td:nth-of-type(5)')[0].get_text(),
			'coligacao': row.select('td:nth-of-type(6)')[0].get_text()
		}
	return candidates

###

import json
def prettify(obj):
	return json.dumps(obj, indent=4)

def getList(url):
	html = get_html(url)
	soup = BeautifulSoup(html)
	print(url)
	try:
		candidates = parseCandidateList(soup)
	except:
		raise Exception("PQP."+url)
	# print(prettify(candidates))

	result = {}
	for k in candidates:
		url = urllib.parse.urljoin(BASE_URL, candidates[k]['url'])
		soup = BeautifulSoup(get_html(url))
		try:
			person = parseCandidatePage(soup)
		except:
			raise Exception("PQP."+k)

		person.update(candidates[k])
		result[k] = person
		print(person['nomeUrna'])

	return result

siglas = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']

if __name__ == "__main__":
	urls = {
		'presidente': URLS['presidente'],
		'vicepresidente': URLS['vicepresidente'],
	}

	for n, state in enumerate(siglas):
		print(n, state)
		urls['governador'+state] = URLS['governador'](state)
		urls['vicegovernador'+state] = URLS['vicegovernador'](state)
		# urls['senador'+state] = URLS['senador'](state)

	for key in urls:
		file = open('data/'+key+'.json', 'w+')
		file.write(json.dumps({key:getList(urls[key])}, indent=4))
		file.close()