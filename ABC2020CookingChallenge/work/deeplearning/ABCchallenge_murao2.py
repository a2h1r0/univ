# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 21:43:14 2020

@author: Kazuya
"""

import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
#from torchvision import datasets, transforms
from torch.autograd import Variable
import math
import glob
import sys

###Training param
EPOCH_NUM = 1000
HIDDEN_SIZE = 128
NUM_CHANNEL = 3
MAX_SEQ_LEN = 6000

###Label
is_activity_recognition = False #Activities if true, otherwise recipe
activities = ["Cut", "Peel", "Open", "Take", "Put", "Pour", "Wash", "Add", "Mix", "other"]
recipes = ["sandwich", "fruitsalad", "cereal"]
###Model class
class LSTM(nn.Module):
    def __init__(self, seq_size, hidden_size, out_size):
        super(LSTM, self).__init__()
        self.hidden_size = hidden_size
        self.lstm1 = torch.nn.LSTM(seq_size, hidden_size)
        self.fc1 = torch.nn.Linear(hidden_size, out_size)
        self.lstm2 = torch.nn.LSTM(seq_size, hidden_size)
        self.fc2 = torch.nn.Linear(hidden_size, out_size)
        self.lstm3 = torch.nn.LSTM(seq_size, hidden_size)
        self.fc3 = torch.nn.Linear(hidden_size, out_size)
        self.lstm4 = torch.nn.LSTM(seq_size, hidden_size)
        self.fc4 = torch.nn.Linear(hidden_size, out_size)
        self.fc5 = torch.nn.Linear(out_size*4, out_size)
 #       self.softmax = torch.nn.LogSoftmax(dim=1)
        
    def __call__(self, x1,x2,x3,x4):
        _, lstm_out1 = self.lstm1(x1)
        y1 = self.fc1(lstm_out1[0].view(-1, self.hidden_size))
        _, lstm_out2 = self.lstm2(x2)
        y2 = self.fc2(lstm_out2[0].view(-1, self.hidden_size))
        _, lstm_out3 = self.lstm3(x3)
        y3 = self.fc3(lstm_out3[0].view(-1, self.hidden_size))
        _, lstm_out4 = self.lstm4(x4)
        y4 = self.fc4(lstm_out4[0].view(-1, self.hidden_size))
        out = torch.cat([y1,y2,y3,y4], dim=1)
        y5 = self.fc5(out)
#        score = self.softmax(y) ##BCEWithLogitLoss inplements activation function
        return y5 

###Functions
def ActToIndex(activity, default=False):#Activity name to activity number
    if activity in activities:
        return activities.index(activity)
    else:
        return default
    
def RecpieToIndex(recipe, default=False):#Recipe name to recipe number
    if recipe in recipes:
        return recipes.index(recipe)
    else:
        return default

def MultiLabelBinarizer(label, NUM_CLASSES):#Multiple activity names to multi-label one-hot vector
    y = np.zeros(NUM_CLASSES)
    for i in label:
        y[i] = 1
    return y.tolist()

def MultiLabelDebinarizer(label):#Multi-label one-hot vector to multiple activity names
    label = label.cpu().numpy()
    output = [[] for i in range(len(label))]
    i, j = np.where(label>0)
    for k in range(len(i)):
        output[i[k]].append(j[k])
    return output

def CalcMultiLabelAccuracy(pred, target):#Calculate accuracy of multi-label output compered with groundtruth
    pred = pred.detach().cpu().numpy()
    target = target.cpu().numpy()
    best_th = 0
    best_F1score = 0 
    for th in range(0,100):
        i, j = np.where(pred>th/100)
        pred_onehot = np.zeros_like(pred)
        pred_onehot[i,j] = 1
        TP = np.count_nonzero(pred_onehot * target)
        pred_onehot_count = np.count_nonzero(pred_onehot)
        if pred_onehot_count == 0:
            Precision = 0
        else:
            Precision = TP / pred_onehot_count
        target_count = np.count_nonzero(target)
        if target_count == 0:
            Recall = 0
        else:
            Recall = TP / target_count
        if Precision + Recall == 0:
            F1score = 0
        else:
            F1score = 2 * Precision * Recall / (Precision + Recall)
        if (F1score > best_F1score):
            best_F1score = F1score
            best_th = th
    best_pred_label = [[] for i in range(len(pred))]
    best_i, best_j = np.where(pred>best_th/100)
    for i in range(len(best_i)):
        best_pred_label[best_i[i]].append(best_j[i])
    return best_F1score, best_th, best_pred_label        

###Label load   
labels = []
with open("train_new/labels.txt","r") as f:
    reader = f.readlines()
    for i in reader:
        l = i.replace(',\n', '').split(',')
        l[1] = RecpieToIndex(l[1])
        for j in range(2, len(l)):
            l[j] = ActToIndex(l[j])
        labels.append(l)

###Data load
print("Data Load Start")
print("is_activity_recognition? {}".format(is_activity_recognition))
bodyparts=["left_hip", "left_wrist", "right_arm", "right_wrist"]
for bodypart in bodyparts:
    print("Body part ={}".format(bodypart))
    files = glob.glob("train_new/"+bodypart+"/*")
    activityset = set()
    num_file = 0
    train_x = []
    train_y = []
    train_len = []
    csvname_used = []
#Activity recognition
    if is_activity_recognition:
        NUM_CLASSES = len(activities)
        for file in files:
            csvname = file.split("\\")[-1]
            csvname = csvname.replace(".csv","")
            activity = []
            for label in labels:
                if csvname in label:
                    activity = label[2:]
            reader = pd.read_csv(file)
            if(len(reader)>1):
                csvname_used.append(csvname)
                reader = np.array(reader)
                train_len.append(len(reader))
                train_x.append(torch.tensor(reader[:,:3],dtype=torch.float32))
                train_y.append(MultiLabelBinarizer(activity, NUM_CLASSES))
                num_file = num_file + 1
            else:
                csvname_used.append(csvname)
                train_len.append(1)
                train_x.append(torch.tensor([0,0,0],dtype=torch.float32))
                train_y.append(MultiLabelBinarizer(activity, NUM_CLASSES))
                num_file = num_file + 1
        train_x = torch.nn.utils.rnn.pack_sequence(train_x, enforce_sorted=False)
        train_y = torch.tensor(train_y)
        if bodypart == bodyparts[0]:
            train_x1 = train_x
        elif bodypart == bodyparts[1]:
            train_x2 = train_x
        elif bodypart == bodyparts[2]:
            train_x3 = train_x
        elif bodypart == bodyparts[3]:
            train_x4 = train_x
#Recipe recognition
    elif not is_activity_recognition:
        NUM_CLASSES = len(recipes)
        for file in files:
            csvname = file.split("\\")[-1]
            csvname = csvname.replace(".csv","")
            activity = []
            for label in labels:
                if csvname in label:
                    recipe = label[1]        
            reader = pd.read_csv(file)
            if(len(reader)>1):
                csvname_used.append(csvname)
                reader = np.array(reader)
                train_len.append(len(reader))
                train_x.append(torch.tensor(reader[:,:3],dtype=torch.float32))
                train_y.append(recipe)
                num_file = num_file + 1
            else:
                csvname_used.append(csvname)
                train_len.append(1)
                train_x.append(torch.tensor([0,0,0],dtype=torch.float32))
                train_y.append(recipe)
                num_file = num_file + 1
        train_x = torch.nn.utils.rnn.pack_sequence(train_x,enforce_sorted=False)
        train_y = torch.tensor(train_y)
        if bodypart == bodyparts[0]:
            train_x1 = train_x
        elif bodypart == bodyparts[1]:
            train_x2 = train_x
        elif bodypart == bodyparts[2]:
            train_x3 = train_x
        elif bodypart == bodyparts[3]:
            train_x4 = train_x
    
###model and loss function
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device = " + device.type)
model = LSTM(seq_size=NUM_CHANNEL, hidden_size=HIDDEN_SIZE, out_size=NUM_CLASSES)
model.to(device)
if is_activity_recognition:
    pos_weight = torch.ones([NUM_CLASSES])
    pos_weight_gpu = pos_weight.to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight_gpu)
elif not is_activity_recognition:
    criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters())
    
###Training start
print("NUM_CLASS:{}".format(NUM_CLASSES))
print("Training starts")
st = datetime.datetime.now()
FinalPred = []
FinalSigmoid = []
csvname_used.append("Total loss")
csvname_used.append("F1 score")
csvname_used.append("threshold sigmoid")
FinalPred.append(csvname_used)
FinalSigmoid.append(csvname_used)
if is_activity_recognition:
    train_y_debinarized = MultiLabelDebinarizer(train_y)
elif not is_activity_recognition:
    train_y_debinarized = train_y.numpy().tolist()
train_y_debinarized.append("-----")
train_y_debinarized.append("-----")
train_y_debinarized.append("-----")
FinalPred.append(train_y_debinarized)
FinalSigmoid.append(train_y_debinarized)
header = []
header.append("Filename")
header.append("Groundtruth")
for epoch in range(EPOCH_NUM):
    total_loss = 0
    optimizer.zero_grad()
    train_x1_gpu = train_x1.to(device)
    train_x2_gpu = train_x2.to(device)
    train_x3_gpu = train_x3.to(device)
    train_x4_gpu = train_x4.to(device)
    y = model(train_x1_gpu, train_x2_gpu, train_x3_gpu, train_x4_gpu)
    y_gpu = y.to(device)
    train_y_gpu = train_y.to(device)
    loss = criterion(y, train_y_gpu)
    loss.backward()
    total_loss += loss.item()
    optimizer.step()            
    if (epoch+1) % 10 == 0:
        header.append("EPOCH"+str(epoch+1))
        ed = datetime.datetime.now()
        y = torch.sigmoid(y)
        _, y_ = torch.max(y, 1)
        if is_activity_recognition:
            F1, th, pred = CalcMultiLabelAccuracy(y, train_y)
            pred.append(total_loss)
            pred.append(F1)
            pred.append(th/100)
            FinalPred.append(pred)
            sigmoid = y.detach().cpu().numpy().tolist()
            sigmoid.append(total_loss)
            sigmoid.append(F1)
            sigmoid.append(th/100)
            FinalSigmoid.append(sigmoid)
            print("epoch:\t{}\ttotal loss:\t{}\tF1 score:\t{}\tthreshold:\t{}\ttime:{}".format(epoch+1,total_loss,F1,th,ed-st))
        elif not is_activity_recognition:         
            pred = y_.cpu().numpy().tolist()
            pred.append(total_loss)
            F1 = np.count_nonzero(y_.cpu()==train_y)/len(y_)
            pred.append(F1)
            th = "---"
            pred.append(th)
            FinalPred.append(pred)
            sigmoid = y.detach().cpu().numpy().tolist()
            sigmoid.append(total_loss)
            sigmoid.append(F1)
            sigmoid.append(th)
            FinalSigmoid.append(sigmoid)
            print("epoch:\t{}\ttotal loss:\t{}\tAccuracy:\t{}\ttime:{}".format(epoch+1,total_loss,F1,ed-st))
        st = datetime.datetime.now()
f = open(("Activity_" if is_activity_recognition else "Recipe_") + "Allbodyparts_HIDDEN"+str(HIDDEN_SIZE)+"_prediction.txt", "w")
for i in header:
    f.write(i+"\t")
f.write("\n")
for i in range(len(FinalPred[0])):
    for j in range(len(FinalPred)):
        f.write(str(FinalPred[j][i])+"\t")
    f.write("\n")
f.close()
g = open(("Activity_" if is_activity_recognition else "Recipe_") + "Allbodyparts_HIDDEN"+str(HIDDEN_SIZE)+"_sigmoid.txt", "w")
for i in header:
    g.write(i+"\t")
g.write("\n")
for i in range(len(FinalSigmoid[0])):
    for j in range(len(FinalSigmoid)):
        g.write(str(FinalSigmoid[j][i])+"\t")
    g.write("\n")
g.close()