# NexusMesh-AI: Distributed Multi-Agent Orchestration

NexusMesh is a production-grade, distributed AI framework designed for complex, non-linear task execution. It leverages a hybrid-edge architecture, offloading heavy computation and inference to an in-house server while maintaining a lightweight control plane on the local client.

## 🚀 Key Architectural Pillars
- **Agentic Reasoning:** Powered by Python and LangGraph for stateful multi-agent coordination.
- **Distributed Nervous System:** Task distribution handled via **RabbitMQ** for resilient, asynchronous processing.
- **High-Performance Workers:** Specialized **C#/.NET 9** workers for data-intensive operations and **Python** workers for LLM inference.
- **Semantic Memory:** Integrated with **Milvus Vector DB** and **PostgreSQL (pgvector)** for long-term context retention.

## 🛠 Tech Stack
- **Orchestration:** Python (LangGraph, Pydantic)
- **Messaging:** RabbitMQ
- **Backend Infrastructure:** C# (.NET Core), Celery
- **Database:** Milvus, Redis, PostgreSQL
- **Deployment:** Docker, Nginx

## 🏗 Setup
1. Copy `.env.example` to `.env` and fill in your server credentials.
2. Run infrastructure: `docker-compose up -d`
3. Start the Orchestrator: `python orchestrator/main.py`
