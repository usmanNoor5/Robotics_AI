from graphviz import Digraph
import numpy as np

import math

def trace(root):
    # builds a set of all nodes and edges in a graph
    nodes,edges = set(), set()
    def build(v):
        if v not in nodes:
            nodes.add(v)
            for child in v._prev:
                edges.add((child,v))
                build(child)
    build(root)
    return nodes, edges
            
def draw_dot(root, format='svg', rankdir='LR'):
    assert rankdir in ['LR', 'TB']
    nodes, edges = trace(root)
    dot = Digraph(format=format, graph_attr={'rankdir': rankdir}) #, node_attr={'rankdir': 'TB'})
    
    for n in nodes:
        #modified label definition
        dot.node(name=str(id(n)), label = "{ %s | data %.4f | grad %.4f }" % (n.label,           n.data, n.grad), shape='record')
        if n._op:
            dot.node(name=str(id(n)) + n._op, label=n._op)
            dot.edge(str(id(n)) + n._op, str(id(n)))
    
    for n1, n2 in edges:
        dot.edge(str(id(n1)), str(id(n2)) + n2._op)
    
    return dot

def unbroadcast(grad, shape):
    """
    Reduces gradient so that it matches the given shape.
    This is required for broadcasting backward pass.
    """
    # If grad has extra dimensions, sum them out
    while len(grad.shape) > len(shape):
        grad = grad.sum(axis=0)

    # For dimensions where original had size 1, sum along that axis
    for i, dim in enumerate(shape):
        if dim == 1:
            grad = grad.sum(axis=i, keepdims=True)

    return grad


