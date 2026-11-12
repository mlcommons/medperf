"""Stands in for torchcodec when vLLM starts (infer.py puts this folder first
on vLLM's PYTHONPATH). The arm64 build of vllm/vllm-openai:v0.31.0-cu129 has a
torchcodec compiled for CUDA 13, which fails to load in its CUDA 12.9 image
(OSError: libnvrtc.so.13). vLLM imports torchcodec at startup, for audio and
video inputs only, and skips it if the import raises ImportError, as here."""

raise ImportError("torchcodec is disabled in this image: its arm64 build needs CUDA 13")
