"""Unit tests for the config module."""

import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

from revoagent.core.config import (
    Config,
    ModelConfig,
    AgentConfig,
    SecurityConfig,
    ResourceConfig,
    PlatformConfig,
    get_config,
    set_config,
)


class TestModelConfig:
    """Test ModelConfig class."""

    def test_model_config_defaults(self):
        """Test ModelConfig with default values."""
        config = ModelConfig(name="test-model")
        assert config.name == "test-model"
        assert config.type == "local"
        assert config.path is None
        assert config.api_key is None
        assert config.base_url is None
        assert config.max_tokens == 4096
        assert config.temperature == 0.0
        assert config.quantization is True
        assert config.context_length == 8192

    def test_model_config_custom_values(self):
        """Test ModelConfig with custom values."""
        config = ModelConfig(
            name="custom-model",
            type="api",
            path="/path/to/model",
            api_key="test-key",
            base_url="https://api.example.com",
            max_tokens=2048,
            temperature=0.7,
            quantization=False,
            context_length=4096
        )
        assert config.name == "custom-model"
        assert config.type == "api"
        assert config.path == "/path/to/model"
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.example.com"
        assert config.max_tokens == 2048
        assert config.temperature == 0.7
        assert config.quantization is False
        assert config.context_length == 4096


class TestAgentConfig:
    """Test AgentConfig class."""

    def test_agent_config_defaults(self):
        """Test AgentConfig with default values."""
        config = AgentConfig()
        assert config.enabled is True
        assert config.model == "local/deepseek-coder"
        assert config.tools == []
        assert config.max_iterations == 50
        assert config.timeout == 300
        assert config.memory_size == 1000

    def test_agent_config_custom_values(self):
        """Test AgentConfig with custom values."""
        config = AgentConfig(
            enabled=False,
            model="custom-model",
            tools=["git", "docker"],
            max_iterations=100,
            timeout=600,
            memory_size=2000
        )
        assert config.enabled is False
        assert config.model == "custom-model"
        assert config.tools == ["git", "docker"]
        assert config.max_iterations == 100
        assert config.timeout == 600
        assert config.memory_size == 2000


class TestSecurityConfig:
    """Test SecurityConfig class."""

    def test_security_config_defaults(self):
        """Test SecurityConfig with default values."""
        config = SecurityConfig()
        assert config.sandbox_enabled is True
        assert config.network_isolation is True
        assert config.file_system_limits is True
        assert config.allowed_domains == []
        assert config.blocked_commands == []
        assert config.max_file_size == 100 * 1024 * 1024


class TestResourceConfig:
    """Test ResourceConfig class."""

    def test_resource_config_defaults(self):
        """Test ResourceConfig with default values."""
        config = ResourceConfig()
        assert config.max_memory_mb == 4096
        assert config.max_cpu_percent == 80.0
        assert config.max_disk_mb == 10240
        assert config.gpu_enabled is False
        assert config.gpu_memory_fraction == 0.8


class TestPlatformConfig:
    """Test PlatformConfig class."""

    def test_platform_config_defaults(self):
        """Test PlatformConfig with default values."""
        config = PlatformConfig()
        assert config.name == "reVoAgent"
        assert config.version == "1.0.0"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.data_dir == "./data"
        assert config.models_dir == "./models"
        assert config.temp_dir == "./temp"


