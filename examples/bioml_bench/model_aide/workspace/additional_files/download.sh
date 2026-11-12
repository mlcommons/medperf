# Downloads the LLM's weights (Qwen2.5-Coder-7B-Instruct, about 15 GB) into
# ./Qwen2.5-Coder-7B-Instruct, the folder named by `llm.weights` in parameters.yaml
repo=Qwen/Qwen2.5-Coder-7B-Instruct
revision=c03e6d358207e414f1eca0bb1891e29f1db0e242
folder=Qwen2.5-Coder-7B-Instruct
files="LICENSE config.json generation_config.json merges.txt tokenizer.json tokenizer_config.json vocab.json
model.safetensors.index.json model-00001-of-00004.safetensors model-00002-of-00004.safetensors
model-00003-of-00004.safetensors model-00004-of-00004.safetensors"

mkdir -p $folder
for file in $files; do
    url=https://huggingface.co/$repo/resolve/$revision/$file
    if [ -x "$(which wget)" ] ; then
        wget -c -O $folder/$file $url
    elif [ -x "$(which curl)" ]; then
        curl -L -C - -o $folder/$file $url
    fi
done
