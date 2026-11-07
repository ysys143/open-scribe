from src.core.speech.adapters import REGISTRY

def main():
    for spec in REGISTRY.values():print(f'{spec.model}\tdiarization={spec.diarization}\tdefault={spec.default_provider}')
    return 0
