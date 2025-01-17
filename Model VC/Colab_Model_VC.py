#!/usr/bin/env python
# coding: utf-8

# In[ ]:


get_ipython().run_line_magic('cd', '/content/drive/MyDrive/Final/')

##########OBJECT INITIALIZATION##############

import argparse
import time

from pathlib import Path

import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random
from argparse import Namespace
from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier,     scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path, save_one_box
from utils.plots import colors, plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized

from matplotlib import pyplot as plt

from gtts import gTTS

def detect():
    scale = []
    noms = []
    opt = Namespace(agnostic_nms=False, augment=False, classes=None, conf_thres=0.25, device='', exist_ok=False, hide_conf=False, hide_labels=False, img_size=640, iou_thres=0.45, line_thickness=3, name='exp', nosave=False, project='runs/detect', save_conf=False, save_crop=False, save_txt=False, source='data/images/', update=False, view_img=False, weights=['yolov5s.pt'])
    #opt = Namespace(weights='yolov5s.pt',source='data/images',img_size=640,conf_thres=0.25,iou_thres=0.45,device='',project='runs/detect',name='exp',line_thickness=3,hide_labels=False,hide_conf=False)
    # parser = argparse.ArgumentParser()
    # NameSpace
    # parser.add_argument('--weights', nargs='+', type=str, default='yolov5s.pt', help='model.pt path(s)')
    # parser.add_argument('--source', type=str, default='data/images', help='source')  # file/folder, 0 for webcam
    # parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
    # parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
    # parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
    # parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    # parser.add_argument('--view-img', action='store_true', help='display results')
    # parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    # parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    # parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    # parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    # parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
    # parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    # parser.add_argument('--augment', action='store_true', help='augmented inference')
    # parser.add_argument('--update', action='store_true', help='update all models')
    # parser.add_argument('--project', default='runs/detect', help='save results to project/name')
    # parser.add_argument('--name', default='exp', help='save results to project/name')
    # parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    # parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    # parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    # parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    # opt = parser.parse_args()

    source, weights, view_img, save_txt, imgsz = opt.source, opt.weights, opt.view_img, opt.save_txt, opt.img_size
    save_img = not opt.nosave and not source.endswith('.txt')  # save inference images
    webcam = source.isnumeric() or source.endswith('.txt') or source.lower().startswith(
        ('rtsp://', 'rtmp://', 'http://', 'https://'))

    # Directories
    save_dir = increment_path(Path(opt.project) / opt.name, exist_ok=opt.exist_ok)  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

    # Initialize
    set_logging()
    device = select_device(opt.device)
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load model
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size
    names = model.module.names if hasattr(model, 'module') else model.names  # get class names
    if half:
        model.half()  # to FP16

    # Second-stage classifier
    classify = False
    if classify:
        modelc = load_classifier(name='resnet101', n=2)  # initialize
        modelc.load_state_dict(torch.load('weights/resnet101.pt', map_location=device)['model']).to(device).eval()

    # Set Dataloader
    vid_path, vid_writer = None, None
    if webcam:
        view_img = check_imshow()
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz, stride=stride)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride)

    # Run inference
    if device.type != 'cpu':
        model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once
    t0 = time.time()
    for path, img, im0s, vid_cap in dataset:
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        t1 = time_synchronized()
        pred = model(img, augment=opt.augment)[0]

        # Apply NMS
        pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
        t2 = time_synchronized()

        # Apply Classifier
        if classify:
            pred = apply_classifier(pred, modelc, img, im0s)

        # Process detections
        
        for i, det in enumerate(pred):  # detections per image
            
            if webcam:  # batch_size >= 1
                p, s, im0, frame = path[i], '%g: ' % i, im0s[i].copy(), dataset.count
            else:
                p, s, im0, frame = path, '', im0s.copy(), getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)  # img.jpg
            txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # img.txt
            s += '%gx%g ' % img.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            if len(det):
                
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
                scale.append(det[:, :4])
                aux = []
                for val in det[:,-1]:

                  aux.append(names[int(val)])
                
                noms.append(aux)
                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                # Write results
                for *xyxy, conf, cls in reversed(det):
                    if save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        line = (cls, *xywh, conf) if opt.save_conf else (cls, *xywh)  # label format
                        with open(txt_path + '.txt', 'a') as f:
                            f.write(('%g ' * len(line)).rstrip() % line + '\n')

                    if save_img or opt.save_crop or view_img:  # Add bbox to image
                        c = int(cls)  # integer class
                        label = None if opt.hide_labels else (names[c] if opt.hide_conf else f'{names[c]} {conf:.2f}')

                        plot_one_box(xyxy, im0, label=label, color=colors(c, True), line_thickness=opt.line_thickness)
                        if opt.save_crop:
                            save_one_box(xyxy, im0s, file=save_dir / 'crops' / names[c] / f'{p.stem}.jpg', BGR=True)
            else:
              noms.append([])
              scale.append([])
            # Print time (inference + NMS)
            print(f'{s}Done. ({t2 - t1:.3f}s)')

            # Stream results
            if view_img:
                cv2.imshow(str(p), im0)
                cv2.waitKey(1)  # 1 millisecond

            # Save results (image with detections)
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                else:  # 'video' or 'stream'
                    if vid_path != save_path:  # new video
                        vid_path = save_path
                        if isinstance(vid_writer, cv2.VideoWriter):
                            vid_writer.release()  # release previous video writer
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream
                            fps, w, h = 30, im0.shape[1], im0.shape[0]
                            save_path += '.mp4'
                        vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    vid_writer.write(im0)

    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        print(f"Results saved to {save_dir}{s}")

    print(f'Done. ({time.time() - t0:.3f}s)')
    return scale, noms

