#!/usr/bin/env python3
"""
Script principal para ejecutar el agente mejorado
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Añadir directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from solana_agent_kit import create_solana_agent, SolanaAgent
from mcp_integration import add_mcp_server, MCPServer

async def main():
    print("\n" + "="*70)
    print("🚀 SOLANA SUPER AGENT - Enhanced Multi-Capability Agent")
    print("="*70 + "\n")
    
    # Cargar configuración
    config_path = Path("agent_config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # 1. Crear agente (con o sin clave privada)
    print("1. Creating Solana Agent...")
    
    # Opción: usar clave privada existente o generar nueva
    private_key = os.getenv('SOLANA_PRIVATE_KEY')
    
    agent = create_solana_agent(
        private_key=private_key,
        rpc_url=config.get('rpc', {}).get('url'),
        config=config
    )
    
    # 2. Inicializar agente
    print("2. Initializing agent and plugins...")
    await agent.initialize()
    
    # 3. Mostrar estado
    status = await agent.get_agent_status()
    print(f"\n✅ Agent Status:")
    print(f"   Agent ID: {status['agent_id']}")
    print(f"   Wallet: {status['wallet_address']}")
    print(f"   Plugins: {', '.join(status['plugins_enabled'])}")
    print(f"   Capabilities: {', '.join(status['capabilities'])}")
    
    # 4. Conectar MCP si está configurado
    mcp_servers = config.get('mcp_servers', [])
    if mcp_servers:
        print("\n3. Connecting to MCP servers...")
        for server_config in mcp_servers:
            if server_config.get('enabled', False):
                mcp = MCPServer(
                    transport=server_config['transport'],
                    endpoint=server_config['endpoint'],
                    agent_id=status['agent_id']
                )
                
                if await mcp.connect():
                    print(f"   ✅ Connected to MCP: {server_config['endpoint']}")
                    
                    # Listar herramientas MCP
                    tools = await mcp.list_tools()
                    if tools:
                        print(f"   Available MCP tools: {len(tools)}")
                        for tool in tools[:5]:  # Mostrar primeras 5
                            print(f"     - {tool.get('name')}")
    
    # 5. Ejecutar comandos de ejemplo
    print("\n4. Running example commands...")
    
    # Ejemplo 1: Crear token
    print("   Example 1: Creating test token...")
    result = await agent.execute(
        plugin_name="token",
        action="create_token",
        name="AgentTest",
        symbol="AGENT",
        description="Token created by enhanced Solana Agent",
        image_path="./example.png",  # Asegúrate de tener este archivo
        amount_sol=0.1,
        slippage=10.0
    )
    
    if result.get('success'):
        print(f"   ✅ Token created: {result.get('token_address')}")
    else:
        print(f"   ❌ Token creation failed: {result.get('error', 'Unknown error')}")
    
    # Ejemplo 2: Consultar MCP
    print("\n   Example 2: Querying MCP server...")
    mcp_result = await agent.execute(
        plugin_name="mcp",
        action="mcp_query",
        query="What are the top trending tokens on Solana?",
        context={'network': 'solana'}
    )
    
    if mcp_result.get('success'):
        print("   ✅ MCP query successful")
    else:
        print(f"   ❌ MCP query failed: {mcp_result.get('error', 'Unknown error')}")
    
    # Ejemplo 3: Crear vault
    print("\n   Example 3: Creating gold vault...")
    vault_result = await agent.execute(
        plugin_name="vault",
        action="create_vault",
        seed="2eeb25e9f22b46bb932a4f0a88510f11"
    )
    
    if vault_result.get('success'):
        print(f"   ✅ Vault created: {vault_result.get('vault_address')}")
    
    # 6. Ejecución múltiple
    print("\n5. Running multiple commands...")
    commands = [
        {
            'plugin': 'market',
            'action': 'get_market_trends',
            'params': {}
        },
        {
            'plugin': 'security',
            'action': 'analyze_risks',
            'params': {'target': 'vault'}
        }
    ]
    
    multi_results = await agent.multi_execute(commands)
    print(f"   Executed {len(multi_results)} commands")
    
    # 7. Mostrar herramientas disponibles para AI
    print("\n6. Available AI tools:")
    tools = agent.create_tools("vercel_ai")
    for plugin_name, tool_info in tools.items():
        print(f"   - {plugin_name}: {tool_info.get('description', 'No description')}")
    
    print("\n" + "="*70)
    print("🎯 Agent ready for action!")
    print("\nQuick commands:")
    print("  agent.execute('token', 'create_token', name='MyToken', ...)")
    print("  agent.execute('defi', 'swap', from_token='SOL', to_token='USDC', amount=1.0)")
    print("  agent.execute('trading_bot', 'start_bot', strategy_name='momentum')")
    print("="*70)
    
    return agent

async def interactive_mode(agent: SolanaAgent):
    """Modo interactivo para probar el agente"""
    import readline  # Para mejor entrada en terminal
    
    print("\n" + "="*70)
    print("💻 INTERACTIVE MODE - Type commands or 'help'")
    print("="*70)
    
    help_text = """
