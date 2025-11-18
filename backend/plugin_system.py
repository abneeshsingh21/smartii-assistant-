"""
SMARTII Plugin System
Extensible architecture for adding custom functionality
"""

import importlib
import os
import json
from typing import Dict, List, Any, Callable
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Plugin:
    """Base class for all SMARTII plugins"""
    
    def __init__(self):
        self.name = "BasePlugin"
        self.version = "1.0.0"
        self.description = "Base plugin class"
        self.commands = {}
        self.enabled = True
        
    async def initialize(self):
        """Called when plugin is loaded"""
        pass
        
    async def shutdown(self):
        """Called when plugin is unloaded"""
        pass
        
    def register_command(self, command: str, handler: Callable):
        """Register a command handler"""
        self.commands[command] = handler
        
    async def handle_command(self, command: str, params: Dict) -> Any:
        """Handle a command"""
        if command in self.commands:
            return await self.commands[command](params)
        return {"error": f"Unknown command: {command}"}


class PluginManager:
    """Manages all plugins"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_metadata: Dict[str, Dict] = {}
        
        # Create plugins directory if it doesn't exist
        Path(plugin_dir).mkdir(exist_ok=True)
        
    async def load_plugins(self):
        """Load all plugins from plugin directory"""
        plugin_path = Path(self.plugin_dir)
        
        for plugin_file in plugin_path.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
                
            try:
                await self._load_plugin(plugin_file)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file.name}: {e}")
                
    async def _load_plugin(self, plugin_file: Path):
        """Load a single plugin"""
        module_name = plugin_file.stem
        
        try:
            # Import the plugin module
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for Plugin class
            if hasattr(module, 'Plugin'):
                plugin_class = getattr(module, 'Plugin')
                plugin_instance = plugin_class()
                
                # Initialize plugin
                await plugin_instance.initialize()
                
                # Store plugin
                self.plugins[module_name] = plugin_instance
                
                # Store metadata
                self.plugin_metadata[module_name] = {
                    "name": plugin_instance.name,
                    "version": plugin_instance.version,
                    "description": plugin_instance.description,
                    "commands": list(plugin_instance.commands.keys()),
                    "enabled": plugin_instance.enabled
                }
                
                logger.info(f"Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
                
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_file.name}: {e}")
            raise
            
    async def execute_plugin_command(self, plugin_name: str, command: str, params: Dict = None) -> Any:
        """Execute a command from a specific plugin"""
        if plugin_name not in self.plugins:
            return {"error": f"Plugin '{plugin_name}' not found"}
            
        plugin = self.plugins[plugin_name]
        
        if not plugin.enabled:
            return {"error": f"Plugin '{plugin_name}' is disabled"}
            
        if params is None:
            params = {}
            
        try:
            return await plugin.handle_command(command, params)
        except Exception as e:
            logger.error(f"Plugin command error: {e}")
            return {"error": str(e)}
            
    def get_plugin_info(self, plugin_name: str) -> Dict:
        """Get information about a specific plugin"""
        if plugin_name in self.plugin_metadata:
            return self.plugin_metadata[plugin_name]
        return {"error": f"Plugin '{plugin_name}' not found"}
        
    def list_plugins(self) -> List[Dict]:
        """List all loaded plugins"""
        return list(self.plugin_metadata.values())
        
    async def enable_plugin(self, plugin_name: str) -> Dict:
        """Enable a plugin"""
        if plugin_name not in self.plugins:
            return {"error": f"Plugin '{plugin_name}' not found"}
            
        self.plugins[plugin_name].enabled = True
        self.plugin_metadata[plugin_name]["enabled"] = True
        
        return {"success": True, "message": f"Plugin '{plugin_name}' enabled"}
        
    async def disable_plugin(self, plugin_name: str) -> Dict:
        """Disable a plugin"""
        if plugin_name not in self.plugins:
            return {"error": f"Plugin '{plugin_name}' not found"}
            
        self.plugins[plugin_name].enabled = False
        self.plugin_metadata[plugin_name]["enabled"] = False
        
        return {"success": True, "message": f"Plugin '{plugin_name}' disabled"}
        
    async def reload_plugin(self, plugin_name: str) -> Dict:
        """Reload a plugin"""
        if plugin_name not in self.plugins:
            return {"error": f"Plugin '{plugin_name}' not found"}
            
        # Shutdown old instance
        await self.plugins[plugin_name].shutdown()
        
        # Find plugin file
        plugin_file = Path(self.plugin_dir) / f"{plugin_name}.py"
        
        if not plugin_file.exists():
            return {"error": f"Plugin file '{plugin_file}' not found"}
            
        try:
            # Reload plugin
            await self._load_plugin(plugin_file)
            return {"success": True, "message": f"Plugin '{plugin_name}' reloaded"}
        except Exception as e:
            return {"error": f"Failed to reload plugin: {str(e)}"}
            
    async def unload_all_plugins(self):
        """Unload all plugins"""
        for plugin_name, plugin in self.plugins.items():
            try:
                await plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_name}: {e}")
                
        self.plugins.clear()
        self.plugin_metadata.clear()

# Global plugin manager
plugin_manager = PluginManager()

async def initialize_plugins():
    """Initialize plugin system"""
    await plugin_manager.load_plugins()

async def execute_plugin(plugin_name: str, command: str, params: Dict = None) -> Any:
    """Execute a plugin command"""
    return await plugin_manager.execute_plugin_command(plugin_name, command, params)

def get_available_plugins() -> List[Dict]:
    """Get list of available plugins"""
    return plugin_manager.list_plugins()
