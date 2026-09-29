from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama

# Import your custom tools from tools.py
from tools import (
    fetch_and_load_currenflux_data,
    export_query_to_excel,
    generate_consolidated_spreadsheet,
    DB_PATH)

tools = [
    fetch_and_load_currenflux_data,
    export_query_to_excel,
    generate_consolidated_spreadsheet, # <--- ADICIONAR AQUI NA LISTA DO AGENTE
]

# 1. Carrega dados iniciais
fetch_and_load_currenflux_data.invoke({})

# 2. Configuração do Banco de Dados e LLM
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
coder_llm = ChatOllama(model="qwen2.5-coder:3b", temperature=0)
agent_llm = ChatOllama(model="gemma4:e4b", temperature=0)

# 3. Consolida TODAS as ferramentas (Toolkit SQL + Suas Ferramentas Customizadas)
sql_toolkit = SQLDatabaseToolkit(db=db, llm=coder_llm)

tools = sql_toolkit.get_tools() + [
    fetch_and_load_currenflux_data,
    export_query_to_excel,
    generate_consolidated_spreadsheet, # <--- GARANTA QUE ESTÁ AQUI
]

# 4. Prompt do Agente
prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é o assistente do CurrenFlux. Sempre use a ferramenta generate_consolidated_spreadsheet para exportar relatórios consolidados."),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(agent_llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    agent_executor.invoke({"input": "Gere o relatório consolidado em Excel."})