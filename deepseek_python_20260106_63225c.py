# 1. Crear agente
agent = create_solana_agent(private_key="your_key")

# 2. Ejecutar cualquier acción
result = await agent.execute("token", "create_token", name="MyToken", ...)

# 3. Usar con frameworks AI
tools = agent.create_tools("vercel_ai")  # Para Vercel AI SDK
# o
tools = agent.create_tools("langchain")   # Para LangChain