import os
import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, Subset
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler


# Configuration
DATASET_PATH = "dataset.json"
MODELS_DIR = "saved_models"
BATCH_SIZE = 64
EPOCHS = 50  
LEARNING_RATE = 1e-4
TRAIN_SPLIT = 0.8 
INPUT_SIZE = 1000  
HIDDEN_SIZE = 128

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)


class FingerprintClassifier(nn.Module):
    """Basic neural network model for website fingerprinting classification."""
    
    def __init__(self, input_size, hidden_size, num_classes):
        super(FingerprintClassifier, self).__init__()
        
        # 1D Convolutional layers
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=5, stride=2, padding=2)
        self.pool1 = nn.MaxPool1d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=5, stride=1, padding=2)
        self.pool2 = nn.MaxPool1d(kernel_size=2, stride=2)
        
        # Calculate the size after convolutions and pooling
        conv_output_size = input_size // 8  # After two 2x pooling operations
        self.fc_input_size = conv_output_size * 64
        
        # Fully connected layers
        self.fc1 = nn.Linear(self.fc_input_size, hidden_size)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(hidden_size, num_classes)
        
        # Activation functions
        self.relu = nn.ReLU()
        
    def forward(self, x):
        # Reshape for 1D convolution: (batch_size, 1, input_size)
        x = x.unsqueeze(1)
        
        # Convolutional layers
        x = self.relu(self.conv1(x))
        x = self.pool1(x)
        x = self.relu(self.conv2(x))
        x = self.pool2(x)
        
        # Flatten for fully connected layers
        x = x.view(-1, self.fc_input_size)
        
        # Fully connected layers
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        
        return x
        
class ComplexFingerprintClassifier(nn.Module):
    """A more complex neural network model for website fingerprinting classification."""
    
    def __init__(self, input_size, hidden_size, num_classes):
        super(ComplexFingerprintClassifier, self).__init__()
        
        # 1D Convolutional layers with batch normalization
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=5, stride=1, padding=2)
        self.bn1 = nn.BatchNorm1d(32)
        self.pool1 = nn.MaxPool1d(kernel_size=2, stride=2)
        
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm1d(64)
        self.pool2 = nn.MaxPool1d(kernel_size=2, stride=2)
        
        self.conv3 = nn.Conv1d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm1d(128)
        self.pool3 = nn.MaxPool1d(kernel_size=2, stride=2)
        
        # Calculate the size after convolutions and pooling
        conv_output_size = input_size // 8  # After three 2x pooling operations
        self.fc_input_size = conv_output_size * 128
        
        # Fully connected layers
        self.fc1 = nn.Linear(self.fc_input_size, hidden_size*2)
        self.bn4 = nn.BatchNorm1d(hidden_size*2)
        self.dropout1 = nn.Dropout(0.5)
        
        self.fc2 = nn.Linear(hidden_size*2, hidden_size)
        self.bn5 = nn.BatchNorm1d(hidden_size)
        self.dropout2 = nn.Dropout(0.3)
        
        self.fc3 = nn.Linear(hidden_size, num_classes)
        
        # Activation functions
        self.relu = nn.ReLU()
        
    def forward(self, x):
        # Reshape for 1D convolution: (batch_size, 1, input_size)
        x = x.unsqueeze(1)
        
        # Convolutional layers
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        
        # Flatten for fully connected layers
        x = x.view(-1, self.fc_input_size)
        
        # Fully connected layers
        x = self.relu(self.bn4(self.fc1(x)))
        x = self.dropout1(x)
        x = self.relu(self.bn5(self.fc2(x)))
        x = self.dropout2(x)
        x = self.fc3(x)
        
        return x



