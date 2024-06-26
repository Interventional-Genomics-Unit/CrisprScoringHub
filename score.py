# Native Modules
from math import exp
import pickle
import re
import argparse
import os
# Installed Modules
import pandas as pd
import numpy as np
import tensorflow.compat.v1 as tf1
from tensorflow.keras.models import load_model
# Project Modules
from models.featurization import featurize_data
from models.deepcas_model import DeepCas9


def load_model_params(score_name: str, models_dir: str):
    try:
        if score_name == 'cfd':
            mm_scores = pickle.load(open(models_dir + '/mismatch_score.pkl', 'rb'))
            pam_scores = pickle.load(open(models_dir + '/PAM_scores.pkl', 'rb'))
            return mm_scores, pam_scores
        if score_name == 'azimuth':
            model = pickle.load(open(models_dir + '/python3_V3_model_no.pos.pickle', 'rb'))
            return model
        if score_name == 'doench14':
            doench14params = pickle.load(open(models_dir + '/doench14params.pkl', 'rb'))
            return doench14params
        if score_name == 'deepcpf1':
            model1 = load_model(models_dir + "/DeepCpf1.h5")
            model2 = load_model(models_dir + "/Seq_deepCpf1.h5")
            return model1, model2
        if score_name == 'deepspcas9':
            model = DeepCas9
            sess_path = f"{models_dir}/DeepCas9_Final/PreTrain-Final-False-3-5-7-100-70-40-0.001-550-True-80-60"
            return model, sess_path
    except FileNotFoundError:
        raise Exception(f"File containing {score_name} could not be opened")


def revcom(s):
    basecomp = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A','U':'A'}
    letters = list(s[::-1])
    letters = [basecomp[base] for base in letters]
    return ''.join(letters)

def preprocess_seq(data):
    length = 30
    DATA_X = np.zeros((len(data), 1, length, 4), dtype=int)
    for l in range(len(data)):
        for i in range(length):
            try:
                data[l][i]
            except:
                print(data[l], i, length, len(data))

            if data[l][i] in "Aa":
                DATA_X[l, 0, i, 0] = 1
            elif data[l][i] in "Cc":
                DATA_X[l, 0, i, 1] = 1
            elif data[l][i] in "Gg":
                DATA_X[l, 0, i, 2] = 1
            elif data[l][i] in "Tt":
                DATA_X[l, 0, i, 3] = 1
            else:
                pass
    return DATA_X


# === On-target Efficiency Scoring ===

def deepspcas9(cas9_sites, models_dir):
    '''
    Hui Kwon Kim et al. ,SpCas9 activity prediction by DeepSpCas9,
    a deep learning–based model with high generalization performance.Sci. Adv.5,eaax9249(2019).
    predicts the likelihood of getting a spCas9 indel at the desired target
    This script is copied and modified from https://github.com/MyungjaeSong/Paired-Library
    '''
    model, sess_path = load_model_params('deepspcas9', models_dir)
    processed_seqs = preprocess_seq(cas9_sites)

    # TensorFlow config
    conf = tf1.ConfigProto()
    conf.gpu_options.allow_growth = True
    filter_size = [3, 5, 7]
    filter_num = [100, 70, 40]
    l_rate, load_episode = 0.001, 550
    node_1, node_2 = 80, 60
    tf1.reset_default_graph()
    scores = np.zeros((processed_seqs.shape[0], 1), dtype=float)
    test_batch = 500
    tf1.logging.set_verbosity(tf1.logging.ERROR)
    with tf1.Session(config=conf) as sess:
        sess.run(tf1.global_variables_initializer())
        model = model(filter_size, filter_num, node_1, node_2, l_rate)
        saver = tf1.train.Saver()
        saver.restore(sess, sess_path)
        optimizer = model.optimizer
        for i in range(int(np.ceil(float(processed_seqs.shape[0]) / float(test_batch)))):
            Dict = {model.inputs: processed_seqs[i * test_batch:(i + 1) * test_batch], model.is_training: False}
            scores[i * test_batch:(i + 1) * test_batch] = sess.run([model.outputs], feed_dict=Dict)[0]
    return scores


