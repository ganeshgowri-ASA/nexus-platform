"""Modules registry for NEXUS platform."""

from typing import Dict, Type
from core.base_module import BaseModule


def get_available_modules() -> Dict[str, Type[BaseModule]]:
    """
    Get all available modules.

    Returns:
        Dictionary mapping module names to module classes
    """
    from modules.pipeline.module import PipelineModule

    return {
        "pipeline": PipelineModule,
    }


def load_modules() -> Dict[str, BaseModule]:
    """
    Load and instantiate all modules.

    Returns:
        Dictionary of instantiated modules
    """
    modules = {}
    available_modules = get_available_modules()

    for name, module_class in available_modules.items():
        try:
            modules[name] = module_class()
        except Exception as e:
            print(f"Error loading module {name}: {e}")

    return modules
