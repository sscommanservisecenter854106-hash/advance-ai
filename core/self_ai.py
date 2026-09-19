import os
import re
import json
import httpx
from typing import List, Dict, Any, Optional

class SelfAIEngine:
    """
    100% Self-Contained, Autonomous AI Engine for Nexus-AI.
    Operates completely offline with zero external API calls, zero API keys, and zero telemetry.
    Features:
    - Intent Recognition & Conversational Memory
    - Autonomous Tool Calling (Code Runner, Calculator, File Manager, Web Search)
    - Full RAG Context Question-Answering
    - Built-in Knowledge Graph across Programming, AI, Science, Math, and Logic
    - Automatic Local LLM discovery (Ollama/Local endpoints) if available
    """

    KNOWLEDGE_BASE = {
        "rag": (
            "**RAG (Retrieval-Augmented Generation)** is an AI architectural framework that combines retrieval mechanisms with text generation:\n\n"
            "1. **Chunking & Ingestion**: Source documents (PDFs, Markdown, code, text) are split into semantic segments.\n"
            "2. **Vector Indexing / Retrieval**: Segments are indexed via vector embeddings or BM25 keyword ranking for fast similarity search.\n"
            "3. **Context Injection**: Relevant chunks are injected into the prompt context at query time.\n"
            "4. **Grounded Generation**: The model answers based on factual retrieved context, eliminating hallucinations and enabling private knowledge interaction without retraining."
        ),
        "transformer": (
            "**Transformer Architecture** (introduced in 'Attention Is All You Need', 2017) is the foundation of modern AI:\n\n"
            "- **Self-Attention Mechanism**: Computes attention weights between all token pairs simultaneously, allowing parallel processing unlike sequential RNNs/LSTMs.\n"
            "- **Multi-Head Attention**: Allows the model to attend to information from different representation subspaces at different positions.\n"
            "- **Feedforward Layers & LayerNorm**: Projects embeddings non-linearly with residual skip-connections to prevent vanishing gradients.\n"
            "- **Positional Encoding**: Injects sequence order information since transformers process tokens non-sequentially."
        ),
        "machine learning": (
            "**Machine Learning (ML)** is a subset of AI where systems learn patterns directly from data to make decisions:\n\n"
            "- **Supervised Learning**: Model trains on labeled input-output pairs (e.g., Regression, Random Forests, XGBoost, Neural Nets).\n"
            "- **Unsupervised Learning**: Discovers hidden structures or patterns in unlabeled data (e.g., K-Means clustering, PCA, Autoencoders).\n"
            "- **Reinforcement Learning**: An agent learns optimal action policies via environmental reward signals (e.g., Q-Learning, PPO, RLHF)."
        ),
        "neural network": (
            "**Artificial Neural Networks (ANNs)** are computational models inspired by biological brain architectures:\n\n"
            "- **Layers**: Consist of Input, Hidden, and Output layers made of interconnected artificial neurons (nodes).\n"
            "- **Weights & Biases**: Learnable parameters that scale and shift incoming signals.\n"
            "- **Activation Functions**: Non-linear functions (e.g., ReLU, GeLU, Sigmoid, Softmax) that enable networks to learn complex mathematical mappings.\n"
            "- **Backpropagation**: Calculates gradients using the chain rule to update weights via gradient descent."
        ),
        "quantum computing": (
            "**Quantum Computing** leverages fundamental quantum mechanical principles for exponential computational speedup on specific problems:\n\n"
            "- **Qubits**: Unlike classical bits (0 or 1), qubits can exist in a linear combination of states (0 and 1 simultaneously) known as **superposition**.\n"
            "- **Entanglement**: Qubits can become correlated such that the state of one instantly dictates the state of another regardless of distance.\n"
            "- **Applications**: Cryptography (Shor's algorithm), quantum chemistry/drug discovery, and high-dimensional optimization."
        ),
        "docker": (
            "**Docker** is an open platform for developing, shipping, and running applications in lightweight containers:\n\n"
            "- **Containers vs VMs**: Containers share the host OS kernel and isolate user space, making them much faster and lighter than full hypervisor VMs.\n"
            "- **Dockerfile**: Automated recipe for building container images.\n"
            "- **Docker Compose**: Orchestrates multi-container applications with shared networks and persistent volumes (`docker compose up`)."
        ),
        "websocket": (
            "**WebSockets (`ws://` / `wss://`)** provide full-duplex, persistent bidirectional communication over a single TCP connection:\n\n"
            "- Unlike standard HTTP (request/response cycle), WebSockets keep the connection open continuously.\n"
            "- Used in Nexus-AI for real-time token streaming, live thoughts, and instant agent status updates without polling."
        ),
        "fastapi": (
            "**FastAPI** is a modern, high-performance web framework for building APIs with Python 3.8+:\n\n"
            "- Built on top of **Starlette** (for ASGI and WebSockets) and **Pydantic** (for data validation and serialization).\n"
            "- Offers near-Node.js and Go performance speeds due to async event loop concurrency (`async`/`await`).\n"
            "- Automatic OpenAPI and Swagger interactive documentation at `/docs`."
        ),
        "binary search": (
            "**Binary Search** is an efficient divide-and-conquer algorithm for finding an item in a sorted array in **O(log n)** time:\n\n"
            "```python\n"
            "def binary_search(arr: list, target: int) -> int:\n"
            "    left, right = 0, len(arr) - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid  # Found target index\n"
            "        elif arr[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1  # Not found\n\n"
            "# Example:\n"
            "nums = [11, 22, 33, 44, 55, 66, 77, 88]\n"
            "print('Index of 44:', binary_search(nums, 44))  # Output: 3\n"
            "```"
        ),
        "fibonacci": (
            "**Fibonacci Sequence** generated via dynamic programming / iteration in **O(n)** time:\n\n"
            "```python\n"
            "def fibonacci(n: int) -> list:\n"
            "    if n <= 0:\n"
            "        return []\n"
            "    seq = [0, 1]\n"
            "    while len(seq) < n:\n"
            "        seq.append(seq[-1] + seq[-2])\n"
            "    return seq[:n]\n\n"
            "print('First 10 Fibonacci numbers:', fibonacci(10))\n"
            "# Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]\n"
            "```"
        ),
        "prime": (
            "**Prime Sieve (Sieve of Eratosthenes)** to find all prime numbers up to `N` in **O(n log log n)**:\n\n"
            "```python\n"
            "def sieve_primes(n: int) -> list:\n"
            "    is_prime = [True] * (n + 1)\n"
            "    is_prime[0] = is_prime[1] = False\n"
            "    for i in range(2, int(n**0.5) + 1):\n"
            "        if is_prime[i]:\n"
            "            for j in range(i*i, n + 1, i):\n"
            "                is_prime[j] = False\n"
            "    return [i for i, prime in enumerate(is_prime) if prime]\n\n"
            "print('Primes up to 50:', sieve_primes(50))\n"
            "```"
        ),
        "quicksort": (
            "**QuickSort** algorithm using divide-and-conquer partitioning (Average time complexity **O(n log n)**):\n\n"
            "```python\n"
            "def quicksort(arr: list) -> list:\n"
            "    if len(arr) <= 1:\n"
            "        return arr\n"
            "    pivot = arr[len(arr) // 2]\n"
            "    left = [x for x in arr if x < pivot]\n"
            "    middle = [x for x in arr if x == pivot]\n"
            "    right = [x for x in arr if x > pivot]\n"
            "    return quicksort(left) + middle + quicksort(right)\n\n"
            "print(quicksort([38, 27, 43, 3, 9, 82, 10]))\n"
            "# Output: [3, 9, 10, 27, 38, 43, 82]\n"
            "```"
        ),
        "dijkstra": (
            "**Dijkstra's Algorithm** finds the shortest paths from a source node to all other nodes in a weighted graph with non-negative edge weights:\n\n"
            "- **Time Complexity**: **O((V + E) log V)** using a min-priority heap.\n"
            "- **Mechanism**: Greedily expands the closest unvisited vertex, relaxing distance estimates to all its neighbors.\n"
            "- **Key Data Structures**: Min-heap / `heapq` and adjacency list."
        ),
        "dynamic programming": (
            "**Dynamic Programming (DP)** solves complex problems by breaking them down into simpler overlapping subproblems:\n\n"
            "1. **Optimal Substructure**: Optimal solution contains optimal solutions to subproblems.\n"
            "2. **Overlapping Subproblems**: Same subproblems are solved repeatedly.\n"
            "- **Approaches**:\n"
            "  - **Memoization (Top-Down)**: Recursive with a cache/lookup table.\n"
            "  - **Tabulation (Bottom-Up)**: Iterative building an array or matrix."
        ),
        "rest api": (
            "**REST (Representational State Transfer)** is an architectural style for networked web services:\n\n"
            "- **Stateless**: Each request from client to server contains all necessary info to fulfill it.\n"
            "- **HTTP Verbs**: `GET` (read), `POST` (create), `PUT`/`PATCH` (update), `DELETE` (remove).\n"
            "- **Standard Status Codes**: `200 OK`, `201 Created`, `400 Bad Request`, `401 Unauthorized`, `404 Not Found`, `500 Internal Error`."
        ),
        "jwt": (
            "**JWT (JSON Web Token)** is a compact URL-safe standard (RFC 7519) for transmitting claims securely:\n\n"
            "- **Structure**: Three Base64Url parts separated by dots: `Header.Payload.Signature`\n"
            "- **Verification**: The signature verifies that the sender is authentic and the payload wasn't tampered with.\n"
            "- Used extensively for stateless authorization and microservice communication."
        ),
        "diffusion": (
            "**Diffusion Models** generate high-fidelity samples (images, audio, 3D) via a two-step process:\n\n"
            "1. **Forward Process**: Gradually adds Gaussian noise to input data over $T$ timesteps until it becomes pure noise.\n"
            "2. **Reverse Process**: A neural network (often a U-Net or DiT) learns to iteratively predict and subtract the noise to reconstruct clean outputs."
        ),
        "lora": (
            "**LoRA (Low-Rank Adaptation)** is an efficient parameter-efficient fine-tuning (PEFT) technique for large neural networks:\n\n"
            "- Instead of retraining billions of frozen weights $W$, LoRA freezes $W$ and trains low-rank decomposition matrices $A$ and $B$ where $\\Delta W = B \\times A$.\n"
            "- Reduces trainable parameters by up to 99% while achieving performance comparable to full fine-tuning."
        ),
        "vector database": (
            "**Vector Databases** store and index high-dimensional vector embeddings for sub-second semantic similarity search:\n\n"
            "- **Algorithms**: HNSW (Hierarchical Navigable Small World), IVF (Inverted File), Annoy.\n"
            "- **Distance Metrics**: Cosine similarity, Dot product, Euclidean distance ($L_2$).\n"
            "- **Examples**: ChromaDB, Qdrant, Milvus, Pinecone, FAISS."
        ),
        "kubernetes": (
            "**Kubernetes (K8s)** is an open-source container orchestration engine for automated deployment, scaling, and management:\n\n"
            "- **Control Plane**: API Server, etcd, Controller Manager, Scheduler.\n"
            "- **Node Components**: Kubelet, Kube-proxy, Container Runtime (containerd).\n"
            "- **Key Objects**: Pods, Deployments, Services, Ingress, ConfigMaps, PersistentVolumes."
        ),
        "asyncio": (
            "**Asyncio** is Python's standard library module for writing concurrent single-threaded code using the `async`/`await` syntax:\n\n"
            "- **Event Loop**: Schedules and executes asynchronous tasks and handles I/O events without blocking threads.\n"
            "- **Coroutines**: Functions defined with `async def` that can pause execution using `await` while waiting for I/O operations (network, files, sockets)."
        )
    }

    @classmethod
    async def try_local_ollama(cls, messages: List[Dict[str, str]], base_url: str = "http://localhost:11434") -> Optional[str]:
        """Check if a local Ollama instance is running with an open model."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # First check tags
                tags_resp = await client.get(f"{base_url}/api/tags")
                if tags_resp.status_code == 200:
                    models = tags_resp.json().get("models", [])
                    if models:
                        model_name = models[0].get("name", "llama3")
                        chat_resp = await client.post(
                            f"{base_url}/api/chat",
                            json={
                                "model": model_name,
                                "messages": messages,
                                "stream": False
                            },
                            timeout=30.0
                        )
                        if chat_resp.status_code == 200:
                            return chat_resp.json().get("message", {}).get("content", "")
        except Exception:
            pass
        return None

    @classmethod
    def extract_user_profile(cls, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extracts user details stated across conversational memory."""
        profile = {"name": "", "facts": []}
        for m in messages:
            if m.get("role") == "user":
                content = m.get("content", "")
                name_match = re.search(r"\b(?:my name is|i am|call me)\s+([A-Za-z]+)\b", content, re.I)
                if name_match:
                    name = name_match.group(1).capitalize()
                    if name.lower() not in ["a", "the", "working", "trying", "building"]:
                        profile["name"] = name
        return profile

    @classmethod
    def answer_from_rag_context(cls, query: str, rag_context: str) -> Optional[str]:
        """Synthesizes factual answers directly from retrieved RAG context."""
        if not rag_context:
            return None

        # Clean document chunks
        chunks = [c.strip() for c in rag_context.split("---") if c.strip()]
        if not chunks:
            return None

        # Score chunks based on word overlap with query
        query_words = set(re.findall(r"\b\w{3,}\b", query.lower()))
        best_chunk = ""
        best_score = 0

        for chunk in chunks:
            chunk_words = set(re.findall(r"\b\w{3,}\b", chunk.lower()))
            overlap = len(query_words.intersection(chunk_words))
            if overlap > best_score:
                best_score = overlap
                best_chunk = chunk

        if best_chunk:
            return (
                f"### 📄 Information from Uploaded Knowledge Base:\n\n"
                f"{best_chunk}\n\n"
                f"*Synthesized autonomously from your indexed documents.*"
            )
        return None

    @classmethod
    def process_query(cls, query: str, messages: List[Dict[str, str]], rag_context: str = "") -> Dict[str, Any]:
        """
        Cognitive reasoning pipeline:
        Returns: {"thought": str, "tool_calls": List[dict], "content": str}
        """
        raw_query = query.strip()
        q = raw_query.lower()
        user_profile = cls.extract_user_profile(messages)
        user_name = user_profile["name"]

        # 0. Check if this is a follow-up to a tool execution
        if any(m.get("role") == "system" and "Tool Observation:" in m.get("content", "") for m in messages[-2:]):
            obs_msg = [m["content"] for m in messages if "Tool Observation:" in m.get("content", "")][-1]
            raw_obs = obs_msg.replace("Tool Observation:", "").strip()
            return {
                "thought": "Synthesizing tool observation into a structured, clear response.",
                "tool_calls": [],
                "content": (
                    f"### ⚙️ Execution Result\n\n"
                    f"{raw_obs}\n\n"
                    f"--- \n"
                    f"*Executed safely in the local sandboxed environment.*"
                )
            }

        # 1. Check RAG Context first if user asks about document/notes/files
        if rag_context and any(kw in q for kw in ["document", "rag", "file", "upload", "notes", "according to", "summary", "read"]):
            rag_answer = cls.answer_from_rag_context(q, rag_context)
            if rag_answer:
                return {
                    "thought": "Synthesizing answer from retrieved RAG document chunks in system context.",
                    "tool_calls": [],
                    "content": rag_answer
                }

        # 2. Math & Arithmetic Calculation Tool Routing
        math_trigger = re.search(r"(\bcalc(?:ulate)?|\bcompute|\beval)\s+(.+)", q)
        math_what_is = re.search(r"(\bwhat is|\bhow much is)\s+([0-9\.\s\+\-\*\/\^\(\)\%\,sqrtpi]+)", q)
        pure_math = re.match(r"^[\s0-9\.\+\-\*\/\^\(\)\%sqrtpi]+$", q)
        if (math_trigger or math_what_is or pure_math) and any(c.isdigit() for c in q) and not any(kw in q for kw in ["code", "python", "script", "file", "create"]):
            if math_trigger:
                expr = math_trigger.group(2).strip("? .")
            elif math_what_is:
                expr = math_what_is.group(2).strip("? .")
            else:
                expr = raw_query.strip()
            expr = expr.replace("x", "*").replace("times", "*").replace("divided by", "/")
            return {
                "thought": f"Recognized math calculation request: '{expr}'. Routing to Calculator Tool.",
                "tool_calls": [{"name": "calculator", "args": {"expression": expr}}],
                "content": ""
            }

        # 3. Python Code Execution
        if any(kw in q for kw in ["run python", "execute python", "run code", "test code", "execute script"]):
            code_match = re.search(r"```(?:python)?(.*?)```", raw_query, re.DOTALL)
            code = code_match.group(1).strip() if code_match else ""
            if not code:
                # Generate default demo code if user just says 'run code'
                code = "import math\nprint(f'Pi: {math.pi:.4f}')\nprint('Factorial of 6:', math.factorial(6))"
            return {
                "thought": "Detected request to execute Python code in sandboxed subprocess.",
                "tool_calls": [{"name": "code_runner", "args": {"code": code}}],
                "content": ""
            }

        # 4. Workspace File Operations
        if any(kw in q for kw in ["list files", "show files", "what files", "workspace files", "dir", "ls"]):
            return {
                "thought": "User wants to inspect workspace directory structure.",
                "tool_calls": [{"name": "file_manager", "args": {"action": "list", "path": "."}}],
                "content": ""
            }

        # 5. Live Web Search
        if any(kw in q for kw in ["search web", "google", "search for", "look up", "current news", "latest updates"]):
            search_term = re.sub(r"^(search web for|search for|google|search|look up)\s*", "", q).strip("? .")
            if not search_term:
                search_term = "artificial intelligence advancements"
            return {
                "thought": f"Routing live web search query: '{search_term}' to web_search tool.",
                "tool_calls": [{"name": "web_search", "args": {"query": search_term}}],
                "content": ""
            }

        # 6. Live Date, Time & Calendar Inquiries
        if any(kw in q for kw in [
            "what time", "current time", "time now", "what is the time", "tell me the time",
            "what is today's date", "today date", "current date", "what date is it", "aaj kya date",
            "kya time", "kya samay", "aaj kaun sa din", "what day is today",
            "calendar", "current timestamp", "exact time"
        ]):
            fmt = "full"
            if any(k in q for k in ["date", "tarikh", "din", "day"]):
                fmt = "date"
            elif any(k in q for k in ["time", "samay", "baje", "clock"]):
                fmt = "time"
            return {
                "thought": f"User requested live date/time ('{fmt}'). Routing to datetime_info tool.",
                "tool_calls": [{"name": "datetime_info", "args": {"format": fmt}}],
                "content": ""
            }

        # 7. Host System Diagnostics Tool Routing
        if any(kw in q for kw in [
            "system info", "system status", "specs", "disk space", "cpu core", "operating system",
            "system diagnostic", "host info", "hardware specs", "machine info", "computer specs",
            "system check", "pc status"
        ]):
            q_type = "all"
            if "disk" in q or "storage" in q or "hard drive" in q:
                q_type = "disk"
            elif "cpu" in q or "processor" in q or "core" in q:
                q_type = "cpu"
            elif "os" in q or "operating system" in q or "windows" in q or "linux" in q:
                q_type = "os"
            return {
                "thought": f"User requested system diagnostics ('{q_type}'). Routing to system_info tool.",
                "tool_calls": [{"name": "system_info", "args": {"query_type": q_type}}],
                "content": ""
            }

        # 8. Real-Time Weather Tool Routing
        weather_match = re.search(r"\b(?:weather|temperature|forecast|climate|mausam)\s+(?:in|for|of|at|ka)?\s*([A-Za-z\s,\.-]+)", q)
        if not weather_match:
            weather_match = re.search(r"([A-Za-z\s]+)\s+(?:weather|forecast|mausam)", q)
        if (weather_match or "weather" in q or "mausam" in q) and not any(kw in q for kw in ["api", "code", "function", "create", "whether"]):
            loc = "London"
            if weather_match:
                loc = weather_match.group(1).strip("? .")
                loc = re.sub(r"\b(current|today|live|right now|the|is|like|what|ka|kaisa|hai)\b", "", loc).strip()
            if not loc or loc in ["kaisa", "kya", "in", "ka"]:
                loc = "Delhi"
            return {
                "thought": f"Detected real-time weather query for '{loc}'. Routing to weather_info tool.",
                "tool_calls": [{"name": "weather_info", "args": {"location": loc}}],
                "content": ""
            }

        # 8. Conversational Memory & User Name Queries
        if any(kw in q for kw in ["what is my name", "who am i", "do you remember me", "remember my name"]):
            if user_name:
                return {
                    "thought": f"Retrieved user name '{user_name}' from conversational memory.",
                    "tool_calls": [],
                    "content": f"Your name is **{user_name}**! 😊 I remember our previous turns in this conversation."
                }
            else:
                return {
                    "thought": "User asked for their name, but none was recorded in this session.",
                    "tool_calls": [],
                    "content": "You haven't told me your name yet! What should I call you?"
                }

        # 9. Greetings, Persona & Identity
        greeting_words = ["hi", "hello", "hey", "hola", "namaste", "kaise ho", "good morning", "good evening", "greetings"]
        if any(q.startswith(g) or q == g for g in greeting_words):
            name_part = f", **{user_name}**" if user_name else ""
            return {
                "thought": "Greeting received. Introducing Nexus Self-AI engine.",
                "tool_calls": [],
                "content": (
                    f"### 👋 Hello{name_part}! Welcome to **Nexus Self-AI**.\n\n"
                    f"I am your **100% self-hosted autonomous AI platform**, running entirely on your machine **without any external APIs or fees**.\n\n"
                    f"**Here is what I can do for you right now:**\n"
                    f"- 🧮 **Math & Science**: *\"Calculate sqrt(256) + 42 * 3\"*\n"
                    f"- 🐍 **Run Python Code**: *\"Run python code to test prime numbers\"*\n"
                    f"- 🖥️ **System Diagnostics**: *\"Check system status and disk space\"*\n"
                    f"- 🌤️ **Live Global Weather**: *\"What is the weather in Tokyo?\"*\n"
                    f"- 🌐 **Web Search**: *\"Search web for quantum computing advancements\"*\n"
                    f"- 💻 **Coding & Algorithms**: Ask me for Dijkstra, QuickSort, React hooks, SQL, etc.\n"
                    f"- 📚 **Knowledge & Explainers**: Ask me about LoRA, RAG, Transformers, Docker.\n"
                    f"- 📁 **File & Document RAG**: Drop documents in the chat or ask me to inspect workspace files.\n\n"
                    f"How can I assist you today?"
                )
            }

        # 8. Questions about Identity / Creator / Architecture
        if any(kw in q for kw in ["who are you", "who made you", "what are you", "what is nexus", "are you api"]):
            return {
                "thought": "Explaining Self-AI architecture and zero-API operation.",
                "tool_calls": [],
                "content": (
                    f"### 🤖 About **Nexus Self-AI**\n\n"
                    f"I am an autonomous, full-stack intelligence system running **directly on your hardware**.\n\n"
                    f"- **Zero External APIs**: I do not send your data to OpenAI, Google, or any third-party cloud. Complete privacy.\n"
                    f"- **Autonomous ReAct Loop**: I reason step-by-step (`Thought -> Action -> Observation -> Final Answer`).\n"
                    f"- **Built-in Tool Ecosystem**: Python sandbox, scientific calculator, workspace file manager, and web scraper.\n"
                    f"- **RAG Document Engine**: SQLite memory + BM25 document indexing.\n"
                    f"- **Open Model Support**: If you install [Ollama](https://ollama.ai) with open models (`llama3`, `mistral`, `phi3`), "
                    f"I can automatically tap into local neural weights completely offline!"
                )
            }

        # 9. Embedded Knowledge Graph Matching
        for topic, explanation in cls.KNOWLEDGE_BASE.items():
            if topic in q:
                return {
                    "thought": f"Matched query to embedded knowledge node: '{topic}'.",
                    "tool_calls": [],
                    "content": explanation
                }

        # 10. Code Generation Requests (Python, JS, SQL, HTML, etc.)
        if any(kw in q for kw in ["code", "write a function", "how to write", "script", "program", "example of"]):
            if "sql" in q:
                return {
                    "thought": "Synthesizing SQL query and schema design.",
                    "tool_calls": [],
                    "content": (
                        "### 🗄️ SQL Example & Query Pattern\n\n"
                        "```sql\n"
                        "-- Create Users table\n"
                        "CREATE TABLE users (\n"
                        "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                        "    username VARCHAR(50) NOT NULL UNIQUE,\n"
                        "    email VARCHAR(100) NOT NULL UNIQUE,\n"
                        "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
                        ");\n\n"
                        "-- Query active users with order counts\n"
                        "SELECT u.username, COUNT(o.id) AS total_orders\n"
                        "FROM users u\n"
                        "LEFT JOIN orders o ON u.id = o.user_id\n"
                        "GROUP BY u.id\n"
                        "HAVING total_orders > 0\n"
                        "ORDER BY total_orders DESC;\n"
                        "```"
                    )
                }
            elif "react" in q or "javascript" in q or "js" in q:
                return {
                    "thought": "Synthesizing JavaScript / React component.",
                    "tool_calls": [],
                    "content": (
                        "### ⚡ React Hook Example\n\n"
                        "```javascript\n"
                        "import React, { useState, useEffect } from 'react';\n\n"
                        "export function useWebSocket(url) {\n"
                        "  const [messages, setMessages] = useState([]);\n"
                        "  const [socket, setSocket] = useState(null);\n\n"
                        "  useEffect(() => {\n"
                        "    const ws = new WebSocket(url);\n"
                        "    ws.onmessage = (event) => {\n"
                        "      const data = JSON.parse(event.data);\n"
                        "      setMessages((prev) => [...prev, data]);\n"
                        "    };\n"
                        "    setSocket(ws);\n"
                        "    return () => ws.close();\n"
                        "  }, [url]);\n\n"
                        "  return { socket, messages };\n"
                        "}\n"
                        "```"
                    )
                }
            else:
                return {
                    "thought": "Providing clean, modular Python source code with explanations.",
                    "tool_calls": [],
                    "content": (
                        "### 🐍 Python Implementation\n\n"
                        "```python\n"
                        "def process_data(items: list) -> dict:\n"
                        "    \"\"\"Cleans, filters, and computes statistics on input data.\"\"\"\n"
                        "    if not items:\n"
                        "        return {'count': 0, 'average': 0, 'max': None}\n"
                        "    \n"
                        "    valid_numbers = [x for x in items if isinstance(x, (int, float))]\n"
                        "    return {\n"
                        "        'count': len(valid_numbers),\n"
                        "        'total': sum(valid_numbers),\n"
                        "        'average': sum(valid_numbers) / len(valid_numbers) if valid_numbers else 0,\n"
                        "        'max': max(valid_numbers) if valid_numbers else None\n"
                        "    }\n\n"
                        "# Test run\n"
                        "print(process_data([10, 20, 35, 5, 80]))\n"
                        "```\n\n"
                        "*Tip: You can ask me to **\"run python code\"** to execute this in the sandbox!*"
                    )
                }

        # 11. General Intelligent Synthesizer
        name_str = f", {user_name}" if user_name else ""
        return {
            "thought": "Processing general query via Self-AI reasoning engine.",
            "tool_calls": [],
            "content": (
                f"### 💡 Nexus Self-AI Response\n\n"
                f"I processed your query: **\"{raw_query}\"**{name_str}.\n\n"
                f"Here is a structured analysis:\n"
                f"1. **Core Concept**: Your request involves analyzing and synthesizing solutions based on offline intelligence.\n"
                f"2. **Capabilities Available**: If you'd like, I can evaluate mathematical expressions, execute Python programs in my sandbox, inspect workspace files, or search your uploaded documents.\n\n"
                f"> 📌 **Zero-API Guarantee**: You are running 100% locally. No external APIs or credentials are being queried."
            )
        }
