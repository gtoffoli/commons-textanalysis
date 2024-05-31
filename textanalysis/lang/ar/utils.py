import os
import re

# Clean/Normalize Arabic Text
# from: https://github.com/bakrianoo/aravec/blob/master/utilities.py
def clean_str(text):
    search = ["أ","إ","آ","ة","_","-","/",".","،"," و "," يا ",'"',"ـ","'","ى","\\",'\n', '\t','&quot;','?','؟','!']
    replace = ["ا","ا","ا","ه"," "," ","","",""," و"," يا","","","","ي","",' ', ' ',' ',' ? ',' ؟ ',' ! ']
    
    #remove tashkeel
    p_tashkeel = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = re.sub(p_tashkeel,"", text)
    
    #remove longation
    p_longation = re.compile(r'(.)\1+')
    subst = r"\1\1"
    text = re.sub(p_longation, subst, text)
    
    text = text.replace('وو', 'و')
    text = text.replace('يي', 'ي')
    text = text.replace('اا', 'ا')
    
    for i in range(0, len(search)):
        text = text.replace(search[i], replace[i])
    
    #trim    
    text = text.strip()

    return text

# Clean/Normalize arabic script in UD files (train, dev, test)
def clean_ud_file(path):
    if os.path.exists(path):
        f_in = open(path, 'r')
        f_out = open(path + '_clean', 'w')
        for line in f_in:
            f_out.writeline(clean_str(line))
        f_in.close()
        f_out.close()
