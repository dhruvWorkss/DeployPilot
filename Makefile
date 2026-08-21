.PHONY: up down logs test lint validate

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

test:
	docker compose run --rm api pytest

lint:
	docker compose run --rm api ruff check .
	docker compose run --rm web npm run lint

validate:
	docker compose config --quiet
	kubectl apply --dry-run=client -f deploy/kubernetes
	terraform -chdir=infra/terraform fmt -check -recursive
