import yaml
import argparse


def update_yaml(yaml_path, new_folder):
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)

    for key in data['storage']:
        if key.endswith('_folder'):
            data['storage'][key] = new_folder

    # Write the updated data back to the YAML file
    with open(yaml_path, 'w') as file:
        yaml.safe_dump(data, file)

    print("Config file storage updated successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update YAML file storage paths.")
    parser.add_argument("yaml_path", type=str, help="The path to the YAML file to update.")
    parser.add_argument("new_folder", type=str, help="The new folder path to set for storage keys.")
    args = parser.parse_args()

    update_yaml(args.yaml_path, args.new_folder)
