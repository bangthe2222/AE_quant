import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
import seaborn as sns
from torch import  nn
from tqdm import  tqdm
from torch.utils.data import DataLoader
from sklearn.preprocessing import RobustScaler
from model.AE_FIN import loss_function

        
def normalize_histogram(hist):
    """
    Normalize a histogram so that it represents a probability distribution.
    
    Parameters:
    - hist: NumPy array representing the histogram counts.
    
    Returns:
    - Normalized histogram as a NumPy array.
    """
    total = np.sum(hist)
    if total == 0:
        raise ValueError("Histogram sum is zero; cannot normalize.")
    return hist / total

def total_variation_distance(distribution1, distribution2):
    """
    Calculate the Total Variation Distance (TVD) between two probability distributions.
    
    Parameters:
    - distribution1: NumPy array representing the first probability distribution.
    - distribution2: NumPy array representing the second probability distribution.
    
    Returns:
    - The TVD between the two distributions.
    """
    # Check if the distributions are normalized
    if not np.isclose(np.sum(distribution1), 1) or not np.isclose(np.sum(distribution2), 1):
        raise ValueError("Distributions must be normalized")
    
    # Calculate the TVD
    tvd = 0.5 * np.sum(np.abs(distribution1 - distribution2))
    return tvd

class PreprocessData:
    """
    Preprocess data class
    """
    def __init__(self, df) -> None:
        
        self.company_names = df.columns.to_numpy()[1:]
        self.company_names_out = [name+ " OUT" for name in self.company_names]
        self.data = df.values[:,1:]
        self.data_train = np.array(self.data, dtype=np.float32)
        self.transformer = RobustScaler().fit(self.data_train)
        self.data_norm = self.transformer.transform(self.data_train)

    def get_train_loader(self, batch_size = 64):
        """
        Get train loader

        Parameters:
        - batch_size: batch size of train loader
        
        Returns:
        - train loader
        """
        self.train_loader = DataLoader(self.data_norm, batch_size=batch_size)
        return self.train_loader
    
    def get_inverse_output(self, output):
        """
        Get inverse output data from RobustScaler nomalize

        Parameters:
        - output: output data
        
        Returns:
        - inverse output 
        """
        self.inverse_output = self.transformer.inverse_transform(output.to("cpu").detach().numpy())
        return self.inverse_output

class EDAProcess:
    """
    EDA process data class
    """
    def __init__(self, data_train, inverse_output, company_names) -> None:
        
        self.data_input = torch.tensor(data_train)
        self.data_output = torch.tensor(inverse_output)
        self.company_names = company_names
        self.company_names_out = [name+ " OUT" for name in self.company_names]
        self.loss = loss_function(self.data_output, self.data_input, data_train.shape[1], training=False)
        self.loss_mean = torch.mean(self.loss, dim=0)
        self.max_loss_index = torch.argmax(self.loss_mean)
        self.min_loss_index = torch.argmin(self.loss_mean)
        self.df_input = pd.DataFrame({name: values for name, values in zip(self.company_names, self.data_input.T)})
        self.df_output = pd.DataFrame({name: values for name, values in zip(self.company_names_out, self.data_output.T)})

    def get_min_max_index(self):
        """
        Get index of min and max loss value of reconstruction stock value

        Parameters:
        - None
        
        Returns:
        - index of min loss reconstruction stock value
        - index of max loss reconstruction stock value
        """
        
        print("min loss:", self.min_loss_index.item())
        print("Company name:", self.company_names[self.min_loss_index.item()])
        print()
        print("max loss:", self.max_loss_index.item())
        print("Company name:", self.company_names[self.max_loss_index.item()])
        
        return self.min_loss_index.item(), self.max_loss_index.item()
    
    def get_interleaved_data(self):
        """
        Get interleaved data of dataframe input and dataframe output

        Parameters:
        - None
        
        Returns:
        - dataframe interleaved
        """
        list_name_mix = []
        for i in range(len(self.company_names)):
            list_name_mix.append(self.company_names[i])
            list_name_mix.append(self.company_names_out[i])
        self.df_interleaved = pd.DataFrame()
        labels = list_name_mix

        # Loop through the labels and add the corresponding column to the new DataFrame
        columns_to_concat = [self.df_input[[label]] if label in self.df_input.columns else self.df_output[[label]] for label in labels]

        # Concatenating all collected columns at once
        self.df_interleaved = pd.concat(columns_to_concat, axis=1)

        return self.df_interleaved
    
    def plot_density(self):
        """
        Plot density of all stock value

        Parameters:
        - 
        
        Returns:
        -
        """
        data_frame = {
            "Label" : self.data_input.numpy().flatten(),
            "Reconstruction": self.data_output.numpy().flatten()
        }

        compare_df = pd.DataFrame(data_frame)
        compare_df.plot.density(
            figsize = (7, 7), 
            linewidth = 4
        )
    
    def plot_histgram(self, index = "min"):
        """
        Plot histogram of input and output stock value

        Parameters:
        - index: index of stock  
        
        Returns:
        -
        """
        if index == "min":
            index_ = self.min_loss_index.item()
        elif index == "max":
            index_ = self.max_loss_index.item()
        else:
            index_ = index

        plt.hist(self.df_input.iloc[:,index_].values.flatten(), bins=20, alpha=0.5, label='data_input')
        plt.hist(self.df_output.iloc[:,index_].values.flatten(), bins=20, alpha=0.5, label='data_output')

        # Add labels and legend
        plt.xlabel('Close Stock')
        plt.ylabel('Frequency')
        plt.legend()

        # Show the plot
        plt.show()
    
    def get_TVD(self, index):
        """
        Calculate the Total Variation Distance (TVD) between two probability distributions.
        
        Parameters:
        - index: index of stock
        
        Returns:
        - The TVD between the two distributions.
        """

        if index == "min":
            index_ = self.min_loss_index.item()
        elif index == "max":
            index_ = self.max_loss_index.item()
        else:
            index_ = index

        normalized_hist1 = normalize_histogram(self.df_input.iloc[:,index_].values.flatten())
        normalized_hist2 = normalize_histogram(self.df_output.iloc[:,index_].values.flatten())
        self.TVD_value = total_variation_distance(normalized_hist1, normalized_hist2)

        return self.TVD_value
    
    def plot_side_by_side_box(self, df, min = None, max = None):
        """
        Plot side by side box of stock value

        Parameters:
        - df: dataframe input
        - min: min index
        - max: max index
        
        Returns:
        - 
        """
        if min == None and max == None:
            sns.boxplot(df.iloc[:,:])
        elif min == None:
            sns.boxplot(df.iloc[:, :max])
        elif max == None:
            sns.boxplot(df.iloc[:, min:])
        else:
            sns.boxplot(df.iloc[:, min:max])