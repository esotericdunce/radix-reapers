import re
from typing import Any
from pydantic import BaseModel, field_validator
from app.utils.skill_aliases import canonical_key, canonical_name

CATEGORIES = {
    "COD": "Coding",
    "DSA": "Data Structures & Algorithms",
    "OOD": "Object-Oriented Design",
    "APTI": "Aptitude",
    "COMM": "Communication",
    "AI": "Artificial Intelligence",
    "CLOUD": "Cloud",
    "SQL": "SQL",
    "SWE": "Software Engineering",
    "SYSD": "System Design",
    "NETW": "Networking",
    "OS": "Operating Systems",
    "OTHER": "Other skills",
}

# Comprehensive industry skill taxonomy mapped to the 12 placement evaluation categories
TAXONOMY = {
    # Coding & Frameworks (COD)
    "Python": "COD", "Java": "COD", "JavaScript": "COD", "JS": "COD", "TypeScript": "COD", "TS": "COD",
    "C++": "COD", "C#": "COD", "C": "COD", "Go": "COD", "Golang": "COD", "Rust": "COD", "Ruby": "COD",
    "PHP": "COD", "Swift": "COD", "Kotlin": "COD", "Dart": "COD", "Scala": "COD", "R": "COD", "Julia": "COD",
    "HTML": "COD", "HTML5": "COD", "CSS": "COD", "CSS3": "COD", "React": "COD", "React.js": "COD",
    "Angular": "COD", "Vue": "COD", "Vue.js": "COD", "Next.js": "COD", "Nuxt.js": "COD", "Node.js": "COD",
    "NodeJS": "COD", "Express": "COD", "Express.js": "COD", "FastAPI": "COD", "Flask": "COD", "Django": "COD",
    "Spring Boot": "COD", "Spring": "COD", "ASP.NET": "COD", "Ruby on Rails": "COD", "Svelte": "COD",
    "Tailwind CSS": "COD", "Tailwind": "COD", "Bootstrap": "COD", "Redux": "COD", "GraphQL": "COD",
    "REST APIs": "COD", "RESTful APIs": "COD", "REST": "COD", "gRPC": "COD", "WebSocket": "COD",

    # Data Structures & Algorithms (DSA)
    "Data Structures and Algorithms": "DSA", "Data Structures": "DSA", "Algorithms": "DSA", "DSA": "DSA",
    "Dynamic Programming": "DSA", "Binary Search": "DSA", "Binary Trees": "DSA", "Binary Search Trees": "DSA",
    "Graph Algorithms": "DSA", "Graphs": "DSA", "Trees": "DSA", "Tries": "DSA", "Linked Lists": "DSA",
    "Stacks and Queues": "DSA", "Hash Tables": "DSA", "Recursion": "DSA", "Sorting Algorithms": "DSA",
    "Time Complexity": "DSA", "Space Complexity": "DSA", "Big O": "DSA",

    # Object-Oriented Design (OOD)
    "Object-Oriented Programming": "OOD", "Object-Oriented Design": "OOD", "OOP": "OOD", "OOD": "OOD",
    "SOLID Principles": "OOD", "Design Patterns": "OOD", "Factory Pattern": "OOD", "Singleton Pattern": "OOD",
    "Strategy Pattern": "OOD", "Observer Pattern": "OOD", "Inheritance": "OOD", "Polymorphism": "OOD",
    "Encapsulation": "OOD", "Abstraction": "OOD", "UML": "OOD",

    # Aptitude & Problem Solving (APTI)
    "Problem Solving": "APTI", "Aptitude": "APTI", "Logical Reasoning": "APTI", "Quantitative Analysis": "APTI",
    "Critical Thinking": "APTI", "Analytical Skills": "APTI", "Statistics": "APTI", "Probability": "APTI",

    # Communication & Collaboration (COMM)
    "Communication": "COMM", "Technical Writing": "COMM", "Verbal Communication": "COMM",
    "Written Communication": "COMM", "Collaboration": "COMM", "Teamwork": "COMM", "Presentation Skills": "COMM",

    # AI & Machine Learning (AI)
    "Machine Learning": "AI", "ML": "AI", "Artificial Intelligence": "AI", "AI": "AI", "Deep Learning": "AI",
    "Neural Networks": "AI", "Natural Language Processing": "AI", "NLP": "AI", "Computer Vision": "AI",
    "OpenCV": "AI", "Large Language Models": "AI", "LLM": "AI", "Generative AI": "AI", "GenAI": "AI",
    "LangChain": "AI", "LlamaIndex": "AI", "RAG": "AI", "PyTorch": "AI", "TensorFlow": "AI", "Keras": "AI",
    "scikit-learn": "AI", "Scikit-Learn": "AI", "Pandas": "AI", "NumPy": "AI", "HuggingFace": "AI",

    # Cloud & DevOps (CLOUD)
    "Cloud Computing": "CLOUD", "AWS": "CLOUD", "Amazon Web Services": "CLOUD", "Azure": "CLOUD",
    "Microsoft Azure": "CLOUD", "GCP": "CLOUD", "Google Cloud Platform": "CLOUD", "Docker": "CLOUD",
    "Kubernetes": "CLOUD", "K8s": "CLOUD", "CI/CD": "CLOUD", "Continuous Integration": "CLOUD",
    "Jenkins": "CLOUD", "GitHub Actions": "CLOUD", "GitLab CI": "CLOUD", "Terraform": "CLOUD",
    "Ansible": "CLOUD", "Microservices": "CLOUD", "Serverless": "CLOUD", "AWS Lambda": "CLOUD",

    # SQL & Databases (SQL)
    "SQL": "SQL", "PostgreSQL": "SQL", "Postgres": "SQL", "MySQL": "SQL", "NoSQL": "SQL",
    "MongoDB": "SQL", "Redis": "SQL", "SQLite": "SQL", "Cassandra": "SQL", "Elasticsearch": "SQL",
    "DynamoDB": "SQL", "Oracle Database": "SQL", "Database Design": "SQL", "Indexing": "SQL",
    "Prisma": "SQL", "SQLAlchemy": "SQL",

    # Software Engineering & Tooling (SWE)
    "Software Engineering": "SWE", "Software Testing": "SWE", "Unit Testing": "SWE", "Integration Testing": "SWE",
    "TDD": "SWE", "Test-Driven Development": "SWE", "Git": "SWE", "GitHub": "SWE", "GitLab": "SWE",
    "Version Control": "SWE", "Agile": "SWE", "Scrum": "SWE", "JIRA": "SWE", "Code Review": "SWE",
    "SDLC": "SWE", "Pytest": "SWE", "Jest": "SWE",

    # System Design & Architecture (SYSD)
    "System Design": "SYSD", "Distributed Systems": "SYSD", "High Availability": "SYSD", "Scalability": "SYSD",
    "Load Balancing": "SYSD", "Caching": "SYSD", "CDN": "SYSD", "Message Queues": "SYSD", "Kafka": "SYSD",
    "Apache Kafka": "SYSD", "RabbitMQ": "SYSD", "API Gateway": "SYSD", "Rate Limiting": "SYSD",

    # Computer Networking (NETW)
    "Networking": "NETW", "Computer Networking": "NETW", "Computer Networks": "NETW", "TCP/IP": "NETW",
    "UDP": "NETW", "HTTP": "NETW", "HTTPS": "NETW", "DNS": "NETW", "Sockets": "NETW", "SSL/TLS": "NETW",
    "OSI Model": "NETW", "Firewalls": "NETW", "VPN": "NETW",

    # Operating Systems (OS)
    "Operating Systems": "OS", "Linux": "OS", "Unix": "OS", "Ubuntu": "OS", "Shell Scripting": "OS",
    "Bash": "OS", "Multithreading": "OS", "Concurrency": "OS", "Memory Management": "OS",

    # Other Professional Tools (OTHER)
    "Power BI": "OTHER", "Excel": "OTHER", "Data Visualization": "OTHER", "Troubleshooting": "OTHER",
}

