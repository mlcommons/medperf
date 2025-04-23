import yaml


def generate_plan(training_config_path, aggregator_config_path, plan_path):
    with open(training_config_path) as f:
        training_config = yaml.safe_load(f)
    with open(aggregator_config_path) as f:
        aggregator_config = yaml.safe_load(f)

    # TODO: key checks. Also, define what should be considered aggregator_config
    #       (e.g., tls=true, reconnect_interval, ...)
    training_config["network"]["settings"]["agg_addr"] = aggregator_config["address"]
    training_config["network"]["settings"]["agg_port"] = aggregator_config["port"]

    with open(plan_path, "w") as f:
        yaml.dump(training_config, f)
