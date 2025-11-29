import os
import re
import sqlite3
import traceback
import chromadb
from chromadb.config import Settings
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

# Disable OpenTelemetry errors
os.environ['OTEL_SDK_DISABLED'] = 'true'

# -------------------------
# API KEY CONFIG
# -------------------------
# -------------------------
# API KEY CONFIG (HARDCODED - ONLY FOR TESTING)
# -------------------------
#api_key = "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"

if not api_key or not api_key.startswith("sk-"):
    raise ValueError("❌ Invalid API key format. Check your key.")

# -------------------------
# LLM INITIALIZER
# -------------------------
def llm_initializer(api_key):
    try:
        return LLM(model="gpt-4o", api_key=api_key)
    except Exception as e:
        raise RuntimeError("LLM init failed: " + str(e))

llm = llm_initializer(api_key)

# -------------------------
# POLICY TOOL
# -------------------------
@tool("Policy Fetch Tool")
def policy_tool(policy_query: str) -> str:
    """
    Fetch HR policy information from the vector database based on user query.
    """
    try:
        client = chromadb.Client(
            Settings(persist_directory="chroma_db", anonymized_telemetry=False)
        )
        collection = client.get_collection(name="hr_policies")

        result = collection.query(query_texts=[policy_query], n_results=3)
        documents = result.get("documents", [])

        if not documents or not documents[0]:
            return f"❌ No policy information found for: {policy_query}"

        response = "✅ HR Policy Results:\n\n"
        for i, doc in enumerate(documents[0], 1):
            response += f"{i}. {doc}\n\n"

        return response.strip()

    except Exception as e:
        return f"⚠️ Error fetching policy: {str(e)}"

# -------------------------
# RESUME TOOL
# -------------------------
@tool("Resume Analyzer Tool")
def resume_analyzer_tool(resume_text: str) -> str:
    """
    Analyze resume content and extract structured information.
    """
    try:
        patterns = {
            "Email": r"[\w\.-]+@[\w\.-]+",
            "Phone": r"\+?\d[\d -]{7,}\d",
            "Skills": r"Skills?:\s*(.+)"
        }

        extracted = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, resume_text, re.I)
            if match:
                extracted[key] = match.group()

        if not extracted:
            return "❌ No structured data found."

        return "\n".join([f"{k}: {v}" for k, v in extracted.items()])

    except Exception as e:
        return "⚠️ Resume parsing failed"

# -------------------------
# INTERVIEW TOOL
# -------------------------
@tool("Interview Question Generator Tool")
def interview_question_generator_tool(job_description: str) -> str:
    """
    Generate interview questions based on job description.
    """
    try:
        prompt = f"Generate interview questions for this job:\n{job_description}"
        return llm.invoke(prompt)
    except:
        return "⚠️ Failed to generate interview questions."

# -------------------------
# ONBOARDING TOOL
# -------------------------
@tool("Onboarding Tracker Tool")
def onboarding_tracker_tool(employee_name: str, task: str, status: str) -> str:
    """
    Store onboarding tasks and status for employees.
    """
    try:
        client = chromadb.Client(
            Settings(persist_directory="chroma_db", anonymized_telemetry=False)
        )
        col = client.get_or_create_collection(name="onboarding_tasks")

        doc = f"{employee_name} | {task} | {status}"
        uid = f"{employee_name}_{task}".lower().replace(" ", "_")

        col.add(documents=[doc], metadatas=[{"status": status}], ids=[uid])
        return f"✅ Stored: {employee_name} - {task} ({status})"
    except Exception as e:
        return "⚠️ Could not store onboarding record"

# -------------------------
# AGENTS
# -------------------------
Policy_agent = Agent(
    role="Policy Assistant",
    goal="Resolve HR policy questions",
    backstory="You respond ONLY about HR policies.",
    tools=[policy_tool],
    verbose=True,
    allow_delegation=False,
    llm=llm
)

Resume_agent = Agent(
    role="Resume Analyzer",
    goal="Extract resume information",
    backstory="Parse resumes and return structured info.",
    tools=[resume_analyzer_tool],
    verbose=True,
    allow_delegation=False,
    llm=llm
)

Interview_agent = Agent(
    role="Interview Agent",
    goal="Generate interview questions",
    backstory="Provide technical and HR interview questions.",
    tools=[interview_question_generator_tool],
    verbose=True,
    allow_delegation=False,
    llm=llm
)

Onboarding_agent = Agent(
    role="Onboarding Tracker",
    goal="Track onboarding tasks",
    backstory="Store onboarding tasks and updates.",
    tools=[onboarding_tracker_tool],
    verbose=True,
    allow_delegation=False,
    llm=llm
)

manager_agent = Agent(
    role="Manager Agent",
    goal="Route user query to the correct agent and ensure task execution",
    backstory="""
You are a strict routing controller.

You MUST:
1. Understand user intent
2. Select exactly ONE agent
3. Assign task clearly
4. Ensure that agent returns a response
5. If query mentions:
   • leave / HR / policy -> Policy Assistant
   • resume -> Resume Analyzer
   • interview -> Interview Agent
   • onboarding / join -> Onboarding Tracker
6. You must NEVER return empty result.
""",
    verbose=True,
    allow_delegation=True,
    llm=llm,
)


# -------------------------
# MAIN LOOP
# -------------------------
while True:
    query = input("\nEnter HR query (or 'exit'): ").strip()
    if query.lower() == "exit":
        break

    if not query:
        print("❌ Enter something valid.")
        continue

    task = Task(
    description=f"""
User Query: {query}

YOU MUST:
- Identify which agent is required.
- Assign the task to that agent.
- Ensure the tool is called if needed.
- Return a final user-friendly HR response.
""",
    expected_output="A complete and accurate HR answer based on the user query."
)

    crew = Crew(
        agents=[Policy_agent, Resume_agent, Interview_agent, Onboarding_agent],
        manager_agent=manager_agent,
        task=task,
        process=Process.hierarchical,
        verbose=True
    )

    try:
        result = crew.kickoff()
        print("\n✅ FINAL ANSWER:\n", result)

    except Exception as e:
        print("❌ Execution failed:", e)