class Tensor:
    
    def __init__(self, data, _children=(), _op='', label=''):
        self.data = np.array(data, dtype=np.float32)
        self.grad = np.zeros_like(self.data)
        self._backward = lambda: None # None for leaf nodes in the graph
        self._prev = set(_children)
        self._op = _op
        self.label = label
        
    def __repr__(self):
        return f"Tensor(data={self.data})"
    
    def __add__(self, other):
        out = Tensor(self.data + other.data, (self, other), '+')
        def _backward():
            self.grad += unbroadcast(out.grad, self.data.shape)
            other.grad += unbroadcast(out.grad, other.data.shape)
        out._backward = _backward
        return out
    
    def __mul__(self, other):
        
        out = Tensor(self.data * other.data, (self, other), '*')
        def _backward():
            self.grad += unbroadcast(other.data * out.grad, self.data.shape)
            other.grad += unbroadcast(self.data * out.grad, other.data.shape)
        out._backward = _backward
        return out
    def dot(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        
        out = Tensor(self.data.dot(other.data), (self, other), 'dot')

        def _backward():
            # dL/dX = dL/dY @ W.T
            self.grad += unbroadcast(out.grad.dot(other.data.T), self.data.shape)
            
            # dL/dW = X.T @ dL/dY
            other.grad += unbroadcast(self.data.T.dot(out.grad), other.data.shape)

        out._backward = _backward
        return out


    def tanh(self):
        x = self.data
        t = (math.exp(2*x) - 1)/(math.exp(2*x) + 1)
        out = Tensor(t, (self, ), 'tanh')
        
        def _backward():
            self.grad += (1 - t**2) * out.grad
        out._backward = _backward
        return out
    
    def sigmoid(self):
        x = self.data
        s = 1 / (1 + math.exp(-x))   
        out = Tensor(s, (self,), 'sigmoid')
        
        def _backward():
            self.grad += s * (1 - s) * out.grad  
        out._backward = _backward
        
        return out
    
    def relu(self):
        out = Tensor(np.maximum(0, self.data), (self,), 'relu')

        def _backward():
            relu_grad = (self.data > 0).astype(np.float32)   # 1 where x>0, else 0
            self.grad += unbroadcast(relu_grad * out.grad, self.data.shape)

        out._backward = _backward
        return out

    def log(self):
        out = Tensor(np.log(self.data), (self,), 'log')

        def _backward():
            self.grad += self.unbroadcast((1 / self.data) * out.grad, self.data.shape)

        out._backward = _backward
        return out
    def sum(self, axis=None, keepdims=False):
        out = Tensor(self.data.sum(axis=axis, keepdims=keepdims), (self,), 'sum')

        def _backward():
            self.grad += self.unbroadcast(out.grad, self.data.shape)

        out._backward = _backward
        return out
    
    def softmax(self):
        # Numerical stability
        shifted = self.data - np.max(self.data, axis=-1, keepdims=True)
        exps = np.exp(shifted)
        probs = exps / np.sum(exps, axis=-1, keepdims=True)

        out = Tensor(probs, (self,), 'softmax')

        def _backward():
            # General Jacobian-vector product for softmax
            for i in range(self.data.shape[0]):
                p = probs[i].reshape(-1, 1)
                J = np.diagflat(p) - p @ p.T
                self.grad[i] += J @ out.grad[i]

        out._backward = _backward
        return out
    
    def cross_entropy(self, target):
    
        N = self.data.shape[0]
        
        probs = self.data[np.arange(N), target]
        out = Tensor(-np.log(probs).mean(), (self,), 'cross_entropy')

        def _backward():
            grad = self.data.copy()
            grad[np.arange(N), target] -= 1
            grad /= N
            self.grad += grad * out.grad

        out._backward = _backward
        return out
    

    def exp(self):
        out = Tensor(np.exp(self.data), (self,), 'exp')

        def _backward():
            self.grad += self.unbroadcast(out.data * out.grad, self.data.shape)

        out._backward = _backward
        return out
    
    def backward(self):
        topo = []
        visited = set()

        def build(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build(child)
                topo.append(v)

        build(self)
        self.grad = np.ones_like(self.data) 
        for node in reversed(topo):
            node._backward()

class Linear:
    def __init__(self, in_features, out_features):
        W = np.random.randn(in_features, out_features) * 0.01
        b = np.zeros((1, out_features), dtype=np.float32)

        self.W = Tensor(W)
        self.b = Tensor(b)

    def __call__(self, x):
        return x.dot(self.W) + self.b

    def parameters(self):
        return [self.W, self.b]


class MLP:
    def __init__(self):
        self.l1 = Linear(3072, 128)
        self.l2 = Linear(128, 10)

    def __call__(self, x):
        x = self.l1(x).relu()
        x = self.l2(x)
        return x

    def parameters(self):
        return self.l1.parameters() + self.l2.parameters()




# inputs x1,x2

# Fake batch: 4 samples, 3 features
root = "/home/usman/Documents/Robotics_AI/machine_learning/projects/Project_1/cifar-10-batches-py"
import pickle
import numpy as np
import os

def load_cifar10_batch(file):
    with open(file, 'rb') as f:
        batch = pickle.load(f, encoding='bytes')
    X = batch[b'data']                # (10000, 3072)
    y = np.array(batch[b'labels'])    # (10000,)
    return X, y


def load_cifar10(root):
    xs, ys = [], []

    for i in range(1, 6):
        file = os.path.join(root, f"data_batch_{i}")
        X, y = load_cifar10_batch(file)
        xs.append(X)
        ys.append(y)

    X_train = np.concatenate(xs, axis=0)   # (50000, 3072)
    y_train = np.concatenate(ys, axis=0)   # (50000,)  

    X_test, y_test = load_cifar10_batch(
        os.path.join(root, "test_batch")
    )

    # Normalize to [0,1]
    X_train = X_train.astype(np.float32) / 255.0
    X_test = X_test.astype(np.float32) / 255.0

    return X_train, y_train, X_test, y_test


X_train, y_train, X_test, y_test = load_cifar10(root)

print(X_train.shape)   # (50000, 3072)
print(y_train.shape)   # (50000,)
print(X_test.shape)    # (10000, 3072)
print(y_test.shape)    # (10000,)

# Small batch
xb = Tensor(X_train[:8])   # (8, 3072)
yb = y_train[:8]           # (8,)

model = MLP()

logits = model(xb)
print("logits shape:", logits.data.shape)

probs = logits.softmax()
loss = probs.cross_entropy(yb)

print("loss:", loss.data)

loss.backward()

params = model.parameters()

print("W1 grad:", params[0].grad.shape)  # (3072, 128)
print("b1 grad:", params[1].grad.shape)  # (1, 128)
print("W2 grad:", params[2].grad.shape)  # (128, 10)
print("b2 grad:", params[3].grad.shape)  # (1, 10)





# o._backward()
# n._backward()
# x1w1x2w2._backward()
# x2w2._backward()
# x1w1._backward()

# # draw_dot(o)

# dot = draw_dot(o)
# dot.render("computation_graph", view=True)



# print(d) #prints Tensor(data=6.0)
# print(d._prev) #prints {Tensor(data=12.0), Tensor(data=-6.0)}
# print(d._op) #prints +


# print("d:", d.data, d._op)
# print("d._prev:", d._prev)

# for node in d._prev:
#     print(" parent:", node.data, node._op, node._prev)
    

