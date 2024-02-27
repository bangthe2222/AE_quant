# -*- coding: utf-8 -*-
import torch
from torch import nn
from tqdm import  tqdm

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class AutoEncoder(nn.Module):
    """
    Define AutoEncoder model
    """
    def __init__(self, dim_input = 83, act = nn.SiLU(), d=10):
        super().__init__()
        self.dim_input = dim_input

        self.encoder = nn.Sequential(
            nn.Linear(dim_input, 25),
            act,
            nn.Linear(25, d),
            
        )

        self.decoder = nn.Sequential(
            nn.Linear(d, 25),
            act,
            nn.Linear(25, dim_input),
            # act
        )

        
    def forward(self, x):
        z = self.encoder(x.view(-1, self.dim_input))
        # mu = mu_logvar[:, 0, :]
        # logvar = mu_logvar[:, 1, :]
        # z = self.reparameterise(mu, logvar)
        return self.decoder(z)

    # def reparameterise(self, mu, logvar):
    #     if self.training:
    #         std = logvar.mul(0.5).exp_()
    #         epsilon = std.data.new(std.size()).normal_()
    #         return epsilon.mul(std).add_(mu)
    #     else:
    #         return mu
            
    def loss_function(self,x_hat, x,dim_input):
        
        mse = nn.functional.mse_loss(
            x_hat, x.view(-1, dim_input), reduce=self.training, reduction='sum',
        )
        
        return mse
    
def train_model(model, optimizer, train_loader, epochs, skip = 100):
    """
    Train model

    Parameters:
    - model
    - optimizer
    - train_loader
    - epochs
    - skip

    Returns:
    - None
    
    """
    epochs = epochs
    for epoch in range(0, epochs + 1):
        
        model.train()
        train_loss = 0
        batch_id = 0
        if epoch%skip == 0:
            with tqdm(train_loader, unit=" batch") as tepoch:
                for x in tepoch:
                    
                    tepoch.set_description(f"Epoch {epoch}")
                    optimizer.zero_grad()
                    
                    # model forward
                    x = x.to(device)
                    
                    x_hat = model(x)
                    
                    # caculate loss
                    loss = model.loss_function(x_hat, x, dim_input=83)
                    
                    train_loss += loss.item()

                    # backpropagation
                    loss.backward()
                    optimizer.step()

                    # clear VRam
                    torch.cuda.empty_cache()
                    
                    batch_id += 1
                    
                    tepoch.set_postfix(loss= f' {round(train_loss/batch_id, 4)}')
        else:
            for x in train_loader:
                optimizer.zero_grad()
                
                # model forward
                x = x.to(device)
                
                x_hat = model(x)
                
                # caculate loss
                loss = model.loss_function(x_hat, x, dim_input=83)
                
                train_loss += loss.item()

                # backpropagation
                loss.backward()
                optimizer.step()

                # clear VRam
                torch.cuda.empty_cache()
                
                batch_id += 1


def loss_function(x_hat, x,dim_input, training ):
    """
    Caculate MSE loss

    Parameters:
    - x_hat
    - x
    - dim_input
    
    Returns:
    - mse: mse loss
    """
    mse = nn.functional.mse_loss(
        x_hat, x.view(-1, dim_input), reduce=training, reduction='sum',
    )
    
    return mse