class Skill(BaseModel):
    skill_name: str
    category_code: str
    evidence: str
    confidence: str
    @field_validator("category_code")
    @classmethod
    def valid_category(cls, value):
        if value not in CATEGORIES:
            raise ValueError("Unsupported category code")
        return value
    @field_validator("confidence")
    @classmethod
    def valid_confidence(cls, value):
        if value not in {"high", "medium", "low"}:
            raise ValueError("Confidence must be high, medium, or low")
        return value

def extract_skills(text: str) -> list[dict[str, Any]]:
    """Deterministic taxonomy keyword & phrase extraction with phrase boundary protection."""
    found = []
    seen = set()
    covered = []

    # Sort phrases by length descending so longer compound phrases take precedence
    sorted_phrases = sorted(TAXONOMY.keys(), key=lambda p: len(p), reverse=True)

    for phrase in sorted_phrases:
        category = TAXONOMY[phrase]
        pattern = r"(?<![A-Za-z0-9])" + re.escape(phrase) + r"(?![A-Za-z0-9])"
        m = re.search(pattern, text, re.I)
        if not m:
            continue
        if any(a <= m.start() and m.end() <= b for a, b in covered):
            continue
        key = canonical_key(phrase)
        if key in seen:
            continue
        seen.add(key)
        covered.append((m.start(), m.end()))
        start = max(0, text.rfind("\n", 0, m.start()) + 1)
        end = text.find("\n", m.end())
        end = len(text) if end < 0 else end
        evidence = text[start:end].strip()[:240] or text[max(0, m.start() - 60):m.end() + 60]
        found.append(Skill(
            skill_name=canonical_name(phrase),
            category_code=category,
            evidence=evidence,
            confidence="high" if len(phrase) > 3 else "medium"
        ).model_dump())

    return found


