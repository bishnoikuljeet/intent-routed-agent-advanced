"""
Verification script to check if the installation is complete and correct
"""
import sys
from pathlib import Path
import importlib.util


def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    if sys.version_info < (3, 11):
        print(f"  ✗ Python 3.11+ required. Current: {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"  ✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_directories():
    """Check if required directories exist"""
    print("\nChecking directory structure...")
    required_dirs = [
        "app/agents",
        "app/api",
        "app/core",
        "app/graph",
        "app/language",
        "app/mcp",
        "app/memory",
        "app/rag",
        "app/registry",
        "app/schemas",
        "app/services",
        "cli",
        "tests",
        "scripts"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - MISSING")
            all_exist = False
    
    return all_exist


def check_files():
    """Check if key files exist"""
    print("\nChecking key files...")
    required_files = [
        "main.py",
        "pyproject.toml",
        ".env.example",
        "README.md",
        "QUICKSTART.md",
        "ARCHITECTURE.md",
        "app/__init__.py",
        "app/agents/coordinator.py",
        "app/agents/intent.py",
        "app/agents/planner.py",
        "app/agents/executor.py",
        "app/agents/aggregator.py",
        "app/agents/reasoning.py",
        "app/agents/evaluation.py",
        "app/agents/answer.py",
        "app/api/app.py",
        "app/api/routes.py",
        "app/core/config.py",
        "app/core/logging.py",
        "app/graph/workflow.py",
        "app/language/processor.py",
        "app/mcp/base.py",
        "app/mcp/observability_server.py",
        "app/mcp/knowledge_server.py",
        "app/mcp/language_server.py",
        "app/mcp/utility_server.py",
        "app/mcp/system_server.py",
        "app/memory/manager.py",
        "app/memory/vector_store.py",
        "app/rag/retriever.py",
        "app/registry/tool_registry.py",
        "app/schemas/models.py",
        "app/schemas/state.py",
        "app/services/orchestrator.py",
        "cli/cli.py",
        "tests/conftest.py",
        "tests/test_agents.py",
        "tests/test_mcp_servers.py",
        "tests/test_memory.py",
        "tests/test_language.py",
        "tests/test_registry.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - MISSING")
            all_exist = False
    
    return all_exist


def check_imports():
    """Check if key modules can be imported"""
    print("\nChecking module imports...")
    modules = [
        "app.core.config",
        "app.core.logging",
        "app.schemas.models",
        "app.schemas.state",
        "app.agents.coordinator",
        "app.agents.intent",
        "app.mcp.base",
        "app.registry.tool_registry",
        "app.services.orchestrator"
    ]
    
    all_importable = True
    for module_name in modules:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                print(f"  ✓ {module_name}")
            else:
                print(f"  ✗ {module_name} - NOT FOUND")
                all_importable = False
        except Exception as e:
            print(f"  ✗ {module_name} - ERROR: {str(e)}")
            all_importable = False
    
    return all_importable


def check_env_file():
    """Check if .env file exists"""
    print("\nChecking environment configuration...")
    if Path(".env").exists():
        print("  ✓ .env file exists")
        return True
    else:
        print("  ⚠ .env file not found (copy from .env.example)")
        return False


def count_components():
    """Count project components"""
    print("\nProject Statistics:")
    
    # Count agents
    agent_files = list(Path("app/agents").glob("*.py"))
    agent_count = len([f for f in agent_files if f.name != "__init__.py"])
    print(f"  • Agents: {agent_count}")
    
    # Count MCP servers
    mcp_files = list(Path("app/mcp").glob("*_server.py"))
    print(f"  • MCP Servers: {len(mcp_files)}")
    
    # Count test files
    test_files = list(Path("tests").glob("test_*.py"))
    print(f"  • Test Files: {len(test_files)}")
    
    # Count total Python files
    py_files = list(Path(".").rglob("*.py"))
    py_files = [f for f in py_files if "venv" not in str(f) and ".venv" not in str(f)]
    print(f"  • Total Python Files: {len(py_files)}")
    
    # Count documentation files
    doc_files = list(Path(".").glob("*.md"))
    print(f"  • Documentation Files: {len(doc_files)}")


def main():
    print("=" * 70)
    print("Intent Routed Agent Advanced - Installation Verification")
    print("=" * 70)
    print()
    
    checks = []
    
    checks.append(("Python Version", check_python_version()))
    checks.append(("Directory Structure", check_directories()))
    checks.append(("Key Files", check_files()))
    checks.append(("Module Imports", check_imports()))
    checks.append(("Environment File", check_env_file()))
    
    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    for check_name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{check_name:.<50} {status}")
    
    count_components()
    
    print("\n" + "=" * 70)
    
    all_passed = all(result for _, result in checks[:-1])  # Exclude env file from critical checks
    
    if all_passed:
        print("✓ Installation verification PASSED!")
        print("\nNext steps:")
        print("1. Configure .env file with your API keys")
        print("2. Install dependencies: pip install -e .")
        print("3. Run tests: pytest tests/ -v")
        print("4. Start API: python main.py")
        print("5. Or run CLI: python cli/cli.py")
    else:
        print("✗ Installation verification FAILED!")
        print("\nPlease fix the issues above before proceeding.")
        sys.exit(1)
    
    print("=" * 70)


if __name__ == "__main__":
    main()
