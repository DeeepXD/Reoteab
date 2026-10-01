__all__ = ["BiomeTracker"]


def __getattr__(name):
    if name == "BiomeTracker":
        from .core import BiomeTracker
        return BiomeTracker
    raise AttributeError(name)
