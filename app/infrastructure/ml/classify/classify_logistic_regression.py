from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2

def create_model(input_dim: int):
    """
    Creates a multi-class logistic regression model (3 classes) using Keras.
    
    Args:
        input_dim: Input layer dimension (number of features)
        
    Returns:
        Compiled Keras model for multi-class classification (classes 1, 2, 3)
    """
    model = Sequential()
    model.add(Input(shape=(input_dim,)))
    
    model.add(Dense(64, activation='relu', kernel_regularizer=l2(0.005)))  
    model.add(Dropout(0.5))  
    model.add(Dense(32, activation='relu', kernel_regularizer=l2(0.005)))
    model.add(Dropout(0.3))

    model.add(Dense(3, activation='softmax'))
    
    optimizer = Adam(learning_rate=0.0005)

    model.compile(
        optimizer=optimizer,
        loss='sparse_categorical_crossentropy', 
        metrics=['accuracy']
    )
    
    return model