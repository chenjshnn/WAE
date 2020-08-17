import os, time, pickle, pyflann
from PIL import Image
import numpy as np
import glob

import torch
from torch.utils.data import DataLoader
from torch.autograd import Variable
from torchvision import transforms

from Model_AE2 import AE, mse_loss
from utils import findtTopMinimalIndex, load_data_from_pickle
from opts import get_opt

torch.manual_seed(2)


args = get_opt()
args.cuda = not args.no_cuda and torch.cuda.is_available()
device = torch.device("cuda" if args.cuda else "cpu")

# reshape_size = [140,224]
reshape_size = [180,288]


def save_results(wireframe, sourcefile, query_resultPath, n):
	wireframeavedPath = os.path.join(query_resultPath,'wclosest_{}.png'.format(n))
	image_savePath = wireframeavedPath.replace("wclosest_", "sclosest_")

	os.system("cp '{}' '{}'".format(wireframe, wireframeavedPath))
	os.system("cp '{}' '{}'".format(sourcefile, image_savePath))


def read_test_data():		
	img_transform = transforms.Compose([
	    transforms.Resize((reshape_size[1],reshape_size[1])),
	    transforms.ToTensor()
	])	

	file_list_test = glob.glob(args.test_dir+"/**/**.png", recursive = True)

	image_list_test = []
	for imgfile in file_list_test:
		# create a folder for each query 
		name = os.path.basename(imgfile).split(".")[0]
		query_resultPath = os.path.join(args.result_dir, name)
		if not os.path.exists(query_resultPath):
			os.makedirs(query_resultPath)

		imgtest = Image.open(imgfile)
		imgtest.save(query_resultPath + "/target.png", "PNG")

		# transformation
		imgtest = imgtest.resize((reshape_size[0],reshape_size[1]), Image.ANTIALIAS)
		combine_img = Image.new('RGB', (reshape_size[1],reshape_size[1]), (255,255,255))
		combine_img.paste(imgtest, (0,0))
		imgtest1 = img_transform(combine_img)

		image_list_test.append(imgtest1)

	torchlist = (torch.stack(image_list_test))
	return file_list_test, torchlist


def build_flann(database_middle):
	pyflann.set_distance_type('euclidean')
	flann = pyflann.FLANN()

	param_name = os.path.join(args.model_dir, 'params_AE2.pk')
	flann_name = os.path.join(args.model_dir, 'flann_fix2_AE2')

	if os.path.exists(param_name):
		print("==> Load Flann")
		params = pickle.load(open(param_name,'rb'))
		flann.load_index(bytes(flann_name, encoding='utf8'), database_middle)

	else:
		# build
		print("==> Build Flann")
		params = flann.build_index(database_middle, algorithm='kmeans',\
					   target_precision=0.9, branching = args.branching, log_level='info')

		try:
			pickle.dump(params,open(param_name,'wb'))
			flann.save_index(bytes(flann_name,encoding='utf8'))
		except Exception as e:
			print('Failed to save flann')
			print(e)
	return flann


if __name__ == '__main__':
	if not os.path.exists(args.result_dir):
		os.makedirs(args.result_dir)

	# read latent vectors of database
	print('==> Restoring training data from pickle.' , args.cache_root)
	reading_start = time.clock()
	sfile_list, wfile_list, _ = load_data_from_pickle(args.cache_root)
			
	database_middle = np.load(os.path.join(args.model_dir,'database_middle.npy'))
	database_middle_loader = DataLoader(database_middle, batch_size = args.batch_size, shuffle = False, num_workers= 4)

	if args.use_flann:
		flann = build_flann(database_middle)

	#load model
	model = AE().to(device)
	if args.no_cuda:
		model.load_state_dict(torch.load(args.checkpoint, map_location = lambda storage, loc:storage)) #'cpu'
	else:
		model.load_state_dict(torch.load(args.checkpoint))

	model.eval()

	# load test data
	print('==> Reading Test Data')
	file_list_test, image_list_test = read_test_data()

	# ====> Start Testing
	f_result = open(os.path.join(args.result_dir, 'TestingResult.txt'), 'a')

	img1 = (image_list_test.to(device)).view(-1,3,reshape_size[1],reshape_size[1])
	middle1 = model(img1)
	test_middle = middle1.cpu().data.numpy()

	if args.use_flann:
		test_middle = test_middle.astype(np.float64)
		similarity_list_all, dists = flann.nn_index(test_middle, args.branching , checks = params['checks'])
	else:
		test_middle = torch.tensor(test_middle, dtype = torch.float)

	for i in range(len(image_list_test)):
		f_result.write("\nTestdata: {} \n".format(file_list_test[i]))
		print("Testdata:", file_list_test[i])
		name = os.path.basename(file_list_test[i]).split(".")[0]
		query_resultPath = os.path.join(args.result_dir, name)

		each_test_start = time.clock()

		if args.use_flann:
			new_new_index_list = similarity_list_all[i]
			similarity_list = dists[i]
		else:
			# get middle representation of query image\
			curr_middle = test_middle[i,:]
			middle1 = curr_middle.to(device).view(-1,len(database_middle[0])).float()
			similarity_list = []
			# compare with database
			for j, database_batch in enumerate(database_middle_loader):
				middle2 = database_batch.to(device).view(-1,len(database_middle[0])).float()
				loss = mse_loss(middle2, middle1)
				similarity_list.extend(loss.data)

			similarity_list = np.array(similarity_list)
			# sort similarity
			index_list = np.argpartition(similarity_list, args.topk)[:args.topk]

			new_similarity_list = [similarity_list[index] for index in index_list] 
			new_index_list = findtTopMinimalIndex(args.topk, new_similarity_list)
			new_new_index_list = [index_list[index] for index in new_index_list]


		for j in range(len(new_new_index_list)):
			index = new_new_index_list[j]
			wireframe = wfile_list[index]
			sourcefile = sfile_list[index]
			if args.use_flann:
				current_sim = similarity_list[j]
			else:
				current_sim = similarity_list[index]
			save_results(wireframe, sourcefile, query_resultPath, j)

			f_result.write("searchdata: {}  MSE:{:02f}\n".format(wireframe, current_sim)) 

		print("\n")
	f_result.close()