def doench2014(cas9_sites, models_dir):
        """
        Doench 2014 'on-target score'
        Input is a 30mer: 4bp 5', 20bp guide, 3bp PAM, 3bp 5'
        Doench et al, Nat Biotech 2014, PMID 25184501, http://www.broadinstitute.org/rnai/public/analysis-tools/sgrna-design
        Code from crispor - https://github.com/maximilianh/crisporWebsite
        """
        doench2014params = load_model_params('doench14', models_dir)
        scores = []
        global gcWeight
        intercept = 0.59763615
        gcHigh = -0.1665878
        gcLow = -0.2026259

        for seq in cas9_sites:
            assert (len(seq) == 30)
            score = intercept
            guideSeq = seq[4:24]
            gcCount = guideSeq.count("G") + guideSeq.count("C")

            if gcCount <= 10:
                gcWeight = gcLow
            if gcCount > 10:
                gcWeight = gcHigh

            score += abs(10 - gcCount) * gcWeight

            for pos, modelSeq, weight in doench2014params:
                subSeq = seq[pos:pos + len(modelSeq)]
                if subSeq == modelSeq:
                    score += weight
            scores.append(int(100 * (1.0 / (1.0 + exp(-score)))))

        return scores


def azimuth(cas9_sites, models_dir):
    '''
    Doench/Fusi 2016 Rule -2 on-target / efficiency score now packaged as 'Azimuth'
    This script is copied and modified from https://github.com/MicrosoftResearch/Azimuth
    predicts whether a guide exhibits strong or weak cleavage
    Score range 0-100. A score higher than 55% is recommended
    '''
    #Doench/Fusi 2016 Rule -2 'on-target score'
    # This script is copied and modified to suit from https://github.com/MicrosoftResearch/Azimuth
    model = load_model_params('azimuth', models_dir)
    model, learn_options = model

    res = []
    for seq in cas9_sites:
        if "N" in seq:
            res.append(-1)  # can't do Ns
            continue

        pam = seq[25:27]
        if pam != "GG":
            # res.append(-1)
            # continue
            seq = list(seq)
            seq[25] = "G"
            seq[26] = "G"
            seq = "".join(seq)
        res.append(seq)
    seqs = np.array(res)

    learn_options["V"] = 2

    Xdf = pd.DataFrame(columns=['30mer', 'Strand'],
                       data=zip(seqs, np.repeat('NA', seqs.shape[0])))
    gene_position = pd.DataFrame(columns=['Percent Peptide', 'Amino Acid Cut position'],
                                 data=zip(np.ones(seqs.shape[0]) * -1,
                                          np.ones(seqs.shape[0]) * -1))

    feature_sets = featurize_data(data=Xdf, learn_options=learn_options, Y=pd.DataFrame())
    keys = list(feature_sets.keys())
    N = feature_sets[list(keys)[0]].shape[0]
    inputs = np.zeros((N, 0))
    feature_names = []
    dim = {}
    dimsum = 0
    for set in keys:
        inputs_set = feature_sets[set].values
        dim[set] = inputs_set.shape[1]
        dimsum += dim[set]
        inputs = np.hstack((inputs, inputs_set))
        feature_names.extend(feature_sets[set].columns.tolist())
    scores = model.predict(inputs)
    scores = [(s * 100).round(2) for s in scores]
    return scores


