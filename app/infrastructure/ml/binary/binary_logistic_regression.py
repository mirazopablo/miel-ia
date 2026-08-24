from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam

def create_model(input_dim: int):
    """
    Creates a Logistic Regression model using Keras.
    
    Args:
        input_dim: Input layer dimension (number of features)
        
    Returns:
        Compiled Keras model
    """
    model = Sequential()
    model.add(Input(shape=(input_dim,)))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer=Adam(), loss='binary_crossentropy', metrics=['accuracy'])
    return model