##########DEPTH INITIALIZATION##############

import torch
from options.train_options import TrainOptions
from loaders import aligned_data_loader
from models import pix2pix_model
import sys
import cv2
BATCH_SIZE = 1
#sys.argv[0]='--input=single_view'
opt = TrainOptions().parse()  # set CUDA_VISIBLE_DEVICES before import torch

# video_list = 'data/images/'
save_path = 'outfile'
eval_num_threads = 2
# video_data_loader = aligned_data_loader.DAVISDataLoader(video_list, BATCH_SIZE)
# video_dataset = video_data_loader.load_data()
# print('========================= Video dataset #images = %d =========' %
#       len(video_data_loader))

model = pix2pix_model.Pix2PixModel(opt)

torch.backends.cudnn.enabled = True
torch.backends.cudnn.benchmark = True
best_epoch = 0
global_step = 0

# print(
#     '=================================  BEGIN VALIDATION ====================================='
# )
#
# print('TESTING ON VIDEO')

##########################FUNCTIONS##########################
import statistics
def profunditat_objectes(imagen, coords, noms):
  
  valor_mitja = []
  for i, val in enumerate(coords):
    valor_mitja.append((1-statistics.mean(imagen[val[1]:val[3], val[0]:val[2]].flatten()))*10) # Resten 1-resultat perquè per la llibreria valor+gran=mes lluny i aquí al revés
    #Multipliquem per una constant per amplificar la posició del so a la llibreria.

  return valor_mitja

def punt_mitja(coords, shape):
  coord_finals = []
  for coord in coords:
    x = round((coord[0]+coord[2])/2)
    y = round((coord[1]+coord[3])/2)

    x1 = x/shape[1]#Normalitzem coords
    y1 = y/shape[0]#Normalitzem coords

    x_f = x1-0.5 #les deixem en un rang entre -0.5 i 0.5
    y_f = y1-0.5 #les deixem en un rang entre -0.5 i 0.5

    x_f = x_f*10 #Multipliquem per una constant per amplificar la posició del so a la llibreria.
    y_f = y_f*10 #Multipliquem per una constant per amplificar la posició del so a la llibreria.

    coord_finals.append([x_f,y_f])
  return coord_finals




model.switch_to_eval()

def profundidad():
  imatges = []
  for i, data in enumerate(video_dataset):
    print(i)
    stacked_img = data[0]
    targets = data[1]
    im = model.run_and_save_DAVIS(stacked_img, targets, save_path, video_list)

    # im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

    imatges.append(im)
  return imatges

################## SERVER #########################
import os
import math 
from matplotlib import pyplot as plt
import json

while True:

  objecte_json = []
  diccionari_json = {}
  longitud = 1

  while len(os.listdir('data/images')) != 0:

    video_list = 'data/images/'

    video_data_loader = aligned_data_loader.DAVISDataLoader(video_list, BATCH_SIZE)
    video_dataset = video_data_loader.load_data()

    # longitud = len(video_dataset)

    coords, noms = detect()
    imatges = profundidad()

    for i, y in enumerate(coords):
      if len(coords[i]):
        coords[i] = coords[i].cpu().numpy()
        coords[i] = coords[i].astype(int)


    for i, im in enumerate(imatges):
      plt.imshow(im, interpolation='nearest')
      plt.show()

      prof_mitja = profunditat_objectes(imatges[i], coords[i], noms[i])
      coord_mitja = punt_mitja(coords[i], im.shape)
      
      frase_a_reproduir = ""

      for j, v in enumerate(prof_mitja):
        
        diccionari_json = {}

        diccionari_json['x'] = coord_mitja[j][0]
        diccionari_json['y'] = coord_mitja[j][1]
        diccionari_json['z'] = prof_mitja[j]
        diccionari_json['nom'] = noms[i][j]
        dist = math.sqrt(coord_mitja[j][0]**2 + coord_mitja[j][1]**2 + prof_mitja[j]**2)
        diccionari_json['dist'] = dist

        objecte_json.append(diccionari_json)

        print(coord_mitja[j][0], coord_mitja[j][1], prof_mitja[j], noms[i][j])
        print("dist:", math.sqrt(coord_mitja[j][0]**2 + coord_mitja[j][1]**2 + prof_mitja[j]**2))
        
        dist2 = truncate(dist,2)
        frase_a_reproduir = frase_a_reproduir + noms[i][j] + " it's founded at: " + str(dist) + " metres. "
        

      with open('data/results/data.txt', 'a') as outfile:
        json.dump(objecte_json, outfile, indent=4)

      if frase_a_reproduir != "":
        from gtts import gTTS
        tts = gTTS(frase_a_reproduir)
        tts.save('data/results/audio/audio.wav')

      dir = 'data/images'
      for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))