class TestConfig:
    """Test Config class."""

    def test_config_defaults(self):
        """Test Config with default values."""
        config = Config()
        assert isinstance(config.platform, PlatformConfig)
        assert config.models == {}
        assert config.agents == {}
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.resources, ResourceConfig)

    def test_load_default(self):
        """Test loading default configuration."""
        config = Config.load_default()
        
        # Check that default models are loaded
        assert "local/deepseek-coder" in config.models
        assert "local/llama-3.2" in config.models
        
        # Check that default agents are loaded
        assert "code_generator" in config.agents
        assert "browser_agent" in config.agents
        assert "debugging_agent" in config.agents
        assert "testing_agent" in config.agents
        
        # Verify model configurations
        deepseek_model = config.models["local/deepseek-coder"]
        assert deepseek_model.name == "deepseek-coder"
        assert deepseek_model.type == "local"
        assert deepseek_model.quantization is True
        
        # Verify agent configurations
        code_gen_agent = config.agents["code_generator"]
        assert code_gen_agent.enabled is True
        assert code_gen_agent.model == "local/deepseek-coder"
        assert "git" in code_gen_agent.tools

    def test_load_from_file_success(self):
        """Test loading configuration from a valid YAML file."""
        config_data = {
            "platform": {
                "name": "test-platform",
                "debug": True
            },
            "models": {
                "test-model": {
                    "name": "test-model",
                    "type": "api",
                    "api_key": "test-key"
                }
            },
            "agents": {
                "test-agent": {
                    "enabled": False,
                    "model": "test-model"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = Config.load_from_file(temp_path)
            assert config.platform.name == "test-platform"
            assert config.platform.debug is True
            assert "test-model" in config.models
            assert config.models["test-model"].api_key == "test-key"
            assert "test-agent" in config.agents
            assert config.agents["test-agent"].enabled is False
        finally:
            os.unlink(temp_path)

    def test_load_from_file_not_found(self):
        """Test loading configuration from non-existent file."""
        with pytest.raises(FileNotFoundError):
            Config.load_from_file("/non/existent/path.yaml")

    def test_save_to_file(self):
        """Test saving configuration to YAML file."""
        config = Config.load_default()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            config.save_to_file(temp_path)
            
            # Verify file was created and contains expected data
            assert Path(temp_path).exists()
            
            with open(temp_path, 'r') as f:
                saved_data = yaml.safe_load(f)
            
            assert "platform" in saved_data
            assert "models" in saved_data
            assert "agents" in saved_data
            assert saved_data["platform"]["name"] == "reVoAgent"
        finally:
            os.unlink(temp_path)

    def test_get_model_config(self):
        """Test getting model configuration."""
        config = Config.load_default()
        
        # Test existing model
        model_config = config.get_model_config("local/deepseek-coder")
        assert model_config is not None
        assert model_config.name == "deepseek-coder"
        
        # Test non-existent model
        model_config = config.get_model_config("non-existent")
        assert model_config is None

    def test_get_agent_config(self):
        """Test getting agent configuration."""
        config = Config.load_default()
        
        # Test existing agent
        agent_config = config.get_agent_config("code_generator")
        assert agent_config is not None
        assert agent_config.model == "local/deepseek-coder"
        
        # Test non-existent agent
        agent_config = config.get_agent_config("non-existent")
        assert agent_config is None

    def test_validate_paths(self):
        """Test path validation and creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(
                platform=PlatformConfig(
                    data_dir=f"{temp_dir}/data",
                    models_dir=f"{temp_dir}/models",
                    temp_dir=f"{temp_dir}/temp"
                )
            )
            
            # Paths should not exist initially
            assert not Path(f"{temp_dir}/data").exists()
            assert not Path(f"{temp_dir}/models").exists()
            assert not Path(f"{temp_dir}/temp").exists()
            
            # Validate paths should create them
            config.validate_paths()
            
            assert Path(f"{temp_dir}/data").exists()
            assert Path(f"{temp_dir}/models").exists()
            assert Path(f"{temp_dir}/temp").exists()

    @patch('builtins.print')
    def test_validate_models_missing_file(self, mock_print):
        """Test model validation with missing model file."""
        # Create a config with a non-existent model file
        # The validation happens during config creation
        config = Config(
            models={
                "test-model": ModelConfig(
                    name="test-model",
                    type="local",
                    path="/non/existent/model.gguf"
                )
            }
        )
        
        # Verify warning was printed during config creation
        mock_print.assert_called()
        # Check that at least one call contains the warning message
        warning_found = any("Warning: Model file not found" in str(call) for call in mock_print.call_args_list)
        assert warning_found


class TestGlobalConfig:
    """Test global configuration functions."""

    def setUp(self):
        """Reset global config before each test."""
        # Reset the global config
        import revoagent.core.config
        revoagent.core.config._config = None

    def test_get_config_default(self):
        """Test getting default configuration when no file exists."""
        self.setUp()
        
        with patch.dict(os.environ, {"REVOAGENT_CONFIG": "/non/existent/config.yaml"}):
            with patch('builtins.print') as mock_print:
                config = get_config()
                
                assert isinstance(config, Config)
                assert config.platform.name == "reVoAgent"
                
                # Should print message about using defaults
                mock_print.assert_called()
                # Check that at least one call contains the expected message
                defaults_found = any("using defaults" in str(call) for call in mock_print.call_args_list)
                assert defaults_found

    def test_get_config_from_file(self):
        """Test getting configuration from file."""
        self.setUp()
        
        config_data = {
            "platform": {"name": "test-from-file"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            with patch.dict(os.environ, {"REVOAGENT_CONFIG": temp_path}):
                config = get_config()
                assert config.platform.name == "test-from-file"
        finally:
            os.unlink(temp_path)

    def test_get_config_cached(self):
        """Test that get_config returns cached instance."""
        self.setUp()
        
        config1 = get_config()
        config2 = get_config()
        
        # Should return the same instance
        assert config1 is config2

    def test_set_config(self):
        """Test setting global configuration."""
        self.setUp()
        
        custom_config = Config(
            platform=PlatformConfig(name="custom-platform")
        )
        
        set_config(custom_config)
        
        retrieved_config = get_config()
        assert retrieved_config is custom_config
        assert retrieved_config.platform.name == "custom-platform"

    def test_get_config_validates_paths(self):
        """Test that get_config calls validate_paths."""
        self.setUp()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {
                "platform": {
                    "data_dir": f"{temp_dir}/data",
                    "models_dir": f"{temp_dir}/models",
                    "temp_dir": f"{temp_dir}/temp"
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config_data, f)
                temp_path = f.name
            
            try:
                with patch.dict(os.environ, {"REVOAGENT_CONFIG": temp_path}):
                    get_config()
                    
                    # Paths should have been created
                    assert Path(f"{temp_dir}/data").exists()
                    assert Path(f"{temp_dir}/models").exists()
                    assert Path(f"{temp_dir}/temp").exists()
            finally:
                os.unlink(temp_path)