def deepcpf1(cas12_sites, models_dir):
    '''
    Cpf1(cas12) on-target score "kinda"
    predicts the likelihood of getting a cas12 indel at the desired target
    This script is copied and modified from https://github.com/MyungjaeSong/Paired-Library
    Kim, H., Song, M., Lee, J. et al. In vivo high-throughput profiling of CRISPR–Cpf1 activity. Nat Methods 14, 153–159 (2017)
    '''
    model1,model2 = load_model_params('deepcpf1', models_dir)
    data_n = len(cas12_sites)
    #if chromatin_flag != 'ignore':
     #   CA = np.zeros((data_n, 1), dtype=int)

    SEQ = np.zeros((data_n, 34, 4), dtype=int)

    for l in range(data_n):
        seq = cas12_sites[l]
        for i in range(34):
            if seq[i] in "Aa":
                SEQ[l, i, 0] = 1
            elif seq[i] in "Cc":
                SEQ[l, i, 1] = 1
            elif seq[i] in "Gg":
                SEQ[l, i, 2] = 1
            elif seq[i] in "Tt":
                SEQ[l, i, 3] = 1
        #CA[l - 1, 0] = int(chromatin_accessibility) * 100

    scores = model2.predict([SEQ], batch_size=50, verbose=0).tolist()

    return scores


def deepABE(abesites):
    '''
    ABE Efficiency Scoring
    This script is copied and modified from https://github.com/MyungjaeSong/Paired-Library
    Zhang, C., Yang, Y., Qi, T. et al. Prediction of base editor off-targets by deep learning.
    Nat Commun 14, 5358 (2023). https://doi.org/10.1038/s41467-023-41004-3
    30bp input 30 bp target sequence (4 bp + 20 bp protospacer + PAM + 3 bp)
    '''
    pass
    #model = load_model_params(score_name='deepabe')


# === Microhomology Scoring ===
def oofscore(seq):
    '''
    copied and adapted code from Bae et al. https://www.nature.com/articles/nmeth.3015
    computes both microhomology and out-of-frame score
    A measurement of how likely an out-of-frame deletion occurs after a knock-out experiment
    based on microhomology
    scoring range 0-100. The higher the oof score, the more deletions have a length that is not a multiple of three
     A score above 66 is recommended
    The higher the oof score, the more deletions have a length that is not a multiple of three
    '''
    length_weight = 20.0
    left = 30
    right = len(seq) - int(left)

    s1 = []
    for k in range(2, left)[::-1]:
        for j in range(left, left + right - k + 1):
            for i in range(0, left - k + 1):
                if seq[i:i + k] == seq[j:j + k]:
                    length = j - i
                    s1.append(seq[i:i + k] + '\t' + str(i) + '\t' + str(i + k) + '\t' + str(j) + '\t' + str(j + k) + '\t' + str(length))

    if s1 != "":
        list_f1 = s1
        sum_score_3 = 0
        sum_score_not_3 = 0

        for i in range(len(list_f1)):
            n = 0
            score_3 = 0
            score_not_3 = 0
            line = list_f1[i].split('\t')
            scrap = line[0]
            left_start = int(line[1])
            left_end = int(line[2])
            right_start = int(line[3])
            right_end = int(line[4])
            length = int(line[5])

            for j in range(i):
                line_ref = list_f1[j].split('\t')
                left_start_ref = int(line_ref[1])
                left_end_ref = int(line_ref[2])
                right_start_ref = int(line_ref[3])
                right_end_ref = int(line_ref[4])

                if (left_start >= left_start_ref) and (left_end <= left_end_ref) and (
                        right_start >= right_start_ref) and (right_end <= right_end_ref):
                    if (left_start - left_start_ref) == (right_start - right_start_ref) and (
                            left_end - left_end_ref) == (right_end - right_end_ref):
                        n += 1
                else:
                    pass

            if n == 0:
                if (length % 3) == 0:
                    length_factor = round(1 / exp((length) / (length_weight)), 3)
                    num_GC = len(re.findall('G', scrap)) + len(re.findall('C', scrap))
                    score_3 = 100 * length_factor * ((len(scrap) - num_GC) + (num_GC * 2))

                elif (length % 3) != 0:
                    length_factor = round(1 / exp((length) / (length_weight)), 3)
                    num_GC = len(re.findall('G', scrap)) + len(re.findall('C', scrap))
                    score_not_3 = 100 * length_factor * ((len(scrap) - num_GC) + (num_GC * 2))
            sum_score_3 += score_3
            sum_score_not_3 += score_not_3

        mh_score = round(sum_score_3 + sum_score_not_3,2)
        oof_score = round((sum_score_not_3) * 100 / (sum_score_3 + sum_score_not_3),2)

    return mh_score, oof_score


