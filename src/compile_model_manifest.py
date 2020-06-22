import os
import requests
import yaml
import re
import json
from pathlib import Path

compiled_models = []
preserved_keys = [
    "source",
    "model",
    "weights",
    "files",
    "applications",
    "download_url",
    "name",
    "description",
    "cite",
    "authors",
    "documentation",
    "tags",
    "covers",
]
assert "url" not in preserved_keys

models_yaml_file = Path(__file__).parent / "manifest.bioimage.io.yaml"
models_yaml = yaml.safe_load(models_yaml_file.read_text())

compiled_apps = []
for item in models_yaml["applications"]:
    app_url = item["source"]
    if not app_url.startswith("http"):
        app_url = item["source"].strip("/").strip("./")
        app_url = models_yaml["url_root"].strip("/") + "/" + app_url
    compiled_apps.append({"id": item["id"], "type": "application", "source": app_url})

for tp in ["models", "datasets", "notebooks"]:
    for item in models_yaml[tp]:
        
        source = item["source"]
        root_url = "/".join(source.split("/")[:-1])
        response = requests.get(source)
        if response.status_code != 200:
            print("Failed to fetch model config from " + source)
            continue

        model_config = yaml.safe_load(response.content)

        # merge item from models.yaml to model config
        model_config.update(item)
        model_info = {"root_url": root_url, "type": tp[:-1]} # remove `s`
        for k in model_config:
            # normalize relative path
            if k in ["documentation"]:
                if model_config[k]:
                    model_config[k] = model_config[k].strip("/").strip("./")

            if k == "covers":
                for j in range(len(model_config[k])):
                    model_config[k][j] = model_config[k][j].strip("/").strip("./")

            if k in preserved_keys:
                model_info[k] = model_config[k]

        compiled_models.append(model_info)
        compiled_models.sort(key=lambda m: m["name"], reverse=True)

with (Path(__file__).parent / "../manifest.bioimage.io.json").open("wb") as f:
    new_model_yaml = {
        "name": models_yaml["name"],
        "description": models_yaml["description"],
        "version": models_yaml["version"],
        "url_root": models_yaml["url_root"],
    }
    new_model_yaml["resources"] = compiled_apps + compiled_models
    f.write(
        json.dumps(new_model_yaml, indent=2, separators=(",", ": ")).encode("utf-8")
    )
