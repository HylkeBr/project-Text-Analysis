# project-Text-Analysis
### Collin Krooneman, Maurice Voors & Hylke Brouwer


## assignment 5
#### Deadline
 - 23-05-'22; 14.59


## final project
#### Deadlines
 - System : 01-06-'22; 23.59
 - Presentation : 02-06-'22; 14.59 / 03-06-'22; 12.59
 - Report : 08-06-'22; 23.59

#### Command CoreNLP Server
 - java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -preload tokenize,ssplit,pos,lemma,ner,parse,depparse -status_port 9000 -port 9000 -timeout 15000 -serverProperties server.properties & 