def train(model, train_loader, test_loader, criterion, optimizer, epochs, model_save_path):
    """Train a PyTorch model and evaluate on the test set.
    Args:
        model: PyTorch model to train
        train_loader: DataLoader for training data
        test_loader: DataLoader for testing data
        criterion: Loss function
        optimizer: Optimizer
        epochs: Number of epochs to train
        model_save_path: Path to save the best model
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    train_losses = []
    test_losses = []
    train_accuracies = []
    test_accuracies = []
    
    best_accuracy = 0.0
    
    for epoch in range(epochs):
        # Training
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for traces, labels in train_loader:
            traces, labels = traces.to(device), labels.to(device)
            
            # Zero the parameter gradients
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(traces)
            loss = criterion(outputs, labels)
            
            # Backward pass and optimize
            loss.backward()
            optimizer.step()
            
            # Statistics
            running_loss += loss.item() * traces.size(0)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
        
        epoch_loss = running_loss / len(train_loader.dataset)
        epoch_accuracy = correct / total
        train_losses.append(epoch_loss)
        train_accuracies.append(epoch_accuracy)
        
        # Evaluation
        model.eval()
        running_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for traces, labels in test_loader:
                traces, labels = traces.to(device), labels.to(device)
                outputs = model(traces)
                loss = criterion(outputs, labels)
                
                running_loss += loss.item() * traces.size(0)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        epoch_loss = running_loss / len(test_loader.dataset)
        epoch_accuracy = correct / total
        test_losses.append(epoch_loss)
        test_accuracies.append(epoch_accuracy)
        
        # Print status
        print(f'Epoch {epoch+1}/{epochs}, '
              f'Train Loss: {train_losses[-1]:.4f}, Train Acc: {train_accuracies[-1]:.4f}, '
              f'Test Loss: {test_losses[-1]:.4f}, Test Acc: {test_accuracies[-1]:.4f}')
        
        # Save the best model
        if epoch_accuracy > best_accuracy:
            best_accuracy = epoch_accuracy
            torch.save(model.state_dict(), model_save_path)
            print(f'Model saved with accuracy: {best_accuracy:.4f}')
    
    return best_accuracy



def evaluate(model, test_loader, website_names):
    """Evaluate a PyTorch model on the test set and show classification report with website names.
    Args:
        model: PyTorch model to evaluate
        test_loader: DataLoader for testing data
        website_names: List of website names for classification report
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for traces, labels in test_loader:
            traces, labels = traces.to(device), labels.to(device)
            outputs = model(traces)
            _, predicted = torch.max(outputs.data, 1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    # Print classification report with website names instead of indices
    print("\nClassification Report:")
    print(classification_report(
        all_labels, 
        all_preds, 
        target_names=website_names,
        zero_division=1
    ))
    
    return all_preds, all_labels

def load_data():
    with open(DATASET_PATH, 'r') as f:
        data = json.load(f)
    
    traces = []
    labels = []
    website_to_idx = {
        "https://cse.buet.ac.bd/moodle/": 0,
        "https://google.com": 1,
        "https://prothomalo.com": 2
    }
    
    for item in data:
        trace = item['trace_data']
        # Pad/truncate to 1000 points
        if len(trace) > INPUT_SIZE:
            trace = trace[:INPUT_SIZE]
        else:
            trace = trace + [0] * (INPUT_SIZE - len(trace))
        traces.append(trace)
        labels.append(website_to_idx[item['website']])
    
    return np.array(traces), np.array(labels), website_to_idx  # <-- Return mapping

class TraceDataset(Dataset):
    def __init__(self, traces, labels):
        self.traces = traces.astype(np.float32)
        self.labels = labels.astype(np.int64)
    
    def __len__(self):
        return len(self.traces)
    
    def __getitem__(self, idx):
        return (
            torch.tensor(self.traces[idx], dtype=torch.float32),
            torch.tensor(self.labels[idx], dtype=torch.long)
        )

def main():
    # 1. Load and preprocess data
    X, y, website_to_idx = load_data()  # <-- Get mapping
    
    # 2. Split data (80% train, 20% test)
    sss = StratifiedShuffleSplit(n_splits=1, test_size=1-TRAIN_SPLIT, random_state=42)
    train_idx, test_idx = next(sss.split(X, y))
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # 3. Normalize data
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # 4. Create PyTorch datasets
    train_dataset = TraceDataset(X_train, y_train)
    test_dataset = TraceDataset(X_test, y_test)
    
    # 5. Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)
    
    # 6. Initialize models
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    num_classes = len(website_to_idx)
    basic_model = FingerprintClassifier(INPUT_SIZE, HIDDEN_SIZE, num_classes).to(device)
    complex_model = ComplexFingerprintClassifier(INPUT_SIZE, HIDDEN_SIZE, num_classes).to(device)
    
    # 7. Train models
    criterion = nn.CrossEntropyLoss()
    basic_optimizer = optim.Adam(basic_model.parameters(), lr=LEARNING_RATE)
    complex_optimizer = optim.Adam(complex_model.parameters(), lr=LEARNING_RATE)
    
    print("Training basic model...")
    basic_model_path = os.path.join(MODELS_DIR, "basic_model.pth")
    train(basic_model, train_loader, test_loader, criterion, basic_optimizer, EPOCHS, basic_model_path)
    
    print("\nTraining complex model...")
    complex_model_path = os.path.join(MODELS_DIR, "complex_model.pth")
    train(complex_model, train_loader, test_loader, criterion, complex_optimizer, EPOCHS, complex_model_path)
    
    # 8. Evaluate best model
    best_model = complex_model  # Or add logic to select best model
    website_names = list(website_to_idx.keys())
    evaluate(best_model, test_loader, website_names)
    
    # 9. Save final model
    best_model_path = os.path.join(MODELS_DIR, "best_model.pth")
    torch.save(best_model.state_dict(), best_model_path)

if __name__ == "__main__":
    main()
