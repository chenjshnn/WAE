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
from torch import nn, optim
from torch.nn import functional as F
from torchvision import transforms
from torch.utils.data import DataLoader
from torch.autograd import Variable
from tensorboardX import SummaryWriter

from Model_AE2 import AE, loss_function
from opts import get_opt
from dataloader import data_loader



args = get_opt()
args.cuda = not args.no_cuda and torch.cuda.is_available()
device = torch.device("cuda" if args.cuda else "cpu")

# reshape_size = [140,224]
reshape_size = [180,288]


def train(model, train_loader):
	torch.manual_seed(args.seed)
	writer = SummaryWriter(log_dir=args.model_dir)

	optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
	lr_scheduler = optim.lr_scheduler.StepLR(optimizer, gamma = 0.98, step_size=50)

	numImg = len(train_loader.dataset)
	numBatch = len(train_loader)

	for epoch in range(args.epochs):
		train_loss = 0.0
		epoch_time = time.clock()
		for batch_idx, img in enumerate(train_loader,0):
			train_time = time.clock()

			img = img.to(device)
			optimizer.zero_grad()
			recon_batch  = model(img)

			print(recon_batch.shape, img.shape)
			loss = loss_function(recon_batch[:,:,0:reshape_size[0],:], img[:,:,0:reshape_size[0],:])
			loss.backward()
			train_loss += loss.item()
			optimizer.step()
			lr_scheduler.step()

			writer.add_scalar("Loss/iter", loss.item() / len(img), batch_idx + epoch * numBatch)

		writer.add_scalar("Loss/epoch", train_loss/numImg, epoch)

		if epoch != 0 and epoch % args.save_model_interval == 0:
			torch.save(model.state_dict(), os.path.join(args.result_dir,'state_dict_{}.pth'.format(epoch)))
			torch.save(model, os.path.join(args.result_dir,"model_{}.pt".format(epoch)))
				
		# if train_loss/len(train_loader.dataset) < 100:
		# 	break
		
	torch.save(model.state_dict(), os.path.join(args.model_dir,'state_dict_final.pth'))
	torch.save(model, os.path.join(args.model_dir,"model_final.pt"))



if __name__ == '__main__':
	if not os.path.exists(args.model_dir):
	    os.makedirs(args.model_dir)
	if not os.path.exists(args.cache_root):
	    os.makedirs(args.cache_root)
	
	# load data
	torchlist = data_loader(args, reshape_size)
	train_loader = DataLoader(torchlist,batch_size=args.batch_size,shuffle=True,num_workers=4)

	# set model
	model = AE().to(device)
	model.train()
	if os.path.exists(args.checkpoint):
		model.load_state_dict(torch.load(args.checkpoint))

	print("==> Start training")
	train(model, train_loader)


	###
	print("==> Computing all latent vectors using the trained model")
	model.eval()


	# compute all latent vectors
	train_loader = DataLoader(torchlist, batch_size = args.batch_size,shuffle = False,num_workers= 4)


	# get the dimension of latent vector
	tmp = list(train_loader)[0].to(device)
	latent_vectors = model(tmp)
	middle_size = len(latent_vectors[0])
	print('middle_size:',middle_size)

	database_middle = np.zeros((len(torchlist),middle_size))
	for j,batch in enumerate(tqdm(train_loader)):
		batch = batch.to(device)
		latent_vectors = model(batch)

		left = j*args.batch_size
		right = min((j+1)*args.batch_size, len(torchlist))

		database_middle[left:right,:] = latent_vectors.cpu().data.numpy()

	np.save(os.path.join(args.model_dir,'database_middle.npy'), database_middle)
