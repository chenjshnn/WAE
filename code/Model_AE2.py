from torch.nn import functional as F
from torch import nn
import torch

class AE(nn.Module):
	def __init__(self):
		super(AE, self).__init__()

		self.encoder = nn.Sequential(
			nn.Conv2d(3, 16, 3, stride=1, padding=1),
			nn.ReLU(True),
			nn.MaxPool2d(3, stride=3),
			nn.Conv2d(16, 32, 3, stride=1, padding=1),
			nn.ReLU(True),
			nn.BatchNorm2d(32),
			nn.MaxPool2d(2, stride=2),
			nn.Conv2d(32, 32, 3, stride=1, padding=1),
			nn.ReLU(True),
			nn.MaxPool2d(2, stride=2),
			nn.Conv2d(32, 64, 3, stride=1, padding=1),
			nn.ReLU(True),
			nn.BatchNorm2d(64),
			nn.MaxPool2d(2, stride=2)
		)
		self.decoder = nn.Sequential(
			nn.Upsample(scale_factor=2,mode='nearest'),
			nn.ConvTranspose2d(64, 32, 3, stride=1, padding=1),
			nn.ReLU(True),
			nn.Upsample(scale_factor=2,mode='nearest'),
			nn.ConvTranspose2d(32, 32, 3, stride=1, padding=1),
			nn.ReLU(True),
			nn.Upsample(scale_factor=2,mode='nearest'),
			nn.ConvTranspose2d(32, 16, 3, stride=1, padding=1),
			nn.ReLU(True),
			nn.Upsample(scale_factor=3,mode='nearest'),
			nn.ConvTranspose2d(16, 3, 3, stride=1, padding=1),
			nn.Tanh(),
		)
			
	
	def forward(self, x):
		en = self.encoder(x)
		if self.training:
			de = self.decoder(en)
			return de
		else:
			return en.view(-1,en.shape[1]*en.shape[2]*en.shape[3])	
	
def loss_function(recon_x, x):
	return F.mse_loss(recon_x, x, size_average=False)


def mse_loss(input, target):
	return torch.sum((input - target)**2,1) / input.data.nelement()

def init_weights(m):
	if type(m) == nn.Conv2d:
		torch.nn.init.xavier_uniform_(m.weight)
		m.bias.data.fill_(0.01)