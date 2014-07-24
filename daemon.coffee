
# Todo:
## -

Twit = require 'twit'
wikichanges = require 'wikichanges'

config = require './config.json'
pages = require './pages.json'

twitter = new Twit(config)
wikipedia = new wikichanges.WikiChanges(ircNickname: config.nick)

logEdit = (edit) ->
	d = new Date
	delta = ""+edit.delta
	if edit.delta > 0 then delta = '+'+delta
	what = "#{d.getHours()}:#{d.getMinutes()}:#{d.getSeconds()}: #{edit.page} (#{delta})"
	who = "by #{edit.user}"
	console.log what+Array(process.stdout.columns-what.length-who.length+1).join(' ')+who

main = ->

	p = {}
	for abbr, obj of pages.states
		for title, names of obj
			for name in names
				p[name] = { title: title, ref: abbr }
	for title, names of pages.generic
		for name in names
			p[name] = { title: title, ref: "BR", lastEdit: new Date(0), lastAuthor: null }
	console.log p

	wikipedia.listen (edit) ->
		unless edit.namespace in ['main', 'article']
			return

		if edit.channel isnt '#pt.wikipedia'
			return

		logEdit edit
		if edit.page of p and not edit.robot and Math.abs(edit.delta) > 50
			candidato = p[edit.page]
			
			dt = Date.now() - 1*p[edit.page].lastEdit
			# Don't tweet if same user edited it less than 60 minutes ago or another user edited it less than
			# 15 minutes ago.
			if (edit.user is candidato.lastAuthor and dt < 60*60*1000) or
			dt < 15*60*1000
				console.log("not tweeting it anymore")
				return

			p[edit.page].lastEdit = Date.now()
			p[edit.page].lastAuthor = edit.user
			console.log p[edit.page]

			if candidato.ref is "BR"
				name = "#{edit.page}, candidato(a) a #{candidato.title},"
			else
				name = "#{edit.page}, candidato(a) a #{candidato.title} do #{candidato.ref},"
			status = "Página de #{name} foi editada "
			if edit.anonymous
				status += "anonimamente. "
			else
				status += "por #{edit.user}. "
			status += edit.url

			console.log "\n\n>>>>>>>>>>>>>>>>>>>> #{status}\n\n\n\n\n"
			twitter.post 'statuses/update', status: status, (err, d, r) ->
				if err
					console.log err

if require.main == module
	main()