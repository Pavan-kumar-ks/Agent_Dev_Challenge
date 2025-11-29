# import os
# import re
# import streamlit as st
# import chromadb
# from chromadb.config import Settings
# from crewai import Agent, Task, Crew, Process, LLM
# from crewai.tools import tool

# # -------------------------
# # PAGE CONFIG
# # -------------------------
# st.set_page_config(page_title="HR AI Assistant", layout="centered")
# st.title("🧑‍💼 HR AI Assistant")
# st.write("Ask about policies, resumes, interviews, or onboarding")

# # -------------------------
# # API KEY (LOCAL TESTING ONLY)
# # -------------------------
# # TEMPORARY API KEY FOR LOCAL TESTING ONLY
# api_key = "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"

# if not api_key or not api_key.startswith("sk-"):
#     st.error("Invalid API Key")
#     st.stop()

# if not api_key:
#     st.warning("Please enter API key to continue")
#     st.stop()

# # -------------------------
# # LLM INIT
# # -------------------------
# def llm_initializer(api_key):
#     return LLM(model="gpt-4o", api_key=api_key)

# llm = llm_initializer(api_key)

# # -------------------------
# # TOOLS
# # -------------------------
# @tool("Policy Fetch Tool")
# def policy_tool(policy_query: str) -> str:
#     """Fetch HR policy information from database."""
#     try:
#         client = chromadb.Client(Settings(persist_directory="chroma_db"))
#         collection = client.get_or_create_collection(name="hr_policies")
#         result = collection.query(query_texts=[policy_query], n_results=3)

#         docs = result.get("documents", [])
#         if not docs or not docs[0]:
#             return "No policy found."

#         return "\n\n".join(docs[0])

#     except Exception as e:
#         return str(e)

# @tool("Resume Analyzer Tool")
# def resume_analyzer_tool(resume_text: str) -> str:
#     """Extract info from resume."""
#     email = re.findall(r"[\w\.-]+@[\w\.-]+", resume_text)
#     phone = re.findall(r"\+?\d[\d -]{7,}\d", resume_text)
#     return f"Email: {email}\nPhone: {phone}"

# @tool("Interview Generator Tool")
# def interview_tool(job_desc: str) -> str:
#     """Generate interview questions."""
#     return llm.invoke(f"Generate interview questions for: {job_desc}")

# @tool("Onboarding Tracker Tool")
# def onboarding_tool(name: str, task: str, status: str) -> str:
#     """Store onboarding info."""
#     client = chromadb.Client(Settings(persist_directory="chroma_db"))
#     col = client.get_or_create_collection("onboarding")
#     col.add(documents=[f"{name} | {task} | {status}"], ids=[f"{name}{task}"])
#     return "Onboarding saved."

# # -------------------------
# # AGENTS
# # -------------------------
# policy_agent = Agent(
#     role="Policy Assistant",
#     goal="Answer HR policy questions",
#     backstory="You know HR policies.",
#     tools=[policy_tool],
#     llm=llm,
#     verbose=True
# )

# resume_agent = Agent(
#     role="Resume Analyzer",
#     goal="Extract information from resumes",
#     backstory="You parse resumes.",
#     tools=[resume_analyzer_tool],
#     llm=llm,
#     verbose=True
# )

# interview_agent = Agent(
#     role="Interview Agent",
#     goal="Generate interview questions",
#     backstory="You prepare interview questions.",
#     tools=[interview_tool],
#     llm=llm,
#     verbose=True
# )

# onboarding_agent = Agent(
#     role="Onboarding Tracker",
#     goal="Track new employee onboarding",
#     backstory="You store onboarding tasks.",
#     tools=[onboarding_tool],
#     llm=llm,
#     verbose=True
# )

# # manager_agent = Agent(
# #     role="Manager",
# #     goal="Route queries to correct agent",
# #     backstory="""
# #     Route user query:
# #     policy → policy agent
# #     resume → resume agent
# #     interview → interview agent
# #     onboarding → onboarding agent
# #     """,
# #     llm=llm,
# #     allow_delegation=True,
# #     verbose=True
# # )
# final_agent = Agent(
#     role="Final Answer Agent",
#     goal="Generate a direct answer for any HR query",
#     backstory="""
# You ALWAYS return a final user-facing answer.
# If tools failed or routing fails, summarize based on your knowledge.
# NEVER return empty output.
# """,
#     llm=llm,
#     verbose=True
# )


# # -------------------------
# # UI INPUT
# # -------------------------
# query = st.text_input("Ask HR Question", placeholder="e.g. leave policy")

# # -------------------------
# # RUN CREW
# # -------------------------
# if st.button("Submit"):
#     task = Task(
#     description=f"""
# User Query: {query}

# Do the following:
# 1. Try to use tools if relevant.
# 2. If tools fail, answer from knowledge.
# 3. Final Answer Agent MUST return response.

# DO NOT return empty output.
# """,
#     expected_output="A complete HR response."
# )



