"""The template of the main script of the machine learning process
"""

import games.arkanoid.communication as comm
from games.arkanoid.communication import ( \
    SceneInfo, GameInstruction, GameStatus, PlatformAction
)
import pickle
import numpy as np

import pygame
from pygame import Rect

def check_rect_collide(ball_position, m, bricks) -> bool:
    if len(bricks)!= 0 and m != 0:
        for brick in bricks:
            brick_upper_X = round(ball_position[0] - ((ball_position[1] - brick[1] - 5) / m))
            ball_area = pygame.Rect((brick_upper_X, brick[1]), (5, 5))
            brick_area = pygame.Rect((brick[0], brick[1]), (25, 10))
            if ball_area.colliderect(brick_area) == 1:
                return True
    return False

def get_rect_collide(ball_position, m, bricks):
    if len(bricks)!= 0 and m != 0:
        for brick in bricks:
            brick_upper_X = round(ball_position[0] - ((ball_position[1] - brick[1] - 5) / m))
            ball_area = pygame.Rect((brick_upper_X, brick[1]), (5, 5))
            brick_area = pygame.Rect((brick[0], brick[1]), (25, 10))
            if ball_area.colliderect(brick_area) == 1:
                return brick
    return [0, 0]

def ml_loop():
    mode = "TestTrain" # TestTrain RuleBase
    predictFunction = "svm" #svm
    aid = 100
    past_ball_position = []
    ball_down = False
    comm.ml_ready()

    if mode == "RuleBase":
        while True:
            scene_info = comm.get_scene_info()

            if scene_info.status == GameStatus.GAME_OVER or \
                scene_info.status == GameStatus.GAME_PASS:
                comm.ml_ready()
                continue
            now_ball_position = scene_info.ball

            if len(past_ball_position) == 0:
                past_ball_position = now_ball_position
                bricks_history = scene_info.bricks
            else:
                if (now_ball_position[1] - past_ball_position[1]) > 0:
                    ball_down = True
                else:
                    ball_down = False
        
            m = 0
            if ball_down == True and now_ball_position[1] > 250:
                if now_ball_position[0] - past_ball_position[0] != 0:
                    m = (now_ball_position[1] - past_ball_position[1]) / (now_ball_position[0] - past_ball_position[0])
                    aid = round(now_ball_position[0] - ((now_ball_position[1] - 395) / m))
                if aid < 0:
                    aid = -aid
                elif aid > 195:
                    aid = 200 - (aid - 200)
            else:
                if now_ball_position[0] < 10 or now_ball_position[0] > 175 or now_ball_position[1] < 250:
                    aid = 100

            move = True
            bricks = list(filter(lambda x: x[1] > now_ball_position[1], scene_info.bricks))
            if check_rect_collide(now_ball_position, m, bricks):
                move = False

            now_platform_positionX = scene_info.platform[0] + 20
            if m != 0:
                if (m > 0 and aid >= 100 and aid <= 120) or (m > 0 and aid < 80):
                    now_platform_positionX = scene_info.platform[0] + 5
                elif (m < 0 and aid <= 100 and aid >= 80) or (m < 0 and aid > 120):
                    now_platform_positionX = scene_info.platform[0] + 35

            if move and aid > now_platform_positionX:
                comm.send_instruction(scene_info.frame, PlatformAction.MOVE_RIGHT)
            if move and aid < now_platform_positionX:
                comm.send_instruction(scene_info.frame, PlatformAction.MOVE_LEFT)
            if move and aid == now_platform_positionX:
                comm.send_instruction(scene_info.frame, PlatformAction.NONE)

            past_ball_position = now_ball_position

    if mode == "TestTrain":   
        filename = predictFunction + ".sav"
        model = pickle.load(open(filename, 'rb')) 
        
        while True:
            scene_info = comm.get_scene_info()
            now_ball_position = scene_info.ball

            if len(past_ball_position) != 0:
                m = 0
                if now_ball_position[0] - past_ball_position[0] != 0:
                    m = (now_ball_position[1] - past_ball_position[1]) / (now_ball_position[0] - past_ball_position[0])
                bricks = list(filter(lambda x: x[1] > now_ball_position[1], scene_info.bricks))
                overlap = get_rect_collide(now_ball_position, m, bricks)

                inp_temp = np.array([past_ball_position[0], past_ball_position[1], now_ball_position[0], now_ball_position[1], scene_info.platform[0], overlap[0], overlap[1], m])
                input = inp_temp[np.newaxis, :]
                
                if scene_info.status == GameStatus.GAME_OVER or \
                    scene_info.status == GameStatus.GAME_PASS:
                    comm.ml_ready()
                    continue
                move = model.predict(input)

                if move < 0:
                    comm.send_instruction(scene_info.frame, PlatformAction.MOVE_LEFT)
                elif move > 0:
                    comm.send_instruction(scene_info.frame, PlatformAction.MOVE_RIGHT)
                else:
                    comm.send_instruction(scene_info.frame, PlatformAction.NONE)    
            past_ball_position = now_ball_position