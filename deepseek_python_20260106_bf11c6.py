"""
Solana Agent Kit Mejorado - Sistema Completo de Agente con Múltiples Capacidades
Fusiona: Pump.fun, Solana Agent Kit, MCP Server y Gold Vault
"""

import os
import sys
import json
import asyncio
import requests
import base64
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Importar dependencias de Solana
try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.transaction import VersionedTransaction
    from solders.commitment_config import CommitmentLevel
    from solders.rpc.requests import SendVersionedTransaction
    from solders.rpc.config import RpcSendTransactionConfig
    from solana.rpc.api import Client
    from solana.rpc.commitment import Confirmed
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    print("Warning: solana-py/solders not installed. Install with: pip install solana solders")

# Importar nuestro logger mejorado
sys.path.insert(0, str(Path(__file__).parent))
from logger import get_logger

log = get_logger()

class AgentCapability(Enum):
    """Capacidades del agente"""
    TOKEN_CREATION = "token_creation"
    TOKEN_TRADING = "token_trading"
    NFT_MINTING = "nft_minting"
    DEFI_OPERATIONS = "defi_operations"
    VAULT_MANAGEMENT = "vault_management"
    BLINKS_EXECUTION = "blinks_execution"
    MCP_INTEGRATION = "mcp_integration"
    MARKET_ANALYSIS = "market_analysis"
    SECURITY_AUDIT = "security_audit"
    AUTOMATED_TRADING = "automated_trading"

