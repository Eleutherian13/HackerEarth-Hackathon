# ADR-004: Redis + Celery vs in-memory queues

## Context
PDF processing, OCR, extraction, verification, and notification tasks can take longer than a single API request and must survive process restarts. The workflow also needs retry behavior, queue visibility, and separation between web request handling and task execution.

## Options Considered
- Redis plus Celery for durable background jobs.
- In-memory queues inside the web application.
- A lightweight custom queue embedded in the API process.

## Chosen Approach
Use Redis as the task broker and Celery for background task execution.

## Consequences
- Jobs persist across process restarts and can be retried safely.
- The API stays responsive because heavy work is offloaded.
- Operational overhead increases because Redis and worker processes must be monitored.
- The design supports scaling workers independently from the API tier.
