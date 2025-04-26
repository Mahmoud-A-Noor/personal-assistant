from browser_use import Agent as BrowserAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()


class BrowserTaskAgent:
    """A wrapper for browser_use.Agent to run autonomous browser tasks."""
    def __init__(self, llm=None):
        # Use a LangChain-compatible Gemini LLM for browser agent tasks
        if llm:
            self.llm = llm
        else:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-001",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
            )

    async def run_task(self, task: str):
        agent = BrowserAgent(task=task, llm=self.llm)
        history = await agent.run()
        
        ## Access various types of information
        # urls = history.urls()              # URLs visited
        # screenshots = history.screenshots()       # Screenshot paths
        # actions = history.action_names()      # Actions taken
        # content = history.extracted_content() # Extracted data
        # errors = history.errors()           # Any errors
        # model_actions = history.model_actions()     # All actions with parameters
        
        # Compose a concise, useful summary for the LLM
        content = history.extracted_content()
        errors = history.errors()
        summary_parts = []
        if content:
            if isinstance(content, list):
                summary_parts.append("\n".join(str(c) for c in content if c))
            else:
                summary_parts.append(str(content))
        if errors:
            print("\n".join(str(e) for e in errors if e))
            summary_parts.append("Couldn't extract information from the browsing session.")
        if not summary_parts:
            summary_parts.append("No useful information could be extracted from the browsing session.")
        return "\n".join(summary_parts)