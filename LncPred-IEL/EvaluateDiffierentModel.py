import numpy as np
import pandas as pd
import time
import random
import os
from Bio import SeqIO
from sklearn.metrics import roc_auc_score, accuracy_score, recall_score, f1_score, precision_score
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold

# data preparation
# fasta format
lncRNA = list(SeqIO.parse("/home/xyz/test/data/gencode.v29.Human.lncRNA.input", "fasta"))
pcts = list(SeqIO.parse("/home/xyz/test/data/gencode.v29.Human.coding.input", "fasta"))
# lncRNA = list(SeqIO.parse("/home/xyz/test/data/gencode.vM21.Mouse.lncRNA.input", "fasta"))
# pcts = list(SeqIO.parse("/home/xyz/test/data/gencode.vM21.Mouse.coding.input", "fasta"))
lncRNA = lncRNA[:9000]
pcts = pcts[:27000]
# pcts = pcts[:len(lncRNA)]
# gtf format
# lncRNA = pd.read_csv("gencode.v29.long_noncoding_RNAs.gtf",sep="\t")
# pcts = pd.read_csv("gencode.v29.pcts_RNAs.gtf",sep="\t")
# lncRNA = lncRNA[:len(pcts)]

print(len(lncRNA))
print(len(pcts))
global_y = []
for num in range(0, len(lncRNA)):
    global_y.append(1)
for num in range(0, len(pcts)):
    global_y.append(0)
global_y = np.asarray(global_y)
all_X = np.concatenate((lncRNA, pcts), axis=0)
index = [i for i in range(len(all_X))]
random.shuffle(index)
all_X = all_X[index]
global_y = global_y[index]


def CPC2_model_train(lncRNA_file, pcts_file, output_file):
    os.system(
        "python2 /home/xyz/CPC2-beta/bin/CPC2_train.py -l " + lncRNA_file + " -p " + pcts_file + " -o " + output_file)


def CPC2_model_test(lncRNA_file, output_file):
    print("CPC2 is Running ... ")
    os.system("python2 /home/xyz/CPC2-beta/bin/CPC2.py -i " + lncRNA_file + " -o " + output_file)
    result = pd.read_csv(output_file, sep="\t")
    proba = list(result['coding_probability'])
    label = list(result['label'].apply(lambda x: 0 if x == "coding" else 1))
    os.system("rm -f output_file")
    return proba, label


def CPAT_model_train(lncRNA_file, pcts_file, species):
    os.system(
        "python2 /home/xyz/CPAT-1.2.4/bin/make_hexamer_tab.py -c " + pcts_file + " -n " + lncRNA_file + " > Human_Hexamer.tsv")
    os.system(
        "python2 /home/xyz/CPAT-1.2.4/bin/make_logitModel.py  -x Human_Hexamer.tsv -c " + pcts_file + " -n " + lncRNA_file + " -o " + species)


def CPAT_model_test(lncRNA_file, species, output_file):
    print("CPAT is Running ... ")
    os.system(
        "python2 /home/xyz/CPAT-1.2.4/bin/cpat.py -g " + lncRNA_file + " -d " + species + ".logit.RData -x " + species + "_Hexamer.tsv -o " + output_file)
    result = pd.read_csv(output_file, sep="\t")
    proba = list(1 - result['coding_prob'])
    label = list(result['coding_prob'].apply(lambda x: 1 if x <= 0.5 else 0))
    return proba, label


def CPPred_model_train(lncRNA_file, pcts_file, species):
    print("Making hexamer table...")
    os.system(
        "python2 /home/xyz/CPPred/make_hexamer_tab.py -c " + pcts_file + " -n " + lncRNA_file + " > test_Hexamer.tsv")
    print("Extracting features...")
    os.system(
        "python2 /home/xyz/CPPred/CPPred_train_predict/bin/get_features_svm.py -ip " + pcts_file + " -in " + lncRNA_file + " -hex test_Hexamer.tsv -spe " + species + " -osvm test_features.fa")
    print("Generating the range file...")
    os.system("/home/xyz/CPPred/libsvm-3.22/svm-scale -l 0 -u 1 -s test.range test_features.fa > test.scaled")
    print("Start training...")
    os.system("/home/xyz/CPPred/libsvm-3.22/svm-train -g 0.5 -c 1024 -b 1 test.scaled test.model")