# === Off-target Specifity Scoring ===
def cfd_score(seq1, seq2, models_dir):
    '''
    Doench 2016 off-target scoring
    Doench, Fusi, et al.  Nature Biotechnology 34, 184–191 (2016)."

    '''
    mm_scores, pam_scores = load_model_params('cfd', models_dir)
    pam = seq2[-3:]
    seq1 = seq1.upper().replace('T', 'U')
    seq2 = seq2[:-3].upper().replace('T', 'U')
    m_seq1 = re.search('[^ATCGU\\-]', seq1)
    m_seq2 = re.search('[^ATCGU\\-]', seq2)

    score =1

    if (m_seq1 is None) and (m_seq2 is None):
        if seq1 != seq2:
            shorter, longer = sorted([seq1, seq2], key=len)
            for i in range(-len(shorter), 0):
                if (seq1[i] != seq2[i]):
                    key = 'r' + seq1[i] + ':d' + revcom(seq2[i]) + ',' + str(20 + i + 1)
                    score *= mm_scores[key]

            score *= pam_scores[pam[-2:]]
    else:
        score = -1
    return round(score,4)



def cfd_spec_score(sum_cfd_scores):
    '''
    on_target_seq is spacer site and off_target includes pam
    '''

    guide_cfd_score = 100 / (100+sum_cfd_scores)
    guide_cfd_score = round(guide_cfd_score*100,2)
    return guide_cfd_score


def score(input,output,score_name,models_dir):
    #input = '/home/thudson/projects/CrisprScoringHub/test/azimuth_input.txt'
    score_dict = {'name': [],
                  'grna_seq':[],
                  'context_seq':[]}

    with open(input,"r") as inp:
        for line in inp:
            if line.startswith('name')==False:
                name,grna_seq,context_seq = line.strip().split("\t")
                score_dict['name'].append(name)
                score_dict['grna_seq'].append(grna_seq)
                score_dict['context_seq'].append(context_seq)

    if score_name == 'cfd':
        scores = []
        for seqs in zip(score_dict['grna_seq'], score_dict['context_seq']):
            seq1,seq2 = seqs
            scores.append(cfd_score(seq1[:-3], seq2, models_dir))

    elif score_name == 'azimuth':
        scores = azimuth(score_dict['context_seq'], models_dir)

    elif score_name == 'doench14':
        scores = doench2014(score_dict['context_seq'], models_dir)

    elif score_name == 'deepcpf1':
        scores = deepcpf1(score_dict['context_seq'], models_dir)
        scores = [round(x[0],4) for x in scores]

    elif score_name == 'deepspcas9':
        scores = deepspcas9(score_dict['context_seq'], models_dir)
        scores = [round(x[0], 4) for x in scores]
    elif score_name == 'oof':
        scores = []
        for seq in score_dict['context_seq']:
           scores.append(oofscore(seq)[1])
    else:
        print(f"Print {score_name} is not a valid scoring option")

    score_dict['score'] = scores

    with open(output,'w') as out:
        out.write('\t'.join(score_dict.keys()) + '\n')
        for i in range(len(score_dict['name'])):
            line =[]
            for v in score_dict.values():
                line.append(str(v[i]))
            out.write('\t'.join(line) +'\n')


def main():
    mainParser = argparse.ArgumentParser()

    mainParser.add_argument('--output', "-o", help="output txt file", default="output.txt")
    mainParser.add_argument('--input', "-i", help="input txt file", required=True)
    mainParser.add_argument('--score_name', "-s",
                            help="score name (cfd, azimuth,deepspcas9,doench14,oof,deepcpf1)",
                            required=True)

    models_dir = os.path.dirname(os.path.realpath(__file__)) + "/models/"
    args = mainParser.parse_args()
    score(args.input, args.output, args.score_name, models_dir)

if __name__ == "__main__":
	main()