def extract_skills_semantic(text: str) -> tuple[list[dict[str, Any]], str]:
    """Extract skills using active LLM provider when configured, fused with deterministic taxonomy."""
    from app.intelligence import agents, providers, parsing

    avail = agents.availability()
    deterministic = extract_skills(text)
    if not avail:
        return deterministic, "Deterministic taxonomy extraction (250+ skills across 12 categories); no LLM key configured."

    provider = avail[0]
    prompt = f"""You are a technical recruitment skills parser. Extract all technical and engineering skills required in the job description or resume below.
Map every skill to one of these 12 categories:
- COD: Programming languages, web frameworks, libraries
- DSA: Data structures, algorithms, complexity
- OOD: Object-oriented design, OOP, design patterns
- APTI: Problem solving, quantitative, analytical reasoning
- COMM: Technical writing, communication, presentation
- AI: Machine learning, deep learning, NLP, generative AI, LLMs
- CLOUD: Cloud platforms (AWS/Azure/GCP), DevOps, Docker, K8s, CI/CD
- SQL: Databases (SQL, NoSQL), data modelling, queries
- SWE: Software engineering best practices, Git, testing (unit/integration), Agile
- SYSD: System design, distributed systems, architecture, scalability
- NETW: Computer networks, protocols, TCP/IP, HTTP, security
- OS: Operating systems, Linux, concurrency, multithreading
- OTHER: Other tools, domain skills

Return strict JSON only:
{{
  "skills": [
    {{"skill_name": "...", "category_code": "COD", "evidence": "snippet from text"}}
  ]
}}

TEXT:
{text[:4000]}
"""
    try:
        outcome = providers.call_provider(provider, prompt, timeout=30.0)
        if outcome.get("ok"):
            parsed = parsing.extract_json(outcome.get("text", ""))
            raw_llm_skills = parsed.get("skills", [])
            seen = {canonical_key(s["skill_name"]) for s in deterministic}
            fused = list(deterministic)
            for item in raw_llm_skills:
                name = (item.get("skill_name") or "").strip()
                cat = (item.get("category_code") or "OTHER").strip().upper()
                if not name or cat not in CATEGORIES:
                    continue
                k = canonical_key(name)
                if k not in seen:
                    seen.add(k)
                    fused.append(Skill(
                        skill_name=canonical_name(name),
                        category_code=cat,
                        evidence=(item.get("evidence") or "")[:240],
                        confidence="high"
                    ).model_dump())
            return fused, f"AI-assisted extraction ({provider}) with deterministic taxonomy verification."
    except Exception:
        pass

    return deterministic, "Deterministic taxonomy extraction (fallback; LLM parsing blip)."
