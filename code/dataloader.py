from PIL import Image
import numpy as np
import os
import argparse
import glob
import time
import pickle
import pyflann
from tqdm import tqdm


import torch
from torchvision import transforms

from utils import save_data


def data_loader(args, reshape_size):
	img_transform = transforms.Compose([
	    transforms.Resize((reshape_size[1],reshape_size[1])),
	    transforms.ToTensor()
	])	
	 	
	# wireframe image  - MAY NEED MODIFIED
	wfile_list = glob.glob(args.data_root + "/**/target/**.png", recursive = True)
	# original ui - MAY NEED MODIFIED
	sfile_list = [name.replace("target", "source") for name in wfile_list]

	print('file_list[0]:',wfile_list[0])
							
	# torchlist: transform database images into vector
	torchlist = []	
	for i in tqdm(range(len(wfile_list))):
		#print(file_list[i])
		imgtest = Image.open(wfile_list[i])
		imgtest = imgtest.resize((reshape_size[0],reshape_size[1]), Image.ANTIALIAS)

		combine_img = Image.new('RGB', (reshape_size[1],reshape_size[1]), (255,255,255))
		combine_img.paste(imgtest, (0,0))

		img = img_transform(combine_img)
		torchlist.append(img)
	torchlist = (torch.stack(torchlist)).data.numpy()
	
	save_data([sfile_list, wfile_list, torchlist], args.cache_root)
	print('Finished!')	

	return torchlist