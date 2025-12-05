#ML algorithmic - Mean regression
import numpy as np
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

# Sample data (replace this with your dataset)
X = np.array([[1], [2], [3], [4], [5]])
y = np.array([10, 20, 30, 40, 50])

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Mean Regression Model
class MeanRegression:
    def fit(self, X, y):
        # Calculate the mean of the target variable
        self.mean = np.mean(y)
    
    def predict(self, X):
        # Return the mean value for all inputs
        return np.full((X.shape[0],), self.mean)

# Instantiate and train the model
model = MeanRegression()
model.fit(X_train, y_train)

# Predict on the test set
y_pred = model.predict(X_test)

# Calculate and print the mean squared error
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {mse}")

# Print the mean value used for prediction
print(f"Predicted Mean Value: {model.mean}")
