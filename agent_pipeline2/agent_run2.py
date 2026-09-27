from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama

# Import your custom tools from tools.py
from tools import fetch_and_load_currenflux_data, export_query_to_excel, DB_PATH

# 1. Load initial data (creates currenflux.db)
fetch_and_load_currenflux_data.invoke({})

# 2. Database & LLM setup
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
coder_llm = ChatOllama(model="qwen2.5-coder:3b", temperature=0)
agent_llm = ChatOllama(model="gemma4:e4b", temperature=0)

# 3. Consolidate tools
sql_toolkit = SQLDatabaseToolkit(db=db, llm=coder_llm)
tools = sql_toolkit.get_tools() + [fetch_and_load_currenflux_data, export_query_to_excel]

# 4. Agent prompt and execution
prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é o assistente do CurrenFlux. Use as ferramentas para consultar o banco e gerar planilhas. "
           "Se o usuário não especificar um nome de arquivo, use 'relatorio_output.xlsx' como padrão."),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Substituted create_openai_tools_agent with create_tool_calling_agent
agent = create_tool_calling_agent(agent_llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    agent_executor.invoke({"input": "Gere um relatório Excel combinando as tabelas fx_dashboard, cb_rates e trade_data."})