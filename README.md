# CrisprScoringHub
Popular crispr scoring methods updated to python 3 for convienent use

# Installation

```
git clone https://github.com/Interventional-Genomics-Unit/CrisprScoringHub.git

cd CrisprScoringHub

pip install -r requirements.txt

python setup.py install

```

# Usage

The CrisprScoringHub pipeline requires a input text file, output text file, and score name. The pipeline can be run with the following command ``score.py -i /path/to/input.txt -o /path/to/output.txt -s cfd``

Below is an example ``input.txt`` file::

    name	grna_seq	context_seq
    guide1	GTGCGGCTGGCCCAGGACCTAGG	CTTGTGCGGCTGGCCCAGGACCTAGGCGAG
    guide2  CATGGTGCAGCTAAAGGCCCAGG	CCCTCATGGTGCAGCTAAAGGCCCAGGAGC


## Score Parameters

### Azimuth
### DeepSpCas9
### CFD
### OOF
### DeepCpf1


    