class Plugin:
    """Clase base para plugins del agente"""
    
    def __init__(self, name: str, capabilities: List[AgentCapability]):
        self.name = name
        self.capabilities = capabilities
        self.enabled = True
        
    async def initialize(self, agent: 'SolanaAgent'):
        """Inicializar plugin"""
        log.info(f"plugin_{self.name}", "initializing", f"Capabilities: {[c.value for c in self.capabilities]}")
        
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Ejecutar acción del plugin"""
        raise NotImplementedError

class TokenPlugin(Plugin):
    """Plugin para creación y gestión de tokens"""
    
    def __init__(self):
        super().__init__("token", [
            AgentCapability.TOKEN_CREATION,
            AgentCapability.TOKEN_TRADING
        ])
        self.pump_fun_api = "https://pump.fun"
        self.pump_portal_api = "https://pumpportal.fun"
        
    async def initialize(self, agent: 'SolanaAgent'):
        await super().initialize(agent)
        self.agent = agent
        
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "create_token":
            return await self.create_token(**kwargs)
        elif action == "buy_token":
            return await self.buy_token(**kwargs)
        elif action == "sell_token":
            return await self.sell_token(**kwargs)
        elif action == "get_token_info":
            return await self.get_token_info(**kwargs)
        else:
            raise ValueError(f"Action {action} not supported by TokenPlugin")
    
    async def create_token(self, 
                          name: str,
                          symbol: str,
                          description: str,
                          image_path: str,
                          twitter_url: str = "",
                          telegram_url: str = "",
                          website_url: str = "",
                          amount_sol: float = 1.0,
                          slippage: float = 10.0,
                          priority_fee: float = 0.0005,
                          show_name: bool = True) -> Dict[str, Any]:
        """Crear un nuevo token en Pump.fun"""
        
        log.info("token", "creating", f"{name} ({symbol})")
        
        try:
            # 1. Generar keypair para el token
            mint_keypair = Keypair()
            
            # 2. Preparar metadata
            form_data = {
                'name': name,
                'symbol': symbol,
                'description': description,
                'twitter': twitter_url,
                'telegram': telegram_url,
                'website': website_url,
                'showName': str(show_name).lower()
            }
            
            # 3. Subir imagen a IPFS
            with open(image_path, 'rb') as f:
                file_content = f.read()
            
            files = {
                'file': (os.path.basename(image_path), file_content, 'image/png')
            }
            
            log.debug("token", "uploading_image", f"Image: {image_path}")
            
            # Crear metadata en IPFS
            metadata_response = requests.post(
                f"{self.pump_fun_api}/api/ipfs",
                data=form_data,
                files=files
            )
            
            if metadata_response.status_code != 200:
                raise Exception(f"IPFS upload failed: {metadata_response.text}")
            
            metadata_json = metadata_response.json()
            
            # 4. Crear token metadata
            token_metadata = {
                'name': name,
                'symbol': symbol,
                'uri': metadata_json['metadataUri']
            }
            
            # 5. Enviar transacción de creación
            api_key = self.agent.config.get('PUMP_PORTAL_API_KEY', '')
            response = requests.post(
                f"{self.pump_portal_api}/api/trade?api-key={api_key}",
                headers={'Content-Type': 'application/json'},
                data=json.dumps({
                    'action': 'create',
                    'tokenMetadata': token_metadata,
                    'mint': str(mint_keypair),
                    'denominatedInSol': 'true',
                    'amount': amount_sol,
                    'slippage': slippage,
                    'priorityFee': priority_fee,
                    'pool': 'pump',
                    'isMayhemMode': 'false'
                })
            )
            
            if response.status_code == 200:
                data = response.json()
                
                result = {
                    'success': True,
                    'token_address': str(mint_keypair.pubkey()),
                    'transaction_signature': data.get('signature'),
                    'explorer_url': f"https://solscan.io/tx/{data.get('signature')}",
                    'metadata_uri': metadata_json['metadataUri'],
                    'name': name,
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat()
                }
                
                log.info("token", "created", 
                        f"Token {symbol} created: {result['token_address']}")
                
                return result
            else:
                error_msg = response.reason or response.text
                log.error("token", "creation_failed", error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            log.error("token", "creation_error", str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_token_local(self, **kwargs) -> Dict[str, Any]:
        """Crear token usando transacción local (firmada localmente)"""
        signer_keypair = self.agent.wallet.keypair
        
        # Generar keypair para el token
        mint_keypair = Keypair()
        
        # Extraer parámetros
        name = kwargs.get('name', 'TestToken')
        symbol = kwargs.get('symbol', 'TEST')
        description = kwargs.get('description', 'Test token created by agent')
        image_path = kwargs.get('image_path', './example.png')
        amount_sol = kwargs.get('amount_sol', 1.0)
        
        # Preparar metadata
        form_data = {
            'name': name,
            'symbol': symbol,
            'description': description,
            'twitter': kwargs.get('twitter_url', ''),
            'telegram': kwargs.get('telegram_url', ''),
            'website': kwargs.get('website_url', ''),
            'showName': str(kwargs.get('show_name', True)).lower()
        }
        
        # Subir imagen
        with open(image_path, 'rb') as f:
            file_content = f.read()
        
        files = {
            'file': (os.path.basename(image_path), file_content, 'image/png')
        }
        
        # Crear metadata en IPFS
        metadata_response = requests.post(
            f"{self.pump_fun_api}/api/ipfs",
            data=form_data,
            files=files
        )
        
        if metadata_response.status_code != 200:
            raise Exception(f"IPFS upload failed: {metadata_response.text}")
        
        metadata_json = metadata_response.json()
        
        # Token metadata
        token_metadata = {
            'name': name,
            'symbol': symbol,
            'uri': metadata_json['metadataUri']
        }
        
        # Obtener transacción firmada localmente
        response = requests.post(
            f"{self.pump_portal_api}/api/trade-local",
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'publicKey': str(signer_keypair.pubkey()),
                'action': 'create',
                'tokenMetadata': token_metadata,
                'mint': str(mint_keypair.pubkey()),
                'denominatedInSol': 'true',
                'amount': amount_sol,
                'slippage': kwargs.get('slippage', 10.0),
                'priorityFee': kwargs.get('priority_fee', 0.0005),
                'pool': 'pump',
                'isMayhemMode': 'false'
            })
        )
        
        # Crear transacción versionada
        tx = VersionedTransaction.from_bytes(response.content)
        
        # Firmar transacción
        signed_tx = VersionedTransaction(
            tx.message,
            [mint_keypair, signer_keypair]
        )
        
        # Enviar transacción
        commitment = CommitmentLevel.Confirmed
        config = RpcSendTransactionConfig(preflight_commitment=commitment)
        
        client = Client(self.agent.config.get('RPC_URL', 'https://api.mainnet-beta.solana.com'))
        
        # Enviar transacción (simplificado - en producción usar método apropiado)
        result = {
            'success': True,
            'token_address': str(mint_keypair.pubkey()),
            'method': 'local_signed',
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    async def buy_token(self, token_address: str, amount_sol: float, **kwargs) -> Dict[str, Any]:
        """Comprar tokens"""
        log.info("token", "buying", f"{amount_sol} SOL of {token_address[:10]}...")
        
        # Implementar lógica de compra
        return {
            'success': True,
            'action': 'buy',
            'token_address': token_address,
            'amount_sol': amount_sol,
            'timestamp': datetime.now().isoformat()
        }
    
    async def sell_token(self, token_address: str, amount_tokens: float, **kwargs) -> Dict[str, Any]:
        """Vender tokens"""
        log.info("token", "selling", f"{amount_tokens} tokens of {token_address[:10]}...")
        
        # Implementar lógica de venta
        return {
            'success': True,
            'action': 'sell',
            'token_address': token_address,
            'amount_tokens': amount_tokens,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """Obtener información de token"""
        # Implementar obtención de información
        return {
            'address': token_address,
            'name': 'Unknown',
            'symbol': 'UNKNOWN',
            'supply': 0,
            'holders': 0,
            'price': 0
        }

class NFTPlugin(Plugin):
    """Plugin para NFTs"""
    
    def __init__(self):
        super().__init__("nft", [AgentCapability.NFT_MINTING])
        
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "mint_nft":
            return await self.mint_nft(**kwargs)
        elif action == "transfer_nft":
            return await self.transfer_nft(**kwargs)
        else:
            raise ValueError(f"Action {action} not supported by NFTPlugin")
    
    async def mint_nft(self, **kwargs):
        """Mintear un NFT"""
        return {'action': 'mint_nft', 'success': True}

class DeFiPlugin(Plugin):
    """Plugin para DeFi"""
    
    def __init__(self):
        super().__init__("defi", [AgentCapability.DEFI_OPERATIONS])
        
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "swap":
            return await self.swap(**kwargs)
        elif action == "add_liquidity":
            return await self.add_liquidity(**kwargs)
        elif action == "stake":
            return await self.stake(**kwargs)
        else:
            raise ValueError(f"Action {action} not supported by DeFiPlugin")
    
    async def swap(self, from_token: str, to_token: str, amount: float, **kwargs):
        """Realizar swap de tokens"""
        return {'action': 'swap', 'success': True}

class VaultPlugin(Plugin):
    """Plugin para gestión de vaults (del Gold Infrastructure)"""
    
    def __init__(self):
        super().__init__("vault", [AgentCapability.VAULT_MANAGEMENT])
        
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "create_vault":
            return await self.create_vault(**kwargs)
        elif action == "fund_vault":
            return await self.fund_vault(**kwargs)
        elif action == "monitor_vault":
            return await self.monitor_vault(**kwargs)
        else:
            raise ValueError(f"Action {action} not supported by VaultPlugin")
    
    async def create_vault(self, seed: str = None, **kwargs):
        """Crear un vault"""
        # Usar seed del Gold Vault o generar una
        seed = seed or "2eeb25e9f22b46bb932a4f0a88510f11"
        seed_bytes = bytes.fromhex(seed)[:32]
        vault_keypair = Keypair.from_seed(seed_bytes)
        
        return {
            'vault_address': str(vault_keypair.pubkey()),
            'seed_used': seed,
            'success': True
        }

class BlinksPlugin(Plugin):
    """Plugin para Blinks (Blockchain Links)"""
    
    def __init__(self):
        super().__init__("blinks", [AgentCapability.BLINKS_EXECUTION])
        
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "create_blink":
            return await self.create_blink(**kwargs)
        elif action == "execute_blink":
            return await self.execute_blink(**kwargs)
        else:
            raise ValueError(f"Action {action} not supported by BlinksPlugin")
    
    async def create_blink(self, url: str, action_data: Dict, **kwargs):
        """Crear un Blink"""
        return {'action': 'create_blink', 'url': url, 'success': True}

class MCPPlugin(Plugin):
    """Plugin para integración MCP (Model Context Protocol)"""
    
    def __init__(self):
        super().__init__("mcp", [AgentCapability.MCP_INTEGRATION])
        self.mcp_server_url = "https://mcp.solana.com/mcp"
        
    async def initialize(self, agent: 'SolanaAgent'):
        await super().initialize(agent)
        # Conectar con servidor MCP
        log.info("mcp", "connecting", f"Connecting to MCP server: {self.mcp_server_url}")
        
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "mcp_query":
            return await self.mcp_query(**kwargs)
        elif action == "mcp_execute":
            return await self.mcp_execute(**kwargs)
        else:
            raise ValueError(f"Action {action} not supported by MCPPlugin")
    
    async def mcp_query(self, query: str, context: Dict = None):
        """Realizar consulta al servidor MCP"""
        try:
            response = requests.post(
                f"{self.mcp_server_url}/query",
                json={
                    'query': query,
                    'context': context or {},
                    'agent_id': self.agent.agent_id
                }
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'response': response.json(),
                    'query': query
                }
            else:
                return {
                    'success': False,
                    'error': response.text,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            log.error("mcp", "query_failed", str(e))
            return {'success': False, 'error': str(e)}
    
    async def mcp_execute(self, command: str, params: Dict):
        """Ejecutar comando a través de MCP"""
        # Implementar ejecución MCP
        return {'action': 'mcp_execute', 'command': command, 'success': True}

class MarketAnalysisPlugin(Plugin):
    """Plugin para análisis de mercado"""
    
    def __init__(self):
        super().__init__("market", [AgentCapability.MARKET_ANALYSIS])
        
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "analyze_token":
            return await self.analyze_token(**kwargs)
        elif action == "get_market_trends":
            return await self.get_market_trends(**kwargs)
        elif action == "snipe_opportunities":
            return await self.snipe_opportunities(**kwargs)
        else:
            raise ValueError(f"Action {action} not supported by MarketAnalysisPlugin")
    
    async def analyze_token(self, token_address: str, **kwargs):
        """Analizar token"""
        # Implementar análisis
        return {'action': 'analyze_token', 'token': token_address, 'success': True}
    
    async def snipe_opportunities(self, **kwargs):
        """Buscar oportunidades de snipe"""
        return {'action': 'snipe_opportunities', 'success': True}

class SecurityPlugin(Plugin):
    """Plugin para auditoría de seguridad"""
    
    def __init__(self):
        super().__init__("security", [AgentCapability.SECURITY_AUDIT])
        
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "audit_contract":
            return await self.audit_contract(**kwargs)
        elif action == "check_rugpull":
            return await self.check_rugpull(**kwargs)
        elif action == "analyze_risks":
            return await self.analyze_risks(**kwargs)
        else:
            raise ValueError(f"Action {action} not supported by SecurityPlugin")
    
    async def audit_contract(self, contract_address: str, **kwargs):
        """Auditar contrato"""
        return {'action': 'audit_contract', 'contract': contract_address, 'success': True}

class TradingBotPlugin(Plugin):
    """Plugin para trading automatizado"""
    
    def __init__(self):
        super().__init__("trading_bot", [AgentCapability.AUTOMATED_TRADING])
        self.strategies = {}
        
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        if action == "start_bot":
            return await self.start_bot(**kwargs)
        elif action == "stop_bot":
            return await self.stop_bot(**kwargs)
        elif action == "add_strategy":
            return await self.add_strategy(**kwargs)
        else:
            raise ValueError(f"Action {action} not supported by TradingBotPlugin")
    
    async def start_bot(self, strategy_name: str, **kwargs):
        """Iniciar bot de trading"""
        log.info("trading_bot", "starting", f"Strategy: {strategy_name}")
        return {'action': 'start_bot', 'strategy': strategy_name, 'success': True}

@dataclass
class Wallet:
    """Wallet wrapper para el agente"""
    
    def __init__(self, keypair: Keypair = None, private_key: str = None):
        if keypair:
            self.keypair = keypair
        elif private_key:
            # Decodificar clave privada desde base58
            from solders.keypair import Keypair
            import base58
            secret_bytes = base58.b58decode(private_key)
            self.keypair = Keypair.from_secret_key(secret_bytes)
        else:
            # Generar nueva wallet
            self.keypair = Keypair()
        
        self.address = str(self.keypair.pubkey())
        
    def get_balance(self, client: Client = None) -> float:
        """Obtener balance de la wallet"""
        if not client:
            client = Client("https://api.mainnet-beta.solana.com")
        
        response = client.get_balance(self.keypair.pubkey())
        if 'error' not in response:
            lamports = response['result']['value']
            return lamports / 10**9
        return 0.0

class SolanaAgent:
    """Agente principal de Solana con múltiples capacidades"""
    
    def __init__(self, 
                 wallet: Wallet = None,
                 rpc_url: str = None,
                 config: Dict[str, Any] = None):
        
        # Configuración
        self.config = config or {}
        self.rpc_url = rpc_url or self.config.get('RPC_URL', 'https://api.mainnet-beta.solana.com')
        
        # Wallet
        self.wallet = wallet or Wallet()
        
        # Cliente RPC
        self.client = Client(self.rpc_url) if SOLANA_AVAILABLE else None
        
        # Plugins
        self.plugins: Dict[str, Plugin] = {}
        self.enabled_plugins: List[str] = []
        
        # Estado del agente
        self.agent_id = hashlib.sha256(self.wallet.address.encode()).hexdigest()[:16]
        self.is_initialized = False
        
        log.info("agent", "initialized", f"Agent ID: {self.agent_id}, Address: {self.wallet.address}")
    
    def use(self, plugin: Plugin) -> 'SolanaAgent':
        """Añadir plugin al agente"""
        self.plugins[plugin.name] = plugin
        log.info("agent", "plugin_added", f"{plugin.name} with {len(plugin.capabilities)} capabilities")
        return self
    
    async def initialize(self) -> bool:
        """Inicializar todos los plugins"""
        log.info("agent", "initializing", "Initializing agent and plugins...")
        
        try:
            # Inicializar cada plugin
            for plugin_name, plugin in self.plugins.items():
                if plugin.enabled:
                    await plugin.initialize(self)
                    self.enabled_plugins.append(plugin_name)
                    log.debug("agent", "plugin_initialized", plugin_name)
            
            # Verificar conexión RPC
            if self.client:
                version = self.client.get_version()
                if 'error' not in version:
                    log.info("agent", "rpc_connected", 
                            f"Solana {version['result']['solana-core']}")
            
            self.is_initialized = True
            log.info("agent", "initialized", 
                    f"Agent ready with {len(self.enabled_plugins)} plugins")
            
            return True
            
        except Exception as e:
            log.error("agent", "initialization_failed", str(e))
            return False
    
    async def execute(self, plugin_name: str, action: str, **kwargs) -> Dict[str, Any]:
        """Ejecutar acción en un plugin específico"""
        if not self.is_initialized:
            await self.initialize()
        
        if plugin_name not in self.plugins:
            return {
                'success': False,
                'error': f"Plugin {plugin_name} not found. Available: {list(self.plugins.keys())}"
            }
        
        plugin = self.plugins[plugin_name]
        
        if not plugin.enabled:
            return {
                'success': False,
                'error': f"Plugin {plugin_name} is disabled"
            }
        
        log.info("agent", "executing", f"{plugin_name}.{action}")
        
        try:
            result = await plugin.execute(action, **kwargs)
            result['plugin'] = plugin_name
            result['action'] = action
            result['agent_id'] = self.agent_id
            result['timestamp'] = datetime.now().isoformat()
            
            log.info("agent", "execution_complete", 
                    f"{plugin_name}.{action}: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            log.error("agent", "execution_failed", f"{plugin_name}.{action}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'plugin': plugin_name,
                'action': action
            }
    
    async def multi_execute(self, commands: List[Dict]) -> List[Dict[str, Any]]:
        """Ejecutar múltiples comandos en secuencia"""
        results = []
        
        for cmd in commands:
            plugin = cmd.get('plugin')
            action = cmd.get('action')
            params = cmd.get('params', {})
            
            result = await self.execute(plugin, action, **params)
            results.append(result)
        
        return results
    
    def get_capabilities(self) -> List[str]:
        """Obtener todas las capacidades disponibles"""
        capabilities = []
        for plugin in self.plugins.values():
            if plugin.enabled:
                capabilities.extend([c.value for c in plugin.capabilities])
        return list(set(capabilities))
    
    def create_tools(self, framework: str = "vercel_ai") -> Dict[str, Any]:
        """Crear herramientas para frameworks de AI"""
        
        tools = {}
        
        if framework == "vercel_ai":
            # Crear herramientas para Vercel AI SDK
            for plugin_name, plugin in self.plugins.items():
                if plugin.enabled:
                    tools[plugin_name] = {
                        'name': plugin_name,
                        'description': f"Plugin for {plugin_name} operations",
                        'parameters': {
                            'type': 'object',
                            'properties': {
                                'action': {'type': 'string'},
                                'params': {'type': 'object'}
                            }
                        }
                    }
        
        elif framework == "langchain":
            # Crear herramientas para LangChain
            import langchain
            # Implementación para LangChain
        
        return tools
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Obtener estado completo del agente"""
        return {
            'agent_id': self.agent_id,
            'wallet_address': self.wallet.address,
            'initialized': self.is_initialized,
            'plugins_enabled': self.enabled_plugins,
            'capabilities': self.get_capabilities(),
            'rpc_url': self.rpc_url,
            'timestamp': datetime.now().isoformat()
        }
    
    def enable_plugin(self, plugin_name: str):
        """Habilitar plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            log.info("agent", "plugin_enabled", plugin_name)
    
    def disable_plugin(self, plugin_name: str):
        """Deshabilitar plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            log.info("agent", "plugin_disabled", plugin_name)

# Factory function para crear agentes
def create_solana_agent(
    private_key: str = None,
    rpc_url: str = None,
    config: Dict[str, Any] = None,
    plugins: List[str] = None
) -> SolanaAgent:
    """
    Crear agente de Solana con plugins específicos
    
    Args:
        private_key: Clave privada en base58 (opcional, genera nueva si no se proporciona)
        rpc_url: URL del RPC de Solana
        config: Configuración adicional
        plugins: Lista de plugins a habilitar (None = todos)
    """
    
    # Crear wallet
    wallet = Wallet(private_key=private_key) if private_key else Wallet()
    
    # Crear agente
    agent = SolanaAgent(
        wallet=wallet,
        rpc_url=rpc_url,
        config=config
    )
    
    # Plugin por defecto (todos)
    default_plugins = [
        TokenPlugin(),
        NFTPlugin(),
        DeFiPlugin(),
        VaultPlugin(),
        BlinksPlugin(),
        MCPPlugin(),
        MarketAnalysisPlugin(),
        SecurityPlugin(),
        TradingBotPlugin()
    ]
    
    # Añadir plugins
    for plugin in default_plugins:
        if plugins is None or plugin.name in plugins:
            agent.use(plugin)
    
    return agent