# the CNN model to classify spongebob characters
import numpy as np
from models.data_model import DataModel
import matplotlib.pyplot as plt
from services.gradient_check_service import GradientCheckService
from helpers.prediction_helper import PredictionHelper
from sklearn.metrics import f1_score
from services.data_preprocessor_service import DataPreprocessorService as dps


class ShapeClassifier:

    def __init__(self,
                 data: DataModel,
                 epochs: int,
                 layers: list,
                 lamda: float,
                 batch_size: int = 20,
                 gradient_check: bool = False
                 ):
        self.data = data
        self.batch_size = batch_size
        self.epochs = epochs
        self.layers = layers
        self.prediction = None
        self.cost_history = []
        self.y_pred = [],
        self.lamda = lamda
        self.gradient_check = gradient_check

    # train model using this CNN architecture: X -> CONV -> POOL -> FC -> SOFTMAX
    def train(self, x, y):
        # self.display_data(x, y)
        # loop over epochs and perform gradient descent
        for epoch in range(self.epochs):
            print('Epoch: ' + str(epoch))
            for i in range(int(np.floor(y.shape[0] / self.batch_size))):
                index = i * self.batch_size
                offset = index + self.batch_size
                x_batch = dps.preprocess_imagebatch(self.data.x_train[index:offset], [100, 100])
                print('Batch: ' + str(i))

                self.y_pred = self.forward_propogate(x_batch)
                cost = self.compute_cost(y[index:offset], self.y_pred)

                print('Cost: ' + str(cost))
                self.cost_history.append(cost)

                self.backward_propogate(y[index:offset])

                GradientCheckService.check_gradients(self.layers[0], self) if self.gradient_check else None

                self.update_weights(epoch + 1)  # plus 1 to avoid divide by zero in momentum

        self.store_weights()

    def forward_propogate(self, A_prev):
        for layer in self.layers:
            A_prev = layer.forward_propogate(A_prev)

        return A_prev

    def compute_cost(self, y, y_prediction, regularization: bool = False):
        m = y.shape[0]
        cost = -(np.sum(y * np.log(y_prediction) + (1 - y) * np.log(1 - y_prediction))) / m
        cost += self.compute_cost_regularization() if regularization else 0
        return cost

    def compute_cost_regularization(self):
        reg_sum = 0
        for layer in self.layers:
            if hasattr(layer, 'W') and hasattr(layer, 'b'):
                reg_sum += layer.compute_cost_regularization(self.lamda)

        return reg_sum

    def backward_propogate(self, y, for_generator: bool=False):
        # get starting grad for y prediction
        dZ = np.subtract(self.y_pred, y)

        grads = {
            'dZ': dZ
        }

        # add grads to skipped layer
        self.layers[len(self.layers) - 1].backward_cache = grads

        for layer in reversed(self.layers[:-1]):  # skip output layer as it is computed above
            print(layer.name)
            grads = layer.backward_propogate(grads, self.lamda, for_generator)

        return grads

    def update_weights(self, iteration: int):
        for layer in self.layers:
            if hasattr(layer, 'W') and hasattr(layer, 'b'):
                layer.update_weights(iteration)

        return True

    def store_weights(self):
        for layer in self.layers:
            if hasattr(layer, 'W') and hasattr(layer, 'b'):
                layer.store_weights()

    @staticmethod
    def display_data(x, y):
        for i, image in enumerate(x):
            plt.imshow(image)
            plt.title(y[i])
            plt.show()

    def compute_f1_score(self, dataset):
        if dataset == 'train':
            x = self.data.x_train
            y_true = np.argmax(self.data.y_train, axis=1)
        elif dataset == 'cv':
            x = self.data.x_val
            y_true = np.argmax(self.data.y_val, axis=1)
        elif dataset == 'test':
            x = self.data.x_test
            y_true = np.argmax(self.data.y_test, axis=1)

        x_batch = dps.preprocess_imagebatch(self.data.x_train[0:500], [100, 100])
        output = self.forward_propogate(x_batch)
        y_preds = PredictionHelper.predict(output)

        f1score = f1_score(y_true[0:500], y_preds, average='weighted')

        return f1score
