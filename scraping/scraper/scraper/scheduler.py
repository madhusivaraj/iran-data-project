import time
import numpy as np
from contextlib import contextmanager

@contextmanager
def wait_guard(dt):
    '''Guarded block will end no earlier than 'dt' seconds after it starts'''
    wait = mk_wait(dt)
    yield
    wait()

def mk_has_passed(dt):
    t = time.time() + dt
    def has_passed():
        return time.time() > t
    return has_passed

def mk_wait(dt):
    then = time.time()
    def wait():
        wait_until(then + dt)
    return wait

def wait_until(t):
    safe_sleep(t - time.time())

def safe_sleep(dt):
    if dt > 0:
        time.sleep(dt)

def from_gaussian_mixture(*mixture):
    '''
    mixture:
        (mu_1, sigma_1, weight_1), (mu_2, sigma_2, weight_2), ..., (mu_n, sigma_n, weight_n)
            mu: mean
            sigma: standard deviation
            weight: weight of this distribution. sum of weights should be 1
    '''
    a = np.array(mixture, dtype=np.float)
    samples = np.random.normal(a[:,0], a[:,1])
    return np.random.choice(samples, p=a[:,2])

# test_mixture = (
#     (10, 1, .6),
#     (100, .1, .3),
#     (1000, .01, .1),
#     )

def nonnegative(f):
    def wrapper(*args, **kwargs):
        while True:
            x = f(*args, **kwargs)
            if x >= 0:
                return x
    return wrapper

# Distributions chosen sorta arbitrarily
class RandomScheduler(object):

    def __init__(self, speed=1):
        self.magnitude = 1 / speed

    # Time before first session
    @nonnegative
    def initial_delay(self):
        return self.magnitude * (self.session_length() / 5)

    # Time on captcha
    @nonnegative
    def captcha_time(self):
        return self.magnitude * np.random.normal(2, .5)

    # Time on document
    @nonnegative
    def document_time(self):
        return self.magnitude * from_gaussian_mixture(
            (  10 ,  4 , .4),
            (1*60 , 20 , .2),
            (5*60 , 60 , .4),
            )

    # Time of total session
    @nonnegative
    def session_length(self):
        return self.magnitude * from_gaussian_mixture(
            ( 2*60 ,  4 , .2),
            ( 5*60 , 20 , .4),
            (10*60 , 60 , .4),
            )

    # Time between sessions
    @nonnegative
    def session_delay(self):
        return 0

# For testing
class LameScheduler(object):

    def __init__(self, lame_session_length=3*60):
        self.lame_session_length = lame_session_length

    def initial_delay(self):
        return 0

    def captcha_time(self):
        return 0

    def document_time(self):
        return 0

    def session_length(self):
        return self.lame_session_length

    def session_delay(self):
        return 0
