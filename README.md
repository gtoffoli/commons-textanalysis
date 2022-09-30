# commons-textanalysis
Text-analysis support for *Django* clients, talking through HTTP API to an extended *spaCy* deployment. 

This is a **Django** app implementing a repertoire of **Text Analysis** functions with general objectives of linguistic education, to be used in the context of both L1 and L2, by learners and teachers and by editors of text resources.

*commons-textanalysis* currently supports, quite in similar way, **8 European languages**: English, Italian, Spanish, Greek, French, Portuguese, Croatian and Lithuanian.
Since this largely depends on the availability of *spaCy* (statistical) *language models* and on other *language resources* needed by different text analysis methods, support of additional languages is expected to be added as those resources will be available. This, in turn, will depend on the the interest shown by users and contributors.

***Origin***

**commons-textanalysis** is a spin-off of the *commons* project (2014-3017), which started the development of the *Commons Platform* software; the first deployment of the latter was *CommonSpaces*. Since then, the maintance of both the software and *CommonSpaces* has bee ensured by a few members of the original Consortium.

**CommonSpaces** is a *collaborative learning* platform, born with the *Erasmus+* *commons* project.
In 2019 it was integrated as a component of the *Up2U NGDLE* (New Generation Digital Learning Platform), the main result of the H2020 *Up2University* project.
At present, CommonSpaces hosts also a few *mini-sites* dedicated to the communities of other international research projects.

***Architecture***

*commons-textanalysis* was designed as part of a software stack; it:
- gets higher level services from the Django application **commons-language**, which integrates **spaCy**, with the associated language resources, extends someway its functionality and runs as a distict service exposing *HTTP API*;
- provides directly **a set of views**: an input view for selecting the analysis of interest and for inserting or specifying the text to be analyzed; many output views displaying the results of the analysis; doesn't define any Django model; 
- exposes **HTTP API** to be called by other applications; currently, these API are exploited by the Commons Platform (see above), which in this case acts as a **Content Management System** (CMS), allowing a user to analyze also stored contents, such as learning resources and shared documents.

***Dependencies***

*commons-textanalysis* strongly depends on the well-known **spaCy** NLP library, with all the (many) advantages and the few limitations this entails.

It also includes many **language resources**, mostly concerning specific languages, being available as *open data*. The role of these resources is to make the analysis methods, and often even the algorithms, able to work in a very similar way for different languages.

**Functionality**

Currently the following ouput views are implemented:
1. <u>Keywords in Context</u> thanks to the exploitation of a function of **tmtoolkit** in *commons-language*;
2. <u>ord lists by POS</u>; sorted lists are produced based on lexical resources concerning word frequencies and/or *CEFR* vocabulary levels;
3. <u>Annotated text<u>, interactively showing individual attributes of the text *tokens* and the result of *Named Entity Recognition* (NER); at present it reuses some code of **NlpBuddy**;
4. <u>Noun chunks</u> this comes directly from *spaCy*;
5. <u>Text readability</u> this is a provisional view putting together some raw (shallow) text features - mainly counts and means -, lexical features and syntactic features, with the results of classical *readability formulas* also based on raw text features;
6. <u>Text Cohesion</u> this view puts together *text coherence* scores computed with the *entity graph method* (Guinaudeau and Strube), as implemented by **TRUNAJOD**, with *local cohesion* scores based on the lexicon shared among contiguous paragraphs (visual detail is provided) and on *similarity scores* coming directly from spaCy;
7. <u>Text Summarization</u> this is the result of a very simple extractive algorithm;
8. <u>Text Analysis Dashboard</u> this is a tentative view putting together some results from 2, 3, 5 and 7; it also includes a sophisticated visualisation of the text structure derived with *dependency parsing*.

**Plans**

This package is work in progress; main activities planned are:
- complete the restructuring of the software stack, in order to make *commons-textanalysis* completely independent from the software of the *Commons Platform*, of wich originally it was part;
- document the API;
- retrieve language resources allowing to enable additional languages;
- improve and extend the current functionality;
- reorganize the output views to improve their usability;
- clean up the code, also to make easier possible contributions.