import random

DEFAULT_IMAGE_PARAMS = {
    "prompt": "",  # This will be overwritten in generate_image
    "params": {
        "sampler_name": "k_dpmpp_2m",
        "cfg_scale": 4.5,
        "denoising_strength": 0.75,
        "seed": None,
        "height": 1024,
        "width": 1024,
        "steps": 22,
        "n": 1
    },
    "nsfw": False,
    "karras": True,
    "trusted_workers": False,
    "slow_workers": True,
    "censor_nsfw": False,
    "r2": True,
    "shared": False,
    "replacement_filter": True,
    "models": ["AIPG_RED"]
}

MAX_WAIT_TIME = 300  # 5 minutes
CHECK_INTERVAL = 5  # 5 seconds