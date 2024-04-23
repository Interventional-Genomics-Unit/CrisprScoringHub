# CrisprScoringHub

Popular crispr scoring methods retrained & updated to Python 3.11 for convienent use

# Installation

```
git clone https://github.com/Interventional-Genomics-Unit/CrisprScoringHub.git

cd CrisprScoringHub

conda env create --name guidescorer --file guidescorer.yaml

conda activate guidescorer

```

# Usage

The CrisprScoringHub pipeline requires a input text file, output text file, and score name. The pipeline can be run with the following command ``python score.py -i /path/to/input.txt -o /path/to/output.txt -s cfd``

Below is an example ``input.txt`` file::

    name	grna_seq	context_seq
    guide1	GTGCGGCTGGCCCAGGACCTAGG	CTTGTGCGGCTGGCCCAGGACCTAGGCGAG
    guide2  CATGGTGCAGCTAAAGGCCCAGG	CCCTCATGGTGCAGCTAAAGGCCCAGGAGC


## Score Parameters

### Azimuth

Doench/Fusi 2016 Rule Set 2 on-target efficiency score now packaged as 'Azimuth'. Predicts whether a guide exhibits strong or weak cleavage
Score range 0-100. A score higher than 55% is recommended

-i --input: text file that incudes guide name, a gRNA sequence that include PAM and a 30bp context sequence (4bp 5', 20bp guide, 3bp PAM, 3bp 5')

-s --score_name: azimuth

*Reference*

This script was modified and re-trained from https://github.com/MicrosoftResearch/Azimuth

### DeepSpCas9

spCas9 efficiency score. Predicts the likelihood of getting a spCas9 indel at the desired target

-i --input: text file that incudes guide name, a gRNA sequence that include PAM and a 30bp context sequence (4bp 5', 20bp guide, 3bp PAM, 3bp 5')

-s --score_name: deepspcas9

*Reference*

Hui Kwon Kim et al. ,SpCas9 activity prediction by DeepSpCas9,
a deep learning–based model with high generalization performance.Sci. Adv.5,eaax9249(2019).
predicts the likelihood of getting a spCas9 indel at the desired target
This script is copied and modified from https://github.com/MyungjaeSong/Paired-Library

### Doench 2014

Doench 2014 efficiency score

-i --input: text file that incudes guide name, a gRNA sequence that include PAM and a 30bp context sequence (4bp 5', 20bp guide, 3bp PAM, 3bp 5')

-s --score_name: doench14

*Reference*

Doench et al, Nat Biotech 2014, PMID 25184501, http://www.broadinstitute.org/rnai/public/analysis-tools/sgrna-design

### CFD

Doench 2016 off-target specificity scoring. *Currently does not accept DNA or RNA bulges. Coming Soon*

-i --input: text file that incudes off target name, a gRNA sequence that include PAM and context sequence which contains off-target sequence

-s --score_name: cfd

*Reference*

Doench, Fusi, et al.  Nature Biotechnology 34, 184–191 (2016).


### OOF

out-of-frame score(OOF). A measurement of how likely an out-of-frame deletion occurs after a knock-out experiment based on microhomology.
Scoring ranges from 0-100. The higher the OOF score, the more deletions have a length that is not a multiple of three. A score above 66 is recommended

-i --input: text file that incudes guide target name, a gRNA sequence that include PAM and context sequence which is at least 60bp

-s --score_name: oof

*Reference*

Bae et al. https://www.nature.com/articles/nmeth.3015

### DeepCpf1

Cpf1(Cas12) on-target score predicts the likelihood of getting a cas12 indel at the desired target

-i --input: text file that incudes guide name, a gRNA sequence that include PAM and a 30bp context sequence (4bp 5', 20bp guide, 3bp PAM, 3bp 5')

-s --score_name: deepcpf1

*Reference*

Kim, H., Song, M., Lee, J. et al. In vivo high-throughput profiling of CRISPR–Cpf1 activity. Nat Methods 14, 153–159 (2017). 
https://github.com/MyungjaeSong/Paired-Library


### DeepABE

*coming soon*




