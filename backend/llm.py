"""
LLM interface for JobFit.

Single abstracted call — swap models by editing llm_config.json only.
llama-cpp-python is imported lazily so the module loads in environments
where it is not installed (e.g. CI / unit tests).  Tests patch call_llm.
"""
import json
import os

_llm = None  # lazy-loaded singleton


def get_llm():
    """Return the llama-cpp Llama instance, loading it on first call."""
    global _llm
    if _llm is None:
        config_path = os.environ.get("LLM_CONFIG_PATH", "llm_config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"llm_config.json not found at {config_path}")
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        from llama_cpp import Llama  # lazy import — requires CUDA build
        _llm = Llama(
            model_path=config["model_path"],
            n_ctx=config.get("n_ctx", 4096),
            n_gpu_layers=config.get("n_gpu_layers", -1),
            temperature=config.get("temperature", 0.3),
        )
    return _llm


def call_llm(prompt: str, max_tokens: int = 256) -> str:
    """Send *prompt* to the loaded model and return the generated text."""
    llm = get_llm()
    response = llm(prompt, max_tokens=max_tokens, stop=["\n\n"])
    return response["choices"][0]["text"].strip()
