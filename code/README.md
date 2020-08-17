# Code for Wireframe-based UI Design Search Through Image Autoencoder

## Structure

|_ \*\*.py: source code

|_ train_data: toy training data

|_ test_data: toy testing data


## Image Preprocessing

use *wirification.py*

This code is implemented using PyThon2

Please read and modify it as you need by yourself.


## Model Training and Testing

To use this code in your dataset, you may need to modify the *dataloader.py* to read your wireframe/source uis. 
You could first use the toy sample to be familier with the input/output.

### Requirement
```
python3 -m pip install -r requirements.txt
```

### Training

```
python3 train.py \
--data_root "train_data" \
--cache_root "results/run/cache" \
--model_dir "results/run" \
--epochs 10

```


### Testing

```
python3 test.py \
--data_root "." \
--cache_root "results/run/cache" \
--model_dir "results/run" \
--checkpoint "results/run/state_dict_final.pth" \
--use_flann 0 \
--test_dir "test_data" \
--result_dir "results/test_result" \
```

*See more options in opts.py*


