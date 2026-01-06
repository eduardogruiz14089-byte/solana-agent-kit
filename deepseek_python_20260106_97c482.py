"""
Integración MCP (Model Context Protocol) Mejorada
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from enum import Enum

class MCPTransport(Enum):
    HTTP = "http"
    WEBSOCKET = "websocket"
    STDIO = "stdio"

class MCPServer:
    """Cliente para servidor MCP"""
    
    def __init__(self, 
                 transport: MCPTransport = MCPTransport.HTTP,
                 endpoint: str = None,
                 agent_id: str = None):
        
        self.transport = transport
        self.endpoint = endpoint or "https://mcp.solana.com/mcp"
        self.agent_id = agent_id or "solana_agent"
        self.session_id = None
        
    async def connect(self):
        """Conectar con servidor MCP"""
        if self.transport == MCPTransport.HTTP:
            # Test connection
            try:
                response = requests.get(f"{self.endpoint}/health")
                if response.status_code == 200:
                    print(f"✅ Connected to MCP server: {self.endpoint}")
                    return True
            except Exception as e:
                print(f"❌ MCP connection failed: {e}")
                return False
        
        return False
    
    async def query(self, 
                   query: str, 
                   context: Dict[str, Any] = None,
                   tools: List[str] = None) -> Dict[str, Any]:
        """Realizar consulta al servidor MCP"""
        
        payload = {
            'query': query,
            'context': context or {},
            'agent_id': self.agent_id,
            'session_id': self.session_id,
            'tools': tools or []
        }
        
        try:
            response = requests.post(
                f"{self.endpoint}/query",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'query': query
                }
            else:
                return {
                    'success': False,
                    'error': response.text,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def execute_tool(self, 
                          tool_name: str, 
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar herramienta a través de MCP"""
        
        payload = {
            'tool': tool_name,
            'parameters': parameters,
            'agent_id': self.agent_id
        }
        
        try:
            response = requests.post(
                f"{self.endpoint}/execute",
                json=payload
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'result': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Listar herramientas disponibles en MCP"""
        try:
            response = requests.get(f"{self.endpoint}/tools")
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

# CLI para añadir servidor MCP
def add_mcp_server(transport: str, endpoint: str):
    """
    Añadir servidor MCP a la configuración del agente
    
    Ejemplo de uso:
    python -c "from mcp_integration import add_mcp_server; add_mcp_server('http', 'https://mcp.solana.com/mcp')"
    """
    
    config_path = os.path.join(os.path.dirname(__file__), 'agent_config.json')
    
    # Cargar o crear configuración
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Añadir configuración MCP
    if 'mcp_servers' not in config:
        config['mcp_servers'] = []
    
    config['mcp_servers'].append({
        'transport': transport,
        'endpoint': endpoint,
        'added_at': datetime.now().isoformat()
    })
    
    # Guardar configuración
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ MCP server added: {transport}://{endpoint}")
    return True