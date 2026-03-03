# ollama-to-lmstudio-bridge.py

# btw if you use this script, update the directories and stuff cuz idk they might not work for you

# also this was designed for Ubuntu/Linux, so it'll need to be updated to work on Windows

from pathlib import Path
import json
import os
import sys

def get_manifests_directory():
	# update this depending on OS
	ollama_manifests_dir = f"{Path.home()}/.ollama/models/manifests"

	return ollama_manifests_dir


def extract_manifest_from_model_dir(model_dir):

	manifest_file_location = ""

	for file in os.listdir(model_dir):
		if file in ["cloud", "latest"]:

			continue # skips current file

		manifest_file_location = model_dir+"/"+file

		break # just break in case there are other file types idk


	if manifest_file_location:
		model_dict = parse_manifest(model_dir, manifest_file_location)

		return model_dict

	return None # return nothing if no valid manifest file found


def scan_manifests_dirs(base_dir):

	# a list of dicts for each model containing keys: model_name, and blob_file
	manifests = []

	# find the layers key and get the digest. this is the .gguf file. also note the author name and the model name

	# get immediate sub dirs
	immediate_dirs = os.listdir(base_dir)


	# TODO change this stupid approach lol

	for im_dir in immediate_dirs:
		if im_dir == "registry.ollama.ai":
			# go to library -> model dir -> model file -> library dir and repeat for all model dirs
			print("Found models in 'registry.ollama.ai' directory!")

			for model_dir in os.listdir(base_dir+"/registry.ollama.ai/library"):

				model_dict = extract_manifest_from_model_dir(base_dir+"/registry.ollama.ai/library/"+model_dir)

				if model_dict:
					manifests.append(model_dict)


		elif im_dir == "hf.co":
			print("Found models in 'hf.co' directory!")

			# go to author dir -> model dir -> model file -> back to author dir and repeat for all authors
			for author_dir in os.listdir(base_dir + "/hf.co"):
				for model_dir in os.listdir(base_dir + "/hf.co/" + author_dir):

					model_dict = extract_manifest_from_model_dir(base_dir+ "/hf.co/" +author_dir+"/"+model_dir)

					if model_dict:
						manifests.append(model_dict)

		else:
			# unknown source, os.walk the entire tree and only keep the end of trees? (skip for now)
			print("Unknown source, skipping...")
			pass

	return manifests

def parse_manifest(model_dir, manifest_file):
	with open(manifest_file, "r") as f:

		manifest_as_json = json.load(f)

		blob_file = ""

		for layer in manifest_as_json["layers"]:
			if layer["mediaType"].endswith("model"):
				blob_file = layer["digest"]

		model_dict = {
			"model_name": model_dir.split("/")[-1],
			"blob_file": blob_file.replace(":", "-")
		}

		if model_dict:
			return model_dict

		return None


def create_symlinks(manifests, overwrite=False):
	origin_path = f"{Path.home()}/.ollama/models/blobs"
	destination_path = f"{Path.home()}/.lmstudio/models/lmstudio/test.ollama.ai/library/"

	# create dir for model if path doesn't exist
	if not os.path.exists(destination_path):
		os.makedirs(destination_path)
		print(f"Created file path: {destination_path}")

	# this does NOT properly load the quant type into LM Studio (which apparently isn't done automatically when LM Studio loads the .gguf file idk)
	for model in manifests:
		model_dest_dir = destination_path + model["model_name"] + "/"
		model_dest_file = model_dest_dir + model["model_name"]+".gguf"
		blob_origin_path = origin_path + "/" + model["blob_file"]

		if not os.path.exists(model_dest_dir):
			print(f"Created file path: {model_dest_dir}")
			os.mkdir(model_dest_dir)

		# create symlinks if they don't exist already		
		if not os.path.isfile(model_dest_file):
			os.symlink(blob_origin_path, model_dest_file)
			print(f"Created symlink for {model["model_name"]}!")

		# if overwrite:
		# 	pass

			# clear destination path,


			# then create symlinks



def main():
	# first get the manifest directory
	base_dir = get_manifests_directory()

	# then get the manifest files and their metadata
	manifests = scan_manifests_dirs(base_dir)

	# # finally create the symlinks
	create_symlinks(manifests)

	print("Finished!")


if __name__ == '__main__':
	main()