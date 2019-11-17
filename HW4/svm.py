from os import listdir
from os.path import isfile, isdir, join
import pickle

mypath = "games/arkanoid/log"
files = listdir(mypath)
data = []

for f in files:
    fullpath = join(mypath, f)
    loadFile = open(fullpath, "rb")
    data.append(pickle.load(loadFile))
    loadFile.close()

frame = []
status = []
ballPosition = []
platformPosition = []
bricks = []

for i in range(0, len(data)):
    for j in range(0, len(data[i])):
        frame.append(data[i][j].frame)
        status.append(data[i][j].status)
        ballPosition.append(data[i][j].ball)
        platformPosition.append(data[i][j].platform)
        bricks.append(data[i][j].bricks)
        
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import numpy as np
import pygame
from pygame import Rect

def check_rect_collide(ball_position, m, bricks):
    if len(bricks)!= 0 and m != 0:
        for brick in bricks:
            brick_upper_X = round(ball_position[0] - ((ball_position[1] - brick[1] - 5) / m))
            ball_area = pygame.Rect((brick_upper_X, brick[1]), (5, 5))
            brick_area = pygame.Rect((brick[0], brick[1]), (25, 10))
            if ball_area.colliderect(brick_area) == 1:
                return brick
    return [0, 0]

x = []
for i in range(len(ballPosition) - 1):
    ball = ballPosition[i]
    ball_next = ballPosition[i + 1]
    m = 0
    if ball_next[0] - ball[0] != 0:
        m = (ball_next[1] - ball[1]) / (ball_next[0] - ball[0])
    brick_array = list(filter(lambda x: x[1] > ball_next[1], bricks[i]))
    overlap = check_rect_collide(ball_next, m, brick_array)
    x.append([ball[0], ball[1], ball_next[0], ball_next[1], platformPosition[i][0], overlap[0], overlap[1], m])

platX = np.array(platformPosition)[:, 0][:, np.newaxis]
platX_next = platX[1:, :]
instruct = (platX_next-platX[0: len(platX_next), 0][ :, np.newaxis])/5

x = np.array(x)
y = instruct
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.1, random_state = 0)

from sklearn import svm 
clf = svm.SVC(gamma = 0.01, decision_function_shape = 'ovo')
clf.fit(x_train, y_train)
filename = "svm.sav"
pickle.dump(clf, open(filename, 'wb'))