def CPPred_model_test(lncRNA_file, output_file):
    print("CPPred is Running ... ")
    os.system(
        "python2 /home/xyz/CPPred/bin/CPPred.py -i " + lncRNA_file + " -hex /home/xyz/CPPred/CPPred_train_predict/bin/test_Hexamer.tsv -r /home/xyz/CPPred/CPPred_train_predict/bin/test.range -mol /home/xyz/CPPred/CPPred_train_predict/bin/test.model -spe Human -o " + output_file)
    result = pd.read_csv(output_file, sep="\t")
    proba = list(1 - result['coding_potential'])
    label = list(result['table'].apply(lambda x: 0 if x == "coding" else 1))
    print(len(proba))
    print(len(label))
    return proba, label


def PLEK_model_train(lncRNA_file, pcts_file):
    os.system("python2 /home/xyz/PLEK.1.2/PLEKModelling.py -mRNA " + pcts_file + " -lncRNA " + lncRNA_file + \
              " -prefix plek -minlength 1")


def PLEK_model_test(lncRNA_file, output_file):
    print("PLEK is Running ... ")
    os.system("python2 /home/xyz/PLEK.1.2/PLEK.py -fasta " + lncRNA_file + " -out " + output_file + ".predicted \
    -range plek.range -model plek.model -minlength 1")
    result = pd.read_csv(output_file, sep="\t", header=None)
    proba = list(result[1])
    label = list(result[1].apply(lambda x: 1 if x <= 0 else 0))
    return proba, label


def COME_model_test(lncRNA_file, output_file):
    print("CPPred is Running ... ")
    os.system(
        "python2 /home/xyz/CPPred/bin/CPPred.py -i " + lncRNA_file + " -hex /home/xyz/CPPred/Hexamer/Human_Hexamer.tsv -r /home/xyz/CPPred/Human_Model/Human.range -mol /home/xyz/CPPred/Human_Model/Human.model -spe Human -o " + output_file)
    time.sleep(10)
    result = pd.read_csv(output_file, sep="\t")
    proba = list(1 - result['coding_potential'])
    label = list(result['table'].apply(lambda x: 0 if x == "coding" else 1))
    return proba, label


# def CNCI_model_test(lncRNA_file, output_file):
#     print("CNCI is Running ... ")
#     os.system("python2 /home/xyz/CNCI-master/CNCI.py -f " + lncRNA_file + " -o " + output_file + " -m ve -p 4")
#     output_file = output_file + "/CNCI.index"
#     result = pd.read_csv(output_file, sep="\t")
#     proba = list(result['index'].apply(lambda x: 0 if x == "coding" else 1))
#     print(proba)
#     label = list(result['index'].apply(lambda x: 0 if x == "coding" else 1))
#     print(label)
#     return proba, label


def Longdist_model_train(lncRNA_file, pcts_file):
    os.system("python /home/xyz/longdist.py/longdist.py --longs " + lncRNA_file + \
              " --pcts " + pcts_file + " --purge ")


def Longdist_model_test(lncRNA_file, train_X_lncRNA_path, train_X_pcts_path, outfile):
    model_config = "/home/xyz/test/mid/" + os.path.split(train_X_lncRNA_path)[1].split(".")[0] + "_x_" + \
                   os.path.split(train_X_pcts_path)[1].split(".")[0] + "_50_orf1.plk.conf"
    print(model_config)
    print("Longdist is Running ... ")
    os.system(
        "python longdist.py/longdist.py --predict --input " + lncRNA_file + " --model_config " + model_config + " --out " + outfile)

    result = pd.read_csv(outfile, sep=",")
    proba = list(result['lncRNA %'])
    label = list(result['lncRNA %'].apply(lambda x: 0 if x < 0.5 else 1))
    return proba, label


def model_performance(model_proba, model_predict, test_y):
    print(len(test_y))
    print(len(model_proba))

    AUC = roc_auc_score(test_y, model_proba)
    Accuracy = accuracy_score(test_y, model_predict)
    Sensitivity = recall_score(test_y, model_predict)
    Specificity = (Accuracy * len(test_y) - Sensitivity * sum(test_y)) / (len(test_y) - sum(test_y))
    F1 = f1_score(test_y, model_predict)
    Precision = precision_score(test_y, model_predict)
    return AUC, Accuracy, Sensitivity, Specificity, F1, Precision


def test_preparation(cv_round, model_name, train_data_lncRNA, train_data_pcts, test_data):
    path1 = "/home/xyz/test/mid/" + model_name + "_" + str(cv_round) + ".fa"
    count1 = SeqIO.write(test_data, path1, "fasta")
    path2 = "/home/xyz/test/mid/" + model_name + "_training_lncRNA" + str(cv_round) + ".fa"
    count2 = SeqIO.write(train_data_lncRNA, path2, "fasta")
    path3 = "/home/xyz/test/mid/" + model_name + "_training_pcts" + str(cv_round) + ".fa"
    count3 = SeqIO.write(train_data_pcts, path3, "fasta")
    return path1, count1, path2, path3


