import numpy as np
import theano
import theano.tensor as T
from theano.compat.python2x import OrderedDict


class DecreasingLearningRate(object):
    def __init__(self, learning_rate, decrease_constant=0.95):
        """
        Parameters
        ----------
        decrease_constant: float
            factor decreasing learning rate.
        """
        assert decrease_constant >= 0.
        assert decrease_constant < 1.
        self.learning_rate = learning_rate
        self.decrease_constant = decrease_constant
        self.current_iteration = theano.shared(np.array(0, dtype=np.int64))
        self.parameters = [self.current_iteration]

    def get_updates(self, grads):
        grads = OrderedDict(grads)
        updates = OrderedDict()

        for param in grads.keys():
            decreased_learning_rate = T.cast(self.learning_rate / (1 + (self.decrease_constant * self.current_iteration)), dtype=theano.config.floatX)
            updates[param] = param - decreased_learning_rate * grads[param]

        updates[self.current_iteration] = self.current_iteration + 1

        return updates


class AdaDelta(object):
    """
    Implements the AdaDelta learning rule as described in:
    "AdaDelta: An Adaptive Learning Rate Method", Matthew D. Zeiler.
    """

    def __init__(self, decay=0.95, epsilon=0.0000001):
        """
        Parameters
        ----------
        decay: float
            decay rate \rho in Algorithm 1 of the afore-mentioned paper.
        """
        assert decay >= 0.
        assert decay < 1.
        self.decay = decay
        self.epsilon = epsilon
        self.parameters = []

    def get_updates(self, grads):
        grads = OrderedDict(grads)
        updates = OrderedDict()

        for param in grads.keys():
            # mean_squared_grad := E[g^2]_{t-1}
            mean_square_grad = theano.shared(theano._asarray(param.get_value() * 0., dtype=theano.config.floatX), name='mean_square_grad_' + param.name, borrow=False)
            self.parameters.append(mean_square_grad)
            # mean_square_dx := E[(\Delta x)^2]_{t-1}
            mean_square_dx = theano.shared(theano._asarray(param.get_value() * 0., dtype=theano.config.floatX), name='mean_square_dx_' + param.name, borrow=False)
            self.parameters.append(mean_square_dx)

            # Accumulate gradient
            new_mean_squared_grad = self.decay * mean_square_grad + (1 - self.decay) * T.sqr(grads[param])

            # Compute update
            rms_dx_tm1 = T.sqrt(mean_square_dx + self.epsilon)
            rms_grad_t = T.sqrt(new_mean_squared_grad + self.epsilon)
            delta_x_t = - rms_dx_tm1 / rms_grad_t * grads[param]

            # Accumulate updates
            new_mean_square_dx = self.decay * mean_square_dx + (1 - self.decay) * T.sqr(delta_x_t)

            # Apply update
            updates[mean_square_grad] = new_mean_squared_grad
            updates[mean_square_dx] = new_mean_square_dx
            updates[param] = param + delta_x_t

        return updates