import argparse

def get_opt():
     parser = argparse.ArgumentParser(description='AE')

     # path
     parser.add_argument('--data_root', type=str, default='dataset', metavar='N',
                         help='training images directory (database)')
     parser.add_argument('--model_dir', type=str, default='results/run', metavar='N',
                         help='path to save model')
     parser.add_argument('--cache_root', type=str, default="results/run/cache", 
                         help='path to cache files')


     parser.add_argument('--checkpoint', type=str, default='results/model_final.pt', \
                         metavar='N',help='full model directory')

     parser.add_argument('--result_dir', type=str, default='results/test_result', metavar='N',
                         help='where should results put')
     parser.add_argument('--test_dir', type=str, default='test_data', metavar='N',
                         help='testing images (query images) directory')

     # hyperparameter
     parser.add_argument('--batch_size', type=int, default=64, metavar='N',
                         help='input batch size for training (default: 16)')
     parser.add_argument('--epochs', type=int, default=1800, metavar='N',
                         help='number of epochs to train (default: 10)')
     parser.add_argument('--lr', type=float, default=0.001, metavar='N',
                         help='learning rate')
     parser.add_argument('--no_cuda', type=int, default=False,
                         help='enables CUDA training')
     parser.add_argument('--seed', type=int, default=1, metavar='S',
                         help='random seed (default: 1)')
     parser.add_argument('--save_model_interval', type=int, default=50, metavar='N',
                         help='save model every 50 epochs')


     # testing
     parser.add_argument('--use_flann', type = int, default = 0, metavar = 'N', 
     		    help = 'use_flann')
     parser.add_argument('--branching', type = int, default = 150, metavar = 'N', 
     		    help = 'k for kmeans')
     parser.add_argument('--topk', type=int, default=10, metavar='N',
                         help='Retrieved top k results')



     args = parser.parse_args()

     return args