Available commands:
  help                    - Show this help
  status                  - Show agent status
  plugins                 - List available plugins
  capabilities           - List agent capabilities
  execute <plugin> <action> [params] - Execute plugin action
  multi [commands_json]  - Execute multiple commands
  tools                  - Show AI tools
  quit                   - Exit interactive mode
  
Example:
  execute token create_token name=TestToken symbol=TEST amount_sol=0.1
  execute market analyze_token token_address=TOKEN_ADDRESS
    """
    
    print(help_text)
    
    while True:
        try:
            command = input("\nagent> ").strip()
            
            if command == "quit" or command == "exit":
                print("Goodbye!")
                break
                
            elif command == "help":
                print(help_text)
                
            elif command == "status":
                status = await agent.get_agent_status()
                print(json.dumps(status, indent=2))
                
            elif command == "plugins":
                print("Enabled plugins:")
                for plugin_name in agent.enabled_plugins:
                    plugin = agent.plugins[plugin_name]
                    caps = [c.value for c in plugin.capabilities]
                    print(f"  {plugin_name}: {caps}")
                    
            elif command == "capabilities":
                caps = agent.get_capabilities()
                print("Agent capabilities:")
                for cap in caps:
                    print(f"  - {cap}")
                    
            elif command.startswith("execute "):
                parts = command[8:].split()
                if len(parts) >= 2:
                    plugin_name = parts[0]
                    action = parts[1]
                    
                    # Parse parameters (simple key=value format)
                    params = {}
                    for part in parts[2:]:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            # Try to convert to appropriate type
                            try:
                                value = float(value) if '.' in value else int(value)
                            except:
                                pass
                            params[key] = value
                    
                    print(f"Executing: {plugin_name}.{action} with {params}")
                    result = await agent.execute(plugin_name, action, **params)
                    print(json.dumps(result, indent=2))
                    
            elif command == "tools":
                tools = agent.create_tools("vercel_ai")
                print("Available AI tools:")
                for name, info in tools.items():
                    print(f"\n{name}:")
                    print(f"  Description: {info.get('description')}")
                    
            else:
                print(f"Unknown command: {command}. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Configurar logging
    os.environ.setdefault('DEFAULT_LOG_LEVEL', 'INFO')
    
    try:
        # Ejecutar agente
        agent = asyncio.run(main())
        
        # Preguntar por modo interactivo
        response = input("\nEnter interactive mode? (y/n): ").strip().lower()
        if response == 'y':
            asyncio.run(interactive_mode(agent))
            
    except KeyboardInterrupt:
        print("\n\nAgent stopped by user")
    except Exception as e:
        print(f"\n❌ Agent error: {e}")
        import traceback
        traceback.print_exc()