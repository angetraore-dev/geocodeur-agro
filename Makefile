.PHONY: build up down logs clean

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "✅ Application disponible sur http://localhost:8501":

down:
	docker-compose down

logs:
	docker-compose logs -f

restart: down up

clean:
	docker-compose down -v
	docker system prune -f

dev:
	docker-compose up