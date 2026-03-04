#Python load_screener_csv

import yaml

def load_bot_config(bot_name: str, config_path="bots_config.yaml"):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    if bot_name not in config["bots"]:
        raise ValueError(f"Bot {bot_name} not found in config")
    return config["bots"][bot_name]

if __name__ == "__main__":
    titan_cfg = load_bot_config("Titan_Bot")
    vega_cfg = load_bot_config("Vega_Bot")

    print("Titan config:", titan_cfg)
    print("Vega config:", vega_cfg)
