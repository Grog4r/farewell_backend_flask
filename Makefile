build:
	sudo docker compose build

up:
	sudo docker compose build --no-cache && sudo docker compose up

gcloud-run:
	gcloud run deploy --source . farewell-backend-flask --region=europe-west1 --port 8000
