import requests
from  crewai import Agent,Task,Crew,Process,LLM
from crewai.tools import tool
import chromadb
from chromadb.config import Settings
from prompt import Interview_prompt,Onboarding_prompt,Manager_prompt,Resume_prompt,policy_prompt
import os
import json,re
import sqlite3
import traceback
from pathlib import Path

os.environ['OTEL_SDK_DISABLED'] = 'true'

#api_key = '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'  # Replace with your actual API key

def llm_initializer(api_key):
    try:
        llm = LLM(
            model="gpt-4o",
            api_key=api_key,
        )
        return llm
    except Exception as e:
        raise RuntimeError(f"LLM init failed: {e}")

# Initialize LLM
llm = llm_initializer(api_key)

   
try:
    llm=llm_initializer(api_key)
except Exception as e:
    print(f"Failed to initialize LLM: {e}")
    
    
#tool to fetch data 

@tool("Policy Fetch Tool")
def policy_tool(policy_query: str) -> str:
    """
    Fetch HR policy data from ChromaDB based on policy name or description.
    """

    try:
        # 1. Validate Input
        if not policy_query:
            return "❌ Please provide a valid policy name or query."

        # 2. Connect to ChromaDB
        client = chromadb.Client(
            Settings(
                persist_directory="chroma_db",
                anonymized_telemetry=False
            )
        )

        # 3. Load Collection
        collection = client.get_collection(name="hr_policies")

        # 4. Execute Query
        result = collection.query(
            query_texts=[policy_query],
            n_results=3
        )

        documents = result.get("documents", [])

        # 5. Extract Policy Data
        if not documents or not documents[0]:
            return f"❌ No data found for policy: {policy_query}"

        policies = documents[0]

        # 6. Return Policies
        response = f"✅ Policies for '{policy_query}':\n\n"
        for i, policy in enumerate(policies):
            response += f"{i+1}. {policy}\n\n"

        return response.strip()

    except Exception as e:
        traceback.print_exc()
        return f"⚠️ Error fetching policy data: {str(e)}"

@tool("Resume Analyzer Tool")
def resume_analyzer_tool(resume_text: str) -> str:
    """
    Analyze a resume and extract key information.
    """

    try:
        # 1. Validate Input
        if not resume_text:
            return "❌ Please provide a valid resume text."

        # 2. Define Patterns
        patterns = {
            "Name": r"Name:\s*(.*)",
            "Email": r"Email:\s*([\w\.-]+@[\w\.-]+)",
            "Phone": r"Phone:\s*(\+?\d[\d -]{7,}\d)",
            "Skills": r"Skills:\s*(.*)",
            "Experience": r"Experience:\s*(.*?)(?:Education:|$)",
            "Education": r"Education:\s*(.*)"
        }

        # 3. Extract Information
        extracted_info = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, resume_text, re.DOTALL)
            if match:
                extracted_info[key] = match.group(1).strip()

        # 4. Format Response
        response = "✅ Extracted Resume Information:\n\n"
        for key, value in extracted_info.items():
            response += f"{key}: {value}\n\n"

        return response.strip()

    except Exception as e:
        traceback.print_exc()
        return f"⚠️ Error analyzing resume: {str(e)}"

@tool("Interview Question Generator Tool")
def interview_question_generator_tool(job_description: str) -> str:
    """
    Generate interview questions based on a job description.
    """

    try:
        # 1. Validate Input
        if not job_description:
            return " Please provide a valid job description."

        # 2. Define Prompt
        prompt = f"Generate a list of interview questions for the following job description:\n\n{job_description}\n\nQuestions:"

        # 3. Call LLM
        # response = llm.complete(
        #     prompt=prompt,
        #     max_tokens=300,
        #     temperature=0.7,
        #     n=1,
        #     stop=None
        # )

        # questions = response.choices[0].text.strip()
        response = llm.invoke(prompt)
        return f"✅ Generated Interview Questions:\n\n{response}"


        # 4. Format Response
        return f"✅ Generated Interview Questions:\n\n{questions}"

    except Exception as e:
        traceback.print_exc()
        return f"⚠️ Error generating interview questions: {str(e)}"
    
@tool("Onboarding Tracker Tool")
def onboarding_tracker_tool(employee_name: str, task: str, status: str) -> str:
    """
    Store and update onboarding tasks in ChromaDB using document collections.
    """

    try:
        # 1. Validate Input
        if not employee_name or not task or not status:
            return "❌ Please provide employee name, task, and status."

        # 2. Connect to ChromaDB
        client = chromadb.Client(
            Settings(
                persist_directory="chroma_db",
                anonymized_telemetry=False
            )
        )

        # 3. Load Chroma Collection
        collection = client.get_or_create_collection(name="onboarding_tasks")

        # 4. Build document
        document_text = f"Employee: {employee_name} | Task: {task} | Status: {status}"

        task_id = f"{employee_name}_{task}".replace(" ", "_").lower()

        # 5. Add or Update entry
        collection.add(
            documents=[document_text],
            metadatas=[{
                "employee": employee_name,
                "task": task,
                "status": status
            }],
            ids=[task_id]
        )

        return f"✅ Onboarding task stored for {employee_name} (Task: {task}, Status: {status})"

    except Exception as e:
        traceback.print_exc()
        return f"⚠️ Error storing onboarding task: {str(e)}"

# Initialize Agent
Policy_agent = Agent(
    role="Policy Assistant",
    goal="Assist employees with HR policy queries and related tasks.",
    backstory=policy_prompt,
    verbose=True,
    allow_delegation=False,
    tools=[policy_tool],
    llm=llm,
)
Resume_agent = Agent(
    role="Resume Analyzer",
    goal="Analyze resumes and extract key information for HR purposes.",
    backstory=Resume_prompt,
    verbose=True,
    allow_delegation=False,
    tools=[resume_analyzer_tool],
    llm=llm,
)
Interview_agent = Agent(
    role="Interview Question Generator",
    goal="Generate interview questions based on job descriptions.",
    backstory=Interview_prompt,
    verbose=True,
    allow_delegation=False,
    tools=[interview_question_generator_tool],
    llm=llm,
)
Onboarding_agent = Agent(
    role="Onboarding Tracker",
    goal="Track and store onboarding tasks for new employees.",
    backstory=Onboarding_prompt,
    verbose=True,
    allow_delegation=False,
    tools=[onboarding_tracker_tool],
    llm=llm,
)
manager_agent = Agent(
    role="Manager Agent",
    goal="Delegates tasks to proper HR agents",
    backstory=Manager_prompt,
    verbose=True,
    allow_delegation=True,
    llm=llm,
)

while True:
    user_input = input("Enter your HR-related query (or 'exit' to quit): ")
    if user_input.lower() == 'exit':
        break
    if not user_input:
        print("Please enter a valid query.")
        continue
    try:
        manager_task = Task(
            description="Manage HR-related queries and delegate tasks to appropriate agents.",
            expected_output="The precise and appropriate response or data depending on the nature of the query."
        )
        crew = Crew(
    agents=[Policy_agent, Resume_agent, Interview_agent, Onboarding_agent],
    manager_agent=manager_agent,
    task=manager_task,
    process=Process.hierarchical,
    verbose=True,
)

        result = crew.kickoff()
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")
    
         
        