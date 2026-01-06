# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear archivos de configuración
# Crear agent_config.json con la configuración anterior

# 3. Añadir servidor MCP (equivalente al comando Claude MCP)
python -c "
from mcp_integration import add_mcp_server
add_mcp_server('http', 'https://mcp.solana.com/mcp')
"

# 4. Configurar variables de entorno
echo "SOLANA_PRIVATE_KEY=your_base58_private_key_here" > .env
echo "PUMP_PORTAL_API_KEY=your_pump_portal_api_key" >> .env

# 5. Ejecutar agente
python run_agent.py