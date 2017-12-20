while true; do
	pgrep -f Botfuzzy77.py || screen python3 Botfuzzy77.py
	rm *.webm
	sleep 10
	git pull --quiet
	sleep 5
	git add Resc/Players.json
	git add Logs/*
	git commit -m "Updating Logs and Players file" --quiet
	git push --quiet
	sleep 10
	pip install --upgrade --no-cache-dir youtube_dl
	sleep 5
	pip install --upgrade --no-cache-dir discord.py[voice]
	sleep 2
	rm .git/index.lock
	sleep 2
done
