import os

os.environ["PROMPTGATE_AUTH_TOKEN"] = "local_promptgate_key"
os.environ["PROMPTGATE_PROVIDER_MODE"] = "mock"
os.environ.pop("PROMPTGATE_UPSTREAM_BASE_URL", None)
os.environ.pop("PROMPTGATE_UPSTREAM_API_KEY", None)
os.environ.pop("PROMPTGATE_UPSTREAM_HTTP_PROXY", None)
os.environ.pop("PROMPTGATE_UPSTREAM_CA_BUNDLE", None)