#     crew = Crew(
#     agents=[
#         policy_agent,
#         resume_agent,
#         interview_agent,
#         onboarding_agent,
#         final_agent     # ✅ GUARANTEED OUTPUT
#     ],
#     task=task,
#     process=Process.sequential,  # FORCE execution
#     verbose=True
# )


#     with st.spinner("Processing..."):
#         try:
#             result = crew.kickoff()
#             if not result:
#                 st.error("No output generated.")
#             else:
#                 st.success("Response")
#                 st.write(result)
#         except Exception as e:
#             st.error(f"Error: {e}")












import os
import re
import streamlit as st
import chromadb
from chromadb.config import Settings
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
import traceback

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(page_title="HR AI Assistant", layout="centered")
st.title("🧑‍💼 HR AI Assistant")
st.write("Ask about policies, resumes, interviews, or onboarding")

# -------------------------
# API KEY (GROQ SETUP)
# -------------------------
# -------------------------
# API KEY (HARDCODED - LOCAL TESTING ONLY)
# -------------------------
#GROQ_KEY = "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"

if not GROQ_KEY or "PASTE" in GROQ_KEY:
    st.error("❌ API Key is missing or not updated in code.")
    st.stop()


# -------------------------
# LLM INIT (GROQ WORKING CONFIG)
# -------------------------
def llm_initializer():
    return LLM(
        model="groq/llama-3.1-70b-versatile",
        api_key=GROQ_KEY
    )

llm = llm_initializer()


# -------------------------
# TOOLS
# -------------------------
@tool("Policy Fetch Tool")
def policy_tool(policy_query: str) -> str:
    """Fetch HR policy info from ChromaDB."""
    try:
        client = chromadb.Client(Settings(persist_directory="chroma_db"))
        collection = client.get_or_create_collection(name="hr_policies")
        result = collection.query(query_texts=[policy_query], n_results=3)

        docs = result.get("documents", [])
        if not docs or not docs[0]:
            return "No policy found."

        return "\n\n".join(docs[0])

    except Exception as e:
        return f"Policy DB Error: {str(e)}"


@tool("Resume Analyzer Tool")
def resume_analyzer_tool(resume_text: str) -> str:
    """Extract email & phone."""
    email = re.findall(r"[\w\.-]+@[\w\.-]+", resume_text)
    phone = re.findall(r"\+?\d[\d -]{7,}\d", resume_text)
    return f"📧 Email: {email}\n📱 Phone: {phone}"


@tool("Interview Generator Tool")
def interview_tool(job_desc: str) -> str:
    """Generate interview questions."""
    response = llm.invoke(f"Generate interview questions for job role: {job_desc}")
    return response.content


@tool("Onboarding Tracker Tool")
def onboarding_tool(name: str, task: str, status: str) -> str:
    """Store onboarding record."""
    try:
        client = chromadb.Client(Settings(persist_directory="chroma_db"))
        col = client.get_or_create_collection("onboarding")
        col.add(documents=[f"{name} | {task} | {status}"], ids=[f"{name}_{task}"])
        return "✅ Onboarding saved."
    except Exception as e:
        return f"Onboarding Error: {str(e)}"


# -------------------------
# AGENTS
# -------------------------
policy_agent = Agent(
    role="Policy Assistant",
    goal="Answer HR policy questions",
    backstory="Expert in HR policies",
    tools=[policy_tool],
    llm=llm,
    verbose=True
)

resume_agent = Agent(
    role="Resume Analyzer",
    goal="Parse resume data",
    backstory="Expert resume analyst",
    tools=[resume_analyzer_tool],
    llm=llm,
    verbose=True
)

interview_agent = Agent(
    role="Interview Agent",
    goal="Create interview questions",
    backstory="Expert interviewer",
    tools=[interview_tool],
    llm=llm,
    verbose=True
)

onboarding_agent = Agent(
    role="Onboarding Tracker",
    goal="Track onboarding tasks",
    backstory="HR onboarding system",
    tools=[onboarding_tool],
    llm=llm,
    verbose=True
)

final_agent = Agent(
    role="Final HR Assistant",
    goal="Always return a complete answer to user",
    backstory="Never return empty answer. Summarize intelligently.",
    llm=llm,
    verbose=True
)


# -------------------------
# UI INPUT
# -------------------------
query = st.text_input("Ask HR Question", placeholder="e.g. Leave policy / Resume text / Interview role")

# -------------------------
# RUN CREW
# -------------------------
if st.button("Submit"):

    task = Task(
    description=f"""
User Query: {query}

1. Use tools if helpful.
2. If tools fail, answer using knowledge.
3. Always return final answer.
""",
    expected_output="Clear final answer",
    agent=final_agent 
)

    crew = Crew(
        agents=[
            policy_agent,
            resume_agent,
            interview_agent,
            onboarding_agent,
            final_agent
        ],
        tasks=[task],    # ✅ FIXED
        process=Process.sequential,
        verbose=True
    )

    with st.spinner("Processing..."):
        try:
            result = crew.kickoff()
            if not result:
                st.error("⚠ No result generated.")
            else:
                st.success("✅ Response")
                st.write(result)

        except Exception:
            st.error("❌ Crew Execution Failed")
            st.code(traceback.format_exc())
