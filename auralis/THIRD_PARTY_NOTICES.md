# Third-party components

Application source: MIT, see LICENSE. Model weights are not bundled. API access is governed by the provider's terms and quotas, independently of model licensing.

- GPT-OSS-20B: OpenAI, Apache 2.0. https://huggingface.co/openai/gpt-oss-20b
- Whisper: OpenAI, MIT. https://github.com/openai/whisper
- Groq: hosted inference service, not an open-source dependency. https://console.groq.com/docs
- Browser SpeechSynthesis and optional browser speech recognition: browser/OS services, not claimed as open-weight models. Browser recognition can send audio to the browser vendor.
- FastAPI: MIT. https://github.com/fastapi/fastapi
- Uvicorn: BSD-3-Clause. https://github.com/encode/uvicorn
- HTTPX: BSD-3-Clause. https://github.com/encode/httpx
- Pydantic: MIT. https://github.com/pydantic/pydantic
- python-multipart: Apache 2.0. https://github.com/Kludex/python-multipart
- pypdf: BSD-3-Clause. https://github.com/py-pdf/pypdf
- python-docx: MIT. https://github.com/python-openxml/python-docx
- python-dotenv: BSD-3-Clause. https://github.com/theskumar/python-dotenv
- pytest: MIT. https://github.com/pytest-dev/pytest
- REA: optional external MIT-licensed toolkit, not bundled or copied. https://github.com/morluto/rea

Development used ChatGPT/Codex for implementation, documentation, and tests. Verify current licenses and provider availability before redistribution or deployment. Dependency packages retain their original license files when installed.


### Hugging Face Inference Providers (optional inference service)

Hosted service accessed by HTTPS using the user's Hugging Face token. Model weights
are those of OpenAI GPT-OSS, distributed under Apache 2.0. Model providers and
Hugging Face have independent service terms, pricing, quotas and data policies.
No model weights, commercial voice services, or Hugging Face SDK are redistributed
by this ZIP.