def crossValidation(all_X, global_y, folds):
    AUCs = []
    Accuracys = []
    Sensitivitys = []
    Specificitys = []
    F1s = []
    Precisions = []
    cv_round = 1
    for global_train_index, global_test_index in folds.split(all_X, global_y):
        print('..........................................................................')
        print('global cross validation, round %d, beginning' % cv_round)
        start = time.perf_counter()
        train_X = all_X[global_train_index]
        train_y = global_y[global_train_index]
        test_X = all_X[global_test_index]
        test_y = global_y[global_test_index]
        # path = "/home/xyz/test/mid/CPC2_test_"+str(cv_round)+".fa"
        # count = SeqIO.write(test_X,path,"fasta")
        train_X_lncRNA = train_X[train_y == 1]
        train_X_pcts = train_X[train_y == 0]
        # path, count, train_X_lncRNA_path, train_X_pcts_path = test_preparation(cv_round, "CPC2_test", train_X_lncRNA, train_X_pcts, test_X)
        # path,count,train_X_lncRNA_path,train_X_pcts_path= test_preparation(cv_round,"PLEK_test",train_X_lncRNA,train_X_pcts,test_X)
        # path,count,train_X_lncRNA_path,train_X_pcts_path = test_preparation(cv_round,"CPPred_test",train_X_lncRNA,train_X_pcts,test_X)
        # path,count,train_X_lncRNA_path,train_X_pcts_path= test_preparation(cv_round,"CPAT_test",train_X_lncRNA,train_X_pcts,test_X)
        # path, count, train_X_lncRNA_path, train_X_pcts_path = test_preparation(cv_round, "CNCI_test", train_X_lncRNA,train_X_pcts, test_X)
        path, count, train_X_lncRNA_path, train_X_pcts_path = test_preparation(cv_round, "Longdist_test",train_X_lncRNA, train_X_pcts, test_X)
        print("write back %i seqences for test" % count)
        # train
        # CPC2_model_train(train_X_lncRNA_path, train_X_pcts_path, "/home/xyz/test/result/yes")
        # CPPred_model_train(train_X_lncRNA_path, train_X_pcts_path, 'Human')
        # CPAT_model_train(train_X_lncRNA_path,train_X_pcts_path,'Human')
        # PLEK_model_train(train_X_lncRNA_path,train_X_pcts_path)
        Longdist_model_train(train_X_lncRNA_path, train_X_pcts_path)
        # test
        ### proba, label = CNCI_model_test(path, "/home/xyz/test/result/CNCI_result")  ###
        # proba, label = PLEK_model_test(path, "/home/xyz/test/result/PLEK_result.predicted")
        # proba,label = CPAT_model_test(path,'Human',"/home/xyz/test/result/CPAT_result")
        # proba,label = CPC2_model_test(path, "/home/xyz/test/result/CPC2_result")
        # proba,label = CPPred_model_test(path, "/home/xyz/test/result/CPPred_result")
        proba, label = Longdist_model_test(path, train_X_lncRNA_path, train_X_pcts_path, "/home/xyz/test/result/Longdist_result")
        AUC, Accuracy, Sensitivity, Specificity, F1, Precision = model_performance(proba, label, test_y)

        AUCs.append(AUC)
        Accuracys.append(Accuracy)
        Sensitivitys.append(Sensitivity)
        Specificitys.append(Specificity)
        F1s.append(F1)
        Precisions.append(Precision)
        end = time.perf_counter()

        print('AUC %.4f, Accuracy %.4f,Sensitivity %.4f, Specificity %.4f,F1 %.4f, Precision %.4f' % (
            AUC, Accuracy, Sensitivity, Specificity, F1, Precision))
        print('round %.4f, running time: %.4f hour' % (cv_round, (end - start) / 3600))
        print('..........................................................................\n')
        cv_round += 1
    return np.mean(AUCs), np.mean(Accuracys), np.mean(Sensitivitys), np.mean(Specificitys), np.mean(F1s), np.mean(Precisions)


folds = KFold(n_splits=10, shuffle=True, random_state=np.random.RandomState(1))
AUC, Accuracy, Sensitivity, Specificity, F1, Precision = crossValidation(all_X, global_y, folds)
print("AUC:", AUC)
print("Accuracy:", Accuracy)
print("Sensitivity:", Sensitivity)
print("Specificity:", Specificity)
print("F1:", F1)
print("Precision:", Precision)
