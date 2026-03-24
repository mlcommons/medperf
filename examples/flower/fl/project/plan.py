import yaml


def generate_plan(training_config_path, aggregator_config_path, plan_path):
    with open(training_config_path) as f:
        training_config = yaml.safe_load(f)
    with open(aggregator_config_path) as f:
        aggregator_config = yaml.safe_load(f)

    plan = {"config": training_config, "aggregator": aggregator_config}

    with open(plan_path, "w") as f:
        yaml.dump(plan, f)
