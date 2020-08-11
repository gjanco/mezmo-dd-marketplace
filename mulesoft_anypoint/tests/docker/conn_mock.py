INSTANCE = {
    "threads": 16,
    "min_collection_interval": 60,
}

INSTANCE2 = {
    "threads": 16,
    "min_collection_interval": 60,
    "api_filter": ["cloudhub"],
}

INSTANCE3 = {
    "threads": 16,
    "min_collection_interval": 60,
    "api_filter": ["access_management"],
}

INSTANCE4 = {
    "threads": 16,
    "min_collection_interval": 60,
}

INIT_CONFIG = {
    "hosts": {
        "anypoint": "http://{}:8000",
        "object_store_v2": "http://{}:8000",
        "object_store_v2_stats": "http://{}:8000",
        "mule_server": "http://{}:8000",
        "oauth_provider": "http://{}:8000/accounts/api/v2/oauth2/token",
    },
    "client_id": 12345,
    "client_secret": 23456,
    "env_id": "env00000-0000-0000-0000-000000000000",
    "org_id": "org00000-0000-0000-0000-000000000000",
    "threads": 16,
    "app_env": "TEST",
    "api_key": "jhhHuhHuhJHjhhknkfffgyglkmlkMLl8j88gff7g",
    "customer_key": "3dfg3fgf-f356-5426-dcc5-584585r58re6",
    "connection_wait_time": 2,
    "connection_attempts_num": 3,
    "min_collection_interval": 60,
}

OK_TOKEN_RESPONSE = {
    "access_token": "00000000-0000-0000-0000-000000000000",
    "token_type": "bearer",
}

KO_APPS_RESPONSE = {
    "error": "Unauthorized",
    "message": "Failed to create session using the supplied Authorization header",
}
