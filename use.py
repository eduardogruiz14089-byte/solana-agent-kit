# Ejemplo 1: Pipeline completo de creación de token y marketing
async def full_token_pipeline():
    agent = create_solana_agent()
    await agent.initialize()
    
    # 1. Crear token
    token_result = await agent.execute(
        plugin_name="token",
        action="create_token",
        name="SuperToken",
        symbol="SUPER",
        description="The best token ever created",
        image_path="./logo.png",
        amount_sol=0.5
    )
    
    if token_result['success']:
        token_address = token_result['token_address']
        
        # 2. Analizar token con MCP
        analysis = await agent.execute(
            plugin_name="mcp",
            action="mcp_query",
            query=f"Analyze this new token and suggest marketing strategies: {token_address}",
            context={'token': token_address}
        )
        
        # 3. Configurar trading bot
        bot_config = await agent.execute(
            plugin_name="trading_bot",
            action="add_strategy",
            strategy_name="liquidity_provider",
            token_address=token_address,
            buy_threshold=0.0001,
            sell_threshold=0.0002
        )
        
        # 4. Monitorear con vault
        vault = await agent.execute(
            plugin_name="vault",
            action="create_vault",
            seed="2eeb25e9f22b46bb932a4f0a88510f11"
        )
        
        return {
            'token': token_result,
            'analysis': analysis,
            'bot': bot_config,
            'vault': vault
        }

# Ejemplo 2: Agente autónomo con múltiples capacidades
class AutonomousAgent:
    def __init__(self, agent: SolanaAgent):
        self.agent = agent
        
    async def run_strategy(self, strategy: str):
        if strategy == "token_creator":
            # Crear múltiples tokens automáticamente
            tokens = ["Alpha", "Beta", "Gamma"]
            results = []
            
            for token_name in tokens:
                result = await self.agent.execute(
                    plugin_name="token",
                    action="create_token",
                    name=token_name,
                    symbol=token_name[:4].upper(),
                    description=f"Auto-created {token_name} token",
                    image_path=f"./{token_name.lower()}.png",
                    amount_sol=0.1
                )
                results.append(result)
            
            return results
        
        elif strategy == "market_maker":
            # Crear liquidez en múltiples pares
            pass
