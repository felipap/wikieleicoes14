
# Todo:
## -

Twit = require 'twit'
wikichanges = require 'wikichanges'

# refenrece
# https://github.com/edsu/wikichanges/blob/master/wikichanges.js
main = ->
	config = require './config.json'
	pages = require './pages.json'

	twitter = new Twit(config)

	wikipedia = new wikichanges.WikiChanges(ircNickname: config.nick)
	
	p = {}
	for abbr, obj of pages.states
		for title, names of obj
			for name in names
				p[name] = { title: title, ref: abbr }
	for title, names of pages.generic
		for name in names
			p[name] = { title: title, ref: "BR" }
	console.log p

	wikipedia.listen (edit) ->
		unless edit.namespace in ['main', 'article']
			return

		log = (edit) ->
			d = new Date
			delta = ""+edit.delta
			if edit.delta > 0 then delta = '+'+delta
			what = "#{d.getHours()}:#{d.getMinutes()}:#{d.getSeconds()}: #{edit.page} (#{delta})"
			who = "by #{edit.user}"
			console.log what+Array(process.stdout.columns-what.length-who.length+1).join(' ')+who

		if edit.channel is '#pt.wikipedia'
			log edit

		if edit.page of p and not edit.robot and Math.abs(edit.delta) > 15
			log edit

			console.log 'edit to'
			status = "Página de #{edit.page} foi editada "
			if edit.anonymous
				status += "anonimamente. "
			else
				status += "por #{edit.user}" 
			status += edit.url

			console.log "\n\n>>>>>>>>>>>>>>>>>>>> #{status}\n\n\n\n\n"
			twitter.post 'statuses/update', status: status, (err, d, r) ->
				if err
					console.log err

if require.main == module
	main()