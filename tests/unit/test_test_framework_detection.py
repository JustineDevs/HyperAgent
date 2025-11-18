"""Unit tests for test framework auto-detection"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import subprocess
import shutil
from hyperagent.agents.testing import TestingAgent
from hyperagent.events.event_bus import EventBus


class TestTestFrameworkDetection:
    """Test test framework auto-detection"""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus"""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def testing_agent(self, mock_event_bus):
        """Create TestingAgent instance"""
        return TestingAgent(mock_event_bus)
    
    def test_detect_foundry_when_available(self, testing_agent, monkeypatch):
        """Test Foundry detection when forge is available"""
        # Mock shutil.which to return forge path
        monkeypatch.setattr(shutil, 'which', lambda cmd: '/usr/bin/forge' if cmd == 'forge' else None)
        
        framework = testing_agent._detect_test_framework()
        assert framework == "foundry"
    
    def test_detect_hardhat_via_config_file(self, testing_agent, monkeypatch, tmp_path):
        """Test Hardhat detection via config file"""
        # Create hardhat.config.js
        config_file = tmp_path / "hardhat.config.js"
        config_file.write_text("module.exports = {};")
        
        # Mock shutil.which to return None for forge
        monkeypatch.setattr(shutil, 'which', lambda cmd: None)
        
        framework = testing_agent._detect_test_framework(project_path=tmp_path)
        assert framework == "hardhat"
    
    def test_detect_hardhat_via_npx(self, testing_agent, monkeypatch):
        """Test Hardhat detection via npx"""
        # Mock shutil.which
        def mock_which(cmd):
            if cmd == "forge":
                return None
            elif cmd == "npx":
                return "/usr/bin/npx"
            return None
        
        monkeypatch.setattr(shutil, 'which', mock_which)
        
        # Mock subprocess.run to return success
        mock_run = MagicMock()
        mock_run.returncode = 0
        monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: mock_run)
        
        framework = testing_agent._detect_test_framework()
        assert framework == "hardhat"
    
    def test_detect_no_framework_raises_error(self, testing_agent, monkeypatch):
        """Test that ValueError is raised when no framework is found"""
        # Mock shutil.which to return None
        monkeypatch.setattr(shutil, 'which', lambda cmd: None)
        
        # Mock Path.exists to return False
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(ValueError, match="No test framework found"):
                testing_agent._detect_test_framework()
    
    def test_auto_detection_on_init(self, mock_event_bus, monkeypatch):
        """Test that framework is auto-detected on TestingAgent init"""
        from hyperagent.core.config import settings
        
        # Mock settings
        with patch.object(settings, 'test_framework_auto_detect', True):
            # Mock Foundry available
            monkeypatch.setattr(shutil, 'which', lambda cmd: '/usr/bin/forge' if cmd == 'forge' else None)
            
            agent = TestingAgent(mock_event_bus)
            assert agent.test_framework == "foundry"
    
    def test_fallback_to_hardhat_on_detection_failure(self, mock_event_bus, monkeypatch):
        """Test fallback to hardhat when detection fails"""
        from hyperagent.core.config import settings
        
        with patch.object(settings, 'test_framework_auto_detect', True):
            # Mock no framework found
            monkeypatch.setattr(shutil, 'which', lambda cmd: None)
            with patch('pathlib.Path.exists', return_value=False):
                # Should fallback to hardhat
                agent = TestingAgent(mock_event_bus)
                assert agent.test_framework == "hardhat"

