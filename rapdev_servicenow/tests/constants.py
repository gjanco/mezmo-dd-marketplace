class Config:
    INSTANCE_NAME = "servicenow-mock"
    INSTANCE_NAME_ONLY = {"instance_name": INSTANCE_NAME}
    ONLY_STATSDO = {"instance_name": INSTANCE_NAME, "collect_statsdo": True}

    ITSM_NO_CREDS = {"base_url": INSTANCE_NAME, "collect_itsm_metrics": True}

    INVALID_BOOLS = {
        "instance_name": INSTANCE_NAME,
        "collect_statsdo": "Potato"
    }

    ITSM_WITH_CREDS = {
        "instance_name": INSTANCE_NAME,
        "collect_statsdo": False,
        "collect_itsm_metrics": True,
        "username": "test",
        "password": "test",
    }

    STATSDO_AND_ITSM = {
        "instance_name": INSTANCE_NAME,
        "collect_statsdo": True,
        "collect_itsm_metrics": True,
        "username": "test",
        "password": "test",
    }
