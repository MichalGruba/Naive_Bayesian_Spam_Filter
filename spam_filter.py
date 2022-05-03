import numpy as np
import os
import string
import re
from xml.etree.ElementTree import Element, tostring
from xml.etree import ElementTree as ET
from dicttoxml import dicttoxml
import glob

file_path = './emails'


class Email:

    spam_num = 0
    ham_num = 0

    def __init__(self, spam):
        self.nadawca = ""
        self.odbiorca = ""
        self.data = ""
        self.tytul = ""
        self.tresc = ""
        self.spam = spam
        if spam == 0:
            Email.spam_num += 1
        else:
            Email.ham_num += 1

        self.indicators = ['od:', 'do:', 'data:', 'temat:', 'Tresc:']

    def show(self):
        print(self.indicators[0], self.nadawca)
        print(self.indicators[1], self.odbiorca)
        print(self.indicators[2], self.data)
        print(self.indicators[3], self.tytul)
        print(self.indicators[4], self.tresc)

    def load(self, path):
        with open(path, encoding="utf8") as file:
            lines = file.readlines()

        i = 0
        content = ''
        info = []
        for line in lines:
            line = re.sub('\s+', ' ', line)
            line = re.sub(',', '', line)# remove white characters
            line = line.replace("?", '')
            line = line.split(":")[1]
            line = line.strip()

            content += line
            info.append(content)
            content = ''

        self.nadawca = info[0]
        self.odbiorca = info[1]
        self.data = info[2]
        self.tytul = info[3]
        self.tresc = info[4]


def prepareMail(path):
    email = Email(0)
    email.load(path)
    email.show()

    return email


def readFiles(path):
    emails = []
    if os.path.isdir(path):
        items = os.listdir(path)
        spam_files = [item for item in glob.glob(path + '/spam*.txt')]
        ham_files = [item for item in glob.glob(path + '/ham*.txt')]
        for file in spam_files:
            email = Email(1)
            email.load(file)
            email.show()
            emails.append(email)
        for file in ham_files:
            email = Email(0)
            email.load(file)
            email.show()
            emails.append(email)
    return emails


def getWords(emails, spam):
    words_in_emails = set()
    for email in emails:
        if email.spam != spam:
            continue
        text = email.tresc.translate(str.maketrans('', '', string.punctuation))
        splitted = text.split(" ")
        words_in_text = set(splitted)
        words_in_emails = words_in_emails.union(words_in_text)

    return words_in_emails


def getDicts(emails, words, spam):
    dict = {}
    for word in words:
        occurrences = 1
        for email in emails:
            if email.spam == spam:
                text = email.tresc.center(len(email.tresc) + 2)
                text = text.translate(str.maketrans('', '', string.punctuation))
                text = re.sub(' ', '  ', text)
                occurrences += text.count(word.center(len(word) + 2))
        dict[word] = occurrences
    return dict


emails = readFiles(file_path)

spam_words = getWords(emails, 1)
ham_words = getWords(emails, 0)
all_words = spam_words.union(ham_words)

spam_dict = getDicts(emails, all_words, 1)
ham_dict = getDicts(emails, all_words, 0)

words_in_spam = sum(spam_dict.values())
words_in_ham = sum(ham_dict.values())

P_SPAM = Email.spam_num / (Email.spam_num + Email.ham_num)
P_SPAM_pl = (Email.spam_num + 2) / (Email.spam_num + Email.ham_num + 4)

P_HAM = Email.ham_num / (Email.spam_num + Email.ham_num)
P_HAM_pl = (Email.ham_num + 2) / (Email.spam_num + Email.ham_num + 4)


def P_message_group(dictionary, words_in, message):

    P = 1
    for word in message.split():
        if word in dictionary.keys():
            count = dictionary[word]
            P_word_SPAM = count / (words_in + 4)

            P *= P_word_SPAM

    return P


spr = prepareMail(file_path + '/example.txt')

P_message_SPAM = P_message_group(spam_dict, words_in_spam, spr.tresc)
P_message_HAM = P_message_group(ham_dict, words_in_ham, spr.tresc)

P_SPAM_message = (P_message_SPAM * P_SPAM_pl) / (P_message_SPAM * P_SPAM_pl + P_message_HAM * P_HAM_pl)


def dict_to_xml(tag, spam_dictionary, ham_dictionary):
    tree = ET.parse(file_path + "/dict.xml")
    xmlRoot = tree.getroot()

    for key, val in spam_dictionary.items():
        child = Element('word')
        child.set('type', 'spam')
        child.set('probability', str(val / Email.spam_num))
        child.text = key
        xmlRoot.append(child)

    for key, val in ham_dictionary.items():
        child = Element('word')
        child.set('type', 'spam')
        child.set('probability', str(val / Email.spam_num))
        child.text = key
        xmlRoot.append(child)

    tree.write("./dict.xml")

    return xmlRoot


e = dict_to_xml('dictionary', spam_dict, ham_dict)

