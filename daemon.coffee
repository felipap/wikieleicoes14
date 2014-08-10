
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
	pad = (m) ->
		if m < 10
			'0'+m
		else m
	what = "#{d.getHours()}:#{pad(d.getMinutes())}:#{pad(d.getSeconds())}: #{edit.page} (#{delta})"
	who = "by #{edit.user}"
	console.log what+Array(process.stdout.columns-what.length-who.length+1).join(' ')+who

main = ->

	# Build map WikiPage → Info
	p = {}
	for abbr, obj of pages.candidates.states
		for title, names of obj
			for name in names
				p[name] = { title: title, ref: abbr, lastEdit: new Date(0), lastAuthor: null }
	for title, names of pages.candidates.generic
		for name in names
			p[name] = { title: title, ref: "BR", lastEdit: new Date(0), lastAuthor: null }
	console.log p 

	# Listen... 'Olorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor
	wikipedia.listen (edit) ->
		
		# Ignore non-portuguese non-articles
		return unless edit.namespace in ['main', 'article'] and edit.channel is '#pt.wikipedia'

		logEdit edit
		# edit.page = 'Levy Fidelix'

		if edit.page of p and Math.abs(edit.delta) > 50
		# if true
		# 	p[edit.page] = { title: 'MOIII', ref: "BR", lastEdit: new Date(0), lastAuthor: null }
			candidato = p[edit.page]
			
			dt = Date.now() - 1*p[edit.page].lastEdit
			# Don't tweet if same user edited it less than 60 minutes ago or another user edited it less than
			# 15 minutes ago.
			if (edit.user is candidato.lastAuthor and dt < 60*60*1000) or dt < 15*60*1000
				console.log("not tweeting it anymore")
				return

			p[edit.page].lastEdit = Date.now()
			p[edit.page].lastAuthor = edit.user
			console.log p[edit.page]

			if candidato.ref is "BR"
				who = "#{edit.page}, candidato(a) a ##{candidato.title},"
			else
				switch pages.states[candidato.ref].gen
					when "F" then prep = "da"
					when "M" then prep = "do"
					else prep = "de"
				who = "#{edit.page}, candidato(a) a #{candidato.title} #{prep}# #{candidato.ref},"
			status = "Página de #{who} foi editada "
			if edit.anonymous
				status += "anonimamente. "
			else
				status += "por #{edit.user}. "
			status += edit.url

			console.log "\n\n>>>>>>>>>>>>>>>>>>>> #{status}\n\n\n\n\n"
			return
			twitter.post 'statuses/update', status: status, (err, d, r) ->
				if err
					console.log err

if require.main == module